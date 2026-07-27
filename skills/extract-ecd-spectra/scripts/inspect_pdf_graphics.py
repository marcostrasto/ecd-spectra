from __future__ import annotations

import argparse
import json
from pathlib import Path

from pypdf import PdfReader
from pypdf.generic import ContentStream


PATH_OPERATORS = {b"m", b"l", b"c", b"v", b"y", b"re"}
PAINT_OPERATORS = {b"S", b"s", b"f", b"F", b"f*", b"B", b"B*", b"b", b"b*"}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect whether selected PDF pages contain raster images or vector paths."
    )
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--pages", required=True, help="One-based pages, e.g. 2,3,5")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    reader = PdfReader(args.pdf)
    page_numbers = [int(value) for value in args.pages.split(",")]
    results = []
    for page_number in page_numbers:
        if not 1 <= page_number <= len(reader.pages):
            raise SystemExit(f"Page {page_number} is outside the PDF")
        page = reader.pages[page_number - 1]
        resources = page.get("/Resources", {})
        xobjects = resources.get("/XObject", {})
        images = []
        forms = 0
        if xobjects:
            for name, indirect in xobjects.get_object().items():
                obj = indirect.get_object()
                subtype = obj.get("/Subtype")
                if subtype == "/Image":
                    images.append(
                        {
                            "name": str(name),
                            "width": int(obj.get("/Width", 0)),
                            "height": int(obj.get("/Height", 0)),
                            "color_space": str(obj.get("/ColorSpace", "")),
                        }
                    )
                elif subtype == "/Form":
                    forms += 1
        operations = ContentStream(page.get_contents(), reader).operations
        vector_paths = sum(1 for _, operator in operations if operator in PATH_OPERATORS)
        paint_ops = sum(1 for _, operator in operations if operator in PAINT_OPERATORS)
        image_draws = sum(1 for _, operator in operations if operator == b"Do")
        if vector_paths >= 100 and not images:
            classification = "vector_dominant"
        elif images and vector_paths < 100:
            classification = "raster_or_embedded_figure"
        else:
            classification = "mixed_or_ambiguous"
        results.append(
            {
                "page": page_number,
                "classification": classification,
                "image_xobjects": images,
                "form_xobjects": forms,
                "vector_path_operations": vector_paths,
                "paint_operations": paint_ops,
                "xobject_draw_operations": image_draws,
                "note": "Classification is structural evidence, not proof that the spectral curve itself uses that representation.",
            }
        )

    payload = {"source_pdf": str(args.pdf.resolve()), "pages": results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote graphics inspection for {len(results)} page(s) to {args.output}")


if __name__ == "__main__":
    main()

