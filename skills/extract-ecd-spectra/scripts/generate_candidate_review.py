from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


REQUIRED = (
    "candidate_id",
    "experimental",
    "compound",
    "structure_reference",
    "solvent",
    "source_location",
    "curve_identity",
    "axes_units",
)


def assess(item: dict) -> tuple[str, list[str]]:
    missing = [key for key in REQUIRED if item.get(key) in (None, "", [], {})]
    if item.get("experimental") is not True:
        missing.append("experimental_confirmation")
    ambiguities = item.get("ambiguities", [])
    reasons = [f"missing: {key}" for key in dict.fromkeys(missing)]
    if isinstance(ambiguities, list):
        reasons.extend(str(value) for value in ambiguities if value)
    return ("eligible" if not reasons else "blocked", reasons)


def deduplicate(candidates: list[dict]) -> list[dict]:
    """Collapse repeated renderings of one spectrum while preserving provenance."""
    merged: list[dict] = []
    by_key: dict[str, dict] = {}
    for item in candidates:
        spectrum_key = str(item.get("spectrum_key", "")).strip()
        if not spectrum_key or item.get("experimental") is not True:
            merged.append(dict(item))
            continue
        occurrence = {
            "candidate_id": item.get("candidate_id"),
            "source_location": item.get("source_location"),
            "curve_identity": item.get("curve_identity"),
        }
        if spectrum_key not in by_key:
            canonical = dict(item)
            canonical["occurrences"] = [occurrence]
            by_key[spectrum_key] = canonical
            merged.append(canonical)
        else:
            canonical = by_key[spectrum_key]
            canonical["occurrences"].append(occurrence)
            canonical.setdefault("merged_candidate_ids", []).append(
                item.get("candidate_id")
            )
    return merged


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate curve-level ECD candidates and generate user review artifacts."
    )
    parser.add_argument("catalog", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.catalog.read_text(encoding="utf-8"))
    candidates = payload.get("candidates", [])
    if not isinstance(candidates, list):
        raise SystemExit("candidate-curves.json must contain a candidates array")

    seen: set[str] = set()
    rows = []
    for item in deduplicate(candidates):
        if not isinstance(item, dict):
            raise SystemExit("every candidate must be an object")
        status, reasons = assess(item)
        candidate_id = str(item.get("candidate_id", ""))
        if candidate_id and candidate_id in seen:
            raise SystemExit(f"duplicate candidate_id: {candidate_id}")
        seen.add(candidate_id)
        enriched = dict(item)
        enriched["eligibility"] = status
        enriched["blocking_reasons"] = reasons
        rows.append(enriched)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    reviewed = {
        "sources": payload.get("sources", []),
        "candidates": rows,
        "eligible_count": sum(row["eligibility"] == "eligible" for row in rows),
        "requires_user_selection": True,
    }
    (args.output_dir / "candidate-curves-reviewed.json").write_text(
        json.dumps(reviewed, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    columns = (
        ("ID", "candidate_id"),
        ("Compound / stereoisomer", "compound"),
        ("Curve", "curve_identity"),
        ("Solvent", "solvent"),
        ("Source", "source_location"),
        ("Appearances", "occurrence_count"),
        ("Status", "eligibility"),
    )
    for row in rows:
        row["occurrence_count"] = len(row.get("occurrences", [])) or 1
    body = "".join(
        "<tr>"
        + "".join(
            f"<td>{html.escape(str(row.get(key, '')))}</td>" for _, key in columns
        )
        + f"<td>{html.escape('; '.join(row['blocking_reasons']) or 'Ready for selection')}</td>"
        + "</tr>"
        for row in rows
    )
    document = f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ECD candidate review</title><style>
body{{font:15px/1.45 system-ui;margin:32px;color:#17232c}}table{{border-collapse:collapse;width:100%}}
th,td{{padding:10px;border-bottom:1px solid #d8dde0;text-align:left;vertical-align:top}}
th{{background:#edf3f4}}.gate{{padding:14px;border-left:5px solid #b26a00;background:#fff7e6}}
</style></head><body><h1>Experimental ECD candidate review</h1>
<p>{reviewed['eligible_count']} of {len(rows)} curves are eligible.</p>
<div class="gate"><b>Confirmation required.</b> Select candidate IDs before extraction.</div>
<table><thead><tr>{''.join(f'<th>{html.escape(label)}</th>' for label, _ in columns)}
<th>Evidence / blocker</th></tr></thead><tbody>{body}</tbody></table></body></html>"""
    (args.output_dir / "candidate-review.html").write_text(document, encoding="utf-8")
    print(
        f"{reviewed['eligible_count']} eligible of {len(rows)} candidates; "
        f"wrote {args.output_dir / 'candidate-review.html'}"
    )


if __name__ == "__main__":
    main()
