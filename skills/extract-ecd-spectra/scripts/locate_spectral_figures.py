from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from pypdf import PdfReader


TERMS = {
    "ecd": re.compile(r"\b(?:ECD|electronic circular dichroism)\b", re.I),
    "cd_spectrum": re.compile(r"\b(?:CD|ECD)\s+spectr(?:um|a)\b", re.I),
    "delta_epsilon": re.compile(r"(?:delta\s*epsilon|Δ\s*ε|molar ellipticity)", re.I),
    "figure": re.compile(r"\b(?:fig(?:ure)?\.?)\s*\d+", re.I),
    "wavelength": re.compile(r"\b(?:wavelength|nm)\b", re.I),
}


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Locate pages likely to contain experimental ECD/CD spectra."
    )
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--minimum-score", type=int, default=3)
    args = parser.parse_args()

    reader = PdfReader(args.pdf)
    candidates = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = clean(page.extract_text() or "")
        hits = {name: len(pattern.findall(text)) for name, pattern in TERMS.items()}
        score = (
            min(hits["ecd"], 3) * 2
            + min(hits["cd_spectrum"], 3) * 3
            + min(hits["delta_epsilon"], 2) * 2
            + min(hits["figure"], 3)
            + min(hits["wavelength"], 2)
        )
        if score >= args.minimum_score:
            snippets = []
            for match in TERMS["cd_spectrum"].finditer(text):
                snippets.append(text[max(0, match.start() - 220) : match.end() + 350])
            if not snippets:
                for match in TERMS["ecd"].finditer(text):
                    snippets.append(text[max(0, match.start() - 180) : match.end() + 260])
            candidates.append(
                {
                    "page": page_number,
                    "score": score,
                    "hits": hits,
                    "snippets": snippets[:4],
                }
            )

    payload = {
        "source_pdf": str(args.pdf.resolve()),
        "page_count": len(reader.pages),
        "candidates": sorted(candidates, key=lambda item: (-item["score"], item["page"])),
        "requires_human_review": True,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Found {len(candidates)} candidate pages; wrote {args.output}")


if __name__ == "__main__":
    main()

