from __future__ import annotations

import argparse
from pathlib import Path

import fitz


def render_page(pdf: Path, page_number: int, dpi: int, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with fitz.open(pdf) as document:
        if page_number > document.page_count:
            raise ValueError(
                f"page {page_number} exceeds the {document.page_count}-page PDF"
            )
        page = document.load_page(page_number - 1)
        scale = dpi / 72
        pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
        pixmap.save(output)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render one PDF page to PNG.")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--page", type=int, required=True, help="One-based page number")
    parser.add_argument("--dpi", type=int, default=900)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.page < 1:
        raise SystemExit("--page must be one-based and positive")
    try:
        render_page(args.pdf, args.page, args.dpi, args.output)
    except ValueError as error:
        raise SystemExit(f"--{error}") from error
    print(f"Rendered page {args.page} at {args.dpi} dpi to {args.output}")


if __name__ == "__main__":
    main()
