from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import venv
from pathlib import Path


REQUIRED = {
    "numpy": "numpy",
    "Pillow": "PIL",
    "pypdf": "pypdf",
    "PyMuPDF": "fitz",
}


def runtime_python(runtime: Path) -> Path:
    return runtime / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def inspect_environment(executable: Path) -> dict:
    probe = (
        "import importlib.util,json,sys;"
        f"mods={json.dumps(REQUIRED)};"
        "missing=[p for p,m in mods.items() if importlib.util.find_spec(m) is None];"
        "print(json.dumps({'python':'.'.join(map(str,sys.version_info[:3])),"
        "'python_supported':sys.version_info[:2]>=(3,10),'missing_packages':missing}))"
    )
    completed = subprocess.run(
        [str(executable), "-c", probe],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode:
        return {
            "status": "needs_setup",
            "python": "unavailable",
            "python_supported": False,
            "missing_packages": list(REQUIRED),
        }
    result = json.loads(completed.stdout)
    supported_python = result["python_supported"]
    missing = result["missing_packages"]
    result.update(
        {
            "status": "ready" if supported_python and not missing else "needs_setup",
            "python_executable": str(executable.resolve()),
        }
    )
    return result


def create_runtime(runtime: Path) -> Path:
    runtime.parent.mkdir(parents=True, exist_ok=True)
    venv.EnvBuilder(with_pip=True, clear=False).create(runtime)
    return runtime_python(runtime)


def current_python() -> Path:
    return Path(sys.executable)


def prepare_runtime(runtime: Path) -> dict:
    executable = runtime_python(runtime)
    if not executable.exists():
        raise SystemExit(
            "Private runtime has not been created. Run preflight without --install first."
        )
    requirements = Path(__file__).resolve().parents[3] / "requirements.txt"
    completed = subprocess.run(
        [str(executable), "-m", "pip", "install", "-r", str(requirements)],
        check=False,
    )
    result = inspect_environment(executable)
    result["installation_attempted"] = True
    result["installation_exit_code"] = completed.returncode
    return result


def choose_environment(runtime: Path | None) -> Path:
    if runtime:
        executable = runtime_python(runtime)
        if not executable.exists():
            executable = create_runtime(runtime)
        return executable
    return current_python()


def write_result(result: dict, output: Path | None) -> None:
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check and, with explicit permission, prepare ECD Spectra."
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="Create a private runtime and install the required packages.",
    )
    parser.add_argument("--runtime", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.install:
        if args.runtime is None:
            raise SystemExit("--runtime is required with --install")
        result = prepare_runtime(args.runtime)
    else:
        result = inspect_environment(choose_environment(args.runtime))

    write_result(result, args.output)
    print(json.dumps(result, ensure_ascii=False))
    if not result["python_supported"]:
        raise SystemExit("ECD Spectra requires Python 3.10 or newer.")
    if result["missing_packages"]:
        raise SystemExit(
            "Setup required. Ask the user for permission, then rerun with --install."
        )


if __name__ == "__main__":
    main()
