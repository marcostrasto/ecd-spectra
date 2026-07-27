from __future__ import annotations

import argparse
import base64
import csv
import html
import json
from datetime import datetime, timezone
from pathlib import Path


IMAGE_FILES = [
    ("Source page", "source_page.png"),
    ("Source figure", "source_figure.png"),
    ("Trace mask", "trace_mask.png"),
    ("Extraction overlay", "extraction_overlay.png"),
    ("Isolated spectrum", "isolated_spectrum.png"),
]


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def nested(data: dict, *keys: str):
    value = data
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def display(value) -> str:
    if value in (None, "", []):
        return "Not reported"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def solvent_text(metadata: dict) -> str:
    solvent = nested(metadata, "experiment", "solvent")
    if isinstance(solvent, str):
        return solvent
    if isinstance(solvent, dict):
        return display(solvent.get("reported_as"))
    return "Not reported"


def data_uri(path: Path) -> str:
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def csv_points(path: Path) -> list[list[float]]:
    if not path.exists():
        return []
    points: list[list[float]] = []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            try:
                x = float(row.get("wavelength_nm", row.get("x", "")))
                y = float(row.get("intensity", row.get("y", "")))
            except (TypeError, ValueError):
                continue
            points.append([x, y])
    return points


def stage(status: str, label: str, detail: str) -> dict:
    return {"status": status, "label": label, "detail": detail}


def build_progress(package: Path, metadata: dict, quality: dict) -> list[dict]:
    source = metadata.get("source") if isinstance(metadata.get("source"), dict) else {}
    experiment = (
        metadata.get("experiment")
        if isinstance(metadata.get("experiment"), dict)
        else {}
    )
    calibration = nested(metadata, "extraction", "calibration")
    human_status = nested(metadata, "human_validation", "status")
    quality_status = quality.get("status")
    return [
        stage(
            "complete" if source else "pending",
            "Sources inspected",
            display(source.get("reference_id")),
        ),
        stage(
            "complete" if (package / "source_figure.png").exists() else "pending",
            "ECD figure located",
            "Figure crop available"
            if (package / "source_figure.png").exists()
            else "Awaiting figure crop",
        ),
        stage(
            "complete" if metadata.get("compound") else "needs_review",
            "Curves and sample identified",
            display(nested(metadata, "compound", "stereoisomer")),
        ),
        stage(
            "complete" if experiment else "pending",
            "Conditions recovered",
            f"Solvent: {solvent_text(metadata)}",
        ),
        stage(
            "complete" if isinstance(calibration, dict) else "pending",
            "Axes calibrated",
            "Calibration recorded"
            if isinstance(calibration, dict)
            else "Calibration unavailable",
        ),
        stage(
            "complete"
            if (package / "spectrum_canonical.csv").exists()
            else "pending",
            "Curve extracted",
            "Canonical CSV available"
            if (package / "spectrum_canonical.csv").exists()
            else "Canonical CSV unavailable",
        ),
        stage(
            "complete"
            if human_status == "approved"
            else (
                "needs_review"
                if (package / "extraction_overlay.png").exists()
                else "pending"
            ),
            "Overlay reviewed",
            f"Human validation: {display(human_status)}",
        ),
        stage(
            "complete"
            if quality_status == "pass"
            else ("needs_review" if quality else "pending"),
            "Package validated",
            f"Quality status: {display(quality_status)}",
        ),
        stage("complete", "Report generated", "HTML and Markdown written"),
    ]


def condition_rows(metadata: dict) -> list[tuple[str, str]]:
    experiment = (
        metadata.get("experiment")
        if isinstance(metadata.get("experiment"), dict)
        else {}
    )
    return [
        ("Solvent", solvent_text(metadata)),
        ("Concentration", display(experiment.get("concentration"))),
        ("Path length", display(experiment.get("path_length"))),
        ("Temperature / K", display(experiment.get("temperature_K"))),
        ("Instrument", display(experiment.get("instrument"))),
        ("Cell material", display(experiment.get("cell_material"))),
        ("Bandwidth / nm", display(experiment.get("spectral_bandwidth_nm"))),
        ("Scan rate / nm min-1", display(experiment.get("scan_rate_nm_min"))),
        ("Number of scans", display(experiment.get("number_of_scans"))),
        ("pH", display(experiment.get("pH"))),
    ]


def evidence_rows(metadata: dict) -> list[dict]:
    evidence = nested(metadata, "compound", "stereochemistry", "evidence")
    return evidence if isinstance(evidence, list) else []


def make_markdown(
    package: Path, metadata: dict, quality: dict, progress: list[dict]
) -> str:
    lines = [
        f"# ECD extraction report: {display(metadata.get('spectrum_id'))}",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Progress",
        "",
    ]
    symbols = {"complete": "[x]", "needs_review": "[!]", "pending": "[ ]"}
    for item in progress:
        lines.append(
            f"- {symbols[item['status']]} {item['label']}: {item['detail']}"
        )
    lines.extend(["", "## Experimental conditions", "", "| Field | Value |", "|---|---|"])
    for key, value in condition_rows(metadata):
        lines.append(f"| {key} | {str(value).replace('|', '\\|')} |")
    lines.extend(["", "## Visual evidence", ""])
    for label, filename in IMAGE_FILES:
        if (package / filename).exists():
            lines.extend([f"### {label}", "", f"![{label}]({filename})", ""])
    lines.extend(
        [
            "## Validation",
            "",
            f"- Quality status: {display(quality.get('status'))}",
            f"- Human validation: {display(nested(metadata, 'human_validation', 'status'))}",
        ]
    )
    warnings = quality.get("warnings")
    if isinstance(warnings, list) and warnings:
        lines.extend(["", "### Warnings", ""])
        lines.extend(f"- {display(warning)}" for warning in warnings)
    lines.extend(
        [
            "",
            "> This report does not replace human approval of sample identity, "
            "calibration, sign, or the final extraction overlay.",
            "",
        ]
    )
    return "\n".join(lines)


def make_html(
    package: Path,
    metadata: dict,
    quality: dict,
    progress: list[dict],
    points: list[list[float]],
) -> str:
    done = sum(item["status"] == "complete" for item in progress)
    percent = round(done / len(progress) * 100)
    stage_cards = "".join(
        f'<li class="{item["status"]}"><span>{index}</span><div><b>'
        f'{html.escape(item["label"])}</b><small>{html.escape(item["detail"])}</small>'
        f"</div></li>"
        for index, item in enumerate(progress, 1)
    )
    conditions = "".join(
        f"<tr><th>{html.escape(key)}</th><td>{html.escape(value)}</td></tr>"
        for key, value in condition_rows(metadata)
    )
    images = "".join(
        f'<figure><img src="{data_uri(package / filename)}" '
        f'alt="{html.escape(label)}"><figcaption>{html.escape(label)}</figcaption></figure>'
        for label, filename in IMAGE_FILES
        if (package / filename).exists()
    )
    evidence = evidence_rows(metadata)
    evidence_html = (
        "".join(
            "<article><b>"
            + html.escape(display(item.get("type")))
            + "</b><p>"
            + html.escape(display(item.get("reported_observation")))
            + "</p><small>"
            + html.escape(display(item.get("source_location")))
            + "</small></article>"
            for item in evidence
            if isinstance(item, dict)
        )
        or "<p>No structured stereochemical evidence recorded.</p>"
    )
    warnings = quality.get("warnings")
    warning_html = (
        "".join(f"<li>{html.escape(display(w))}</li>" for w in warnings)
        if isinstance(warnings, list) and warnings
        else "<li>No validator warnings recorded.</li>"
    )
    title = html.escape(display(metadata.get("spectrum_id")))
    compound = html.escape(display(nested(metadata, "compound", "name")))
    point_json = json.dumps(points, separators=(",", ":"))
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ECD extraction report - {title}</title>
<style>
:root{{--ink:#14212b;--muted:#64727d;--paper:#f5f2eb;--card:#fff;--cyan:#087e8b;
--green:#327a4d;--amber:#a56600;--line:#d9d5ca}}*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.5 system-ui,sans-serif}}
main{{max-width:1180px;margin:auto;padding:34px 22px 70px}}header{{display:flex;gap:24px;
justify-content:space-between;align-items:end;border-bottom:3px solid var(--ink);padding-bottom:20px}}
h1{{font-size:clamp(28px,4vw,52px);line-height:1;margin:6px 0}}.eyebrow{{letter-spacing:.15em;
text-transform:uppercase;color:var(--cyan);font-weight:800}}.summary{{min-width:260px}}
.bar{{height:12px;background:#ddd8cc;border-radius:9px;overflow:hidden}}.bar i{{display:block;
height:100%;width:{percent}%;background:var(--cyan)}}section{{margin-top:34px}}h2{{font-size:24px}}
.stages{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px;
padding:0;list-style:none}}.stages li{{display:flex;gap:12px;background:var(--card);padding:14px;
border-left:5px solid var(--line);box-shadow:0 2px 8px #0000000b}}.stages span{{display:grid;
place-items:center;width:30px;height:30px;border-radius:50%;background:#eee;font-weight:800}}
.stages small{{display:block;color:var(--muted)}}.stages .complete{{border-color:var(--green)}}
.stages .needs_review{{border-color:var(--amber)}}.grid{{display:grid;
grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:18px}}figure,article,.panel{{margin:0;
background:var(--card);padding:14px;border:1px solid var(--line)}}figure img{{display:block;
width:100%;max-height:620px;object-fit:contain;background:#fafafa}}figcaption{{font-weight:750;
padding-top:8px}}table{{width:100%;border-collapse:collapse;background:var(--card)}}th,td{{
padding:9px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}th{{width:34%}}
canvas{{width:100%;height:420px;background:#fff;border:1px solid var(--line)}}.note{{background:#fff8e5;
border-left:5px solid var(--amber);padding:14px}}code{{word-break:break-all}}@media print{{
body{{background:white}}main{{max-width:none}}.panel,figure,article{{break-inside:avoid}}}}
</style>
</head>
<body><main>
<header><div><div class="eyebrow">Auditable literature extraction</div><h1>{title}</h1>
<p>{compound}</p></div><div class="summary"><b>{done}/{len(progress)} stages complete</b>
<div class="bar"><i></i></div><small>Human validation:
{html.escape(display(nested(metadata, "human_validation", "status")))}</small></div></header>
<section><h2>Workflow progress</h2><ol class="stages">{stage_cards}</ol></section>
<section><h2>Extracted spectrum</h2><canvas id="plot" width="1080" height="420"></canvas></section>
<section><h2>Visual evidence</h2><div class="grid">{images or '<p>No images available.</p>'}</div></section>
<section class="grid"><div><h2>Experimental conditions</h2><table>{conditions}</table></div>
<div><h2>Validation</h2><div class="panel"><p><b>Quality status:</b>
{html.escape(display(quality.get("status")))}</p><ul>{warning_html}</ul></div></div></section>
<section><h2>Stereochemical evidence</h2><div class="grid">{evidence_html}</div></section>
<section class="note"><b>Human checkpoint.</b> This report does not approve sample identity,
axis calibration, sign, curve identity, or stereochemical assignment. Review the curve-level
overlay before setting <code>human_validation.status</code> to <code>approved</code>.</section>
</main>
<script>
const pts={point_json};const c=document.getElementById('plot'),x=c.getContext('2d');
x.clearRect(0,0,c.width,c.height);if(pts.length){{const pad={{l:72,r:24,t:24,b:52}};
const xs=pts.map(p=>p[0]),ys=pts.map(p=>p[1]);let xmin=Math.min(...xs),xmax=Math.max(...xs);
let ymin=Math.min(...ys),ymax=Math.max(...ys);if(ymin===ymax){{ymin-=1;ymax+=1}}
const X=v=>pad.l+(v-xmin)/(xmax-xmin)*(c.width-pad.l-pad.r);
const Y=v=>c.height-pad.b-(v-ymin)/(ymax-ymin)*(c.height-pad.t-pad.b);
x.strokeStyle='#98a0a5';x.lineWidth=1;x.strokeRect(pad.l,pad.t,c.width-pad.l-pad.r,c.height-pad.t-pad.b);
if(ymin<=0&&ymax>=0){{x.beginPath();x.moveTo(pad.l,Y(0));x.lineTo(c.width-pad.r,Y(0));x.stroke()}}
x.fillStyle='#14212b';x.font='14px system-ui';x.fillText(xmin.toFixed(1),pad.l,c.height-22);
x.fillText(xmax.toFixed(1),c.width-pad.r-42,c.height-22);x.fillText(ymax.toPrecision(4),8,pad.t+5);
x.fillText(ymin.toPrecision(4),8,c.height-pad.b);x.fillText('wavelength / nm',c.width/2-50,c.height-10);
x.strokeStyle='#087e8b';x.lineWidth=2.5;x.beginPath();pts.forEach((p,i)=>{{
const a=X(p[0]),b=Y(p[1]);i?x.lineTo(a,b):x.moveTo(a,b)}});x.stroke()}}
</script></body></html>"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate self-contained HTML and Markdown ECD reports."
    )
    parser.add_argument("package", type=Path)
    parser.add_argument("--html", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()
    package = args.package.resolve()
    metadata = read_json(package / "metadata.json")
    quality = read_json(package / "quality_report.json")
    progress = build_progress(package, metadata, quality)
    points = csv_points(package / "spectrum_canonical.csv")
    html_path = args.html or package / "extraction-report.html"
    md_path = args.markdown or package / "extraction-report.md"
    progress_path = package / "visual-progress.json"
    html_path.write_text(
        make_html(package, metadata, quality, progress, points), encoding="utf-8"
    )
    md_path.write_text(
        make_markdown(package, metadata, quality, progress), encoding="utf-8"
    )
    progress_path.write_text(
        json.dumps({"stages": progress}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Wrote {html_path}")
    print(f"Wrote {md_path}")
    print(f"Wrote {progress_path}")


if __name__ == "__main__":
    main()

