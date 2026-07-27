from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Render one PDF page to PNG with Poppler.")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--page", type=int, required=True, help="One-based page number")
    parser.add_argument("--dpi", type=int, default=900)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.page < 1:
        raise SystemExit("--page must be one-based and positive")
    executable = shutil.which("pdftoppm")
    if not executable:
        raise SystemExit("pdftoppm was not found on PATH")
    if os.name == "nt" and executable.lower().endswith((".cmd", ".bat")):
        wrapper = Path(executable).resolve()
        bundled_exe = wrapper.parents[2] / "native" / "poppler" / "Library" / "bin" / "pdftoppm.exe"
        if bundled_exe.exists():
            executable = str(bundled_exe)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ecd-render-") as temp:
        prefix = Path(temp) / "page"
        command = [
            executable,
            "-f",
            str(args.page),
            "-l",
            str(args.page),
            "-r",
            str(args.dpi),
            "-png",
            "-singlefile",
            str(args.pdf),
            str(prefix),
        ]
        if os.name == "nt" and str(executable).lower().endswith((".cmd", ".bat")):
            command = ["cmd.exe", "/d", "/c", *command]
        completed = subprocess.run(command, capture_output=True, text=True)
        if completed.returncode:
            raise SystemExit(completed.stderr.strip() or "pdftoppm failed")
        rendered = prefix.with_suffix(".png")
        shutil.copy2(rendered, args.output)
    print(f"Rendered page {args.page} at {args.dpi} dpi to {args.output}")


if __name__ == "__main__":
    main()
