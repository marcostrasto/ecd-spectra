from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path


STAGES = [
    ("sources", "Sources inspected"),
    ("candidates", "Candidate curves verified"),
    ("selection", "User selection"),
    ("conditions", "Conditions recovered"),
    ("calibration", "Axes calibrated"),
    ("separation", "Curve separated"),
    ("reconstruction", "Discontinuities assessed"),
    ("normalization", "Spectrum normalized"),
    ("validation", "Extraction validated"),
    ("report", "Final report"),
]
STATES = {"pending", "in_progress", "needs_review", "complete", "blocked"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Update the ECD workflow progress monitor.")
    parser.add_argument("workdir", type=Path)
    parser.add_argument("--stage", choices=[key for key, _ in STAGES])
    parser.add_argument("--status", choices=sorted(STATES))
    parser.add_argument("--detail", default="")
    args = parser.parse_args()
    args.workdir.mkdir(parents=True, exist_ok=True)
    state_path = args.workdir / "visual-progress.json"
    state = {}
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
    existing = {item.get("id"): item for item in state.get("stages", [])}
    stages = [
        {
            "id": key,
            "label": label,
            "status": existing.get(key, {}).get("status", "pending"),
            "detail": existing.get(key, {}).get("detail", ""),
        }
        for key, label in STAGES
    ]
    if args.stage:
        selected = next(item for item in stages if item["id"] == args.stage)
        selected["status"] = args.status or "in_progress"
        selected["detail"] = args.detail
    state = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "stages": stages,
    }
    state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

    done = sum(item["status"] == "complete" for item in stages)
    active = next(
        (item for item in stages if item["status"] in {"blocked", "needs_review", "in_progress"}),
        next((item for item in stages if item["status"] == "pending"), stages[-1]),
    )
    cards = "".join(
        f'<li class="{item["status"]}"><b>{index}. {html.escape(item["label"])}</b>'
        f'<span>{html.escape(item["status"].replace("_", " ").upper())}</span>'
        f'<small>{html.escape(item["detail"])}</small></li>'
        for index, item in enumerate(stages, 1)
    )
    document = f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="5">
<title>ECD workflow progress</title><style>
:root{{--green:#26734d;--blue:#087e8b;--amber:#a56600;--red:#a33;--line:#d9dfe1}}
body{{font:15px/1.4 system-ui;margin:32px;color:#15242d}}.bar{{height:14px;background:#e4e8e9;border-radius:8px;overflow:hidden}}
.bar i{{display:block;width:{done * 10}%;height:100%;background:var(--blue)}}ol{{padding:0;display:grid;gap:8px}}
li{{list-style:none;padding:12px;border-left:5px solid var(--line);background:#f7f9f9;display:grid;grid-template-columns:1fr auto}}
li small{{grid-column:1/-1;color:#607078}}li.complete{{border-color:var(--green)}}li.in_progress{{border-color:var(--blue)}}
li.needs_review{{border-color:var(--amber)}}li.blocked{{border-color:var(--red)}}span{{font-size:12px;font-weight:800}}
</style></head><body><h1>ECD extraction progress</h1><h2>{done}/10 · {html.escape(active['label'])} ·
{html.escape(active['status'].replace('_', ' ').upper())}</h2><div class="bar"><i></i></div>
<ol>{cards}</ol><small>Updated {html.escape(state['updated_at'])}; refreshes every 5 seconds.</small>
</body></html>"""
    (args.workdir / "workflow-progress.html").write_text(document, encoding="utf-8")
    print(
        f"[{'#' * done}{'-' * (10 - done)}] {done}/10 | "
        f"{active['label']} | {active['status'].upper()}"
    )


if __name__ == "__main__":
    main()
