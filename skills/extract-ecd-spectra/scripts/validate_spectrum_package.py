from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


REQUIRED_FILES = [
    "spectrum_raw.csv",
    "spectrum_canonical.csv",
    "metadata.json",
    "source_page.png",
    "source_figure.png",
    "trace_mask.png",
    "extraction_overlay.png",
    "isolated_spectrum.png",
]


def nested(data: dict, path: str):
    value = data
    for key in path.split("."):
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate an ECD spectrum package.")
    parser.add_argument("package", type=Path)
    args = parser.parse_args()

    errors, warnings = [], []
    for name in REQUIRED_FILES:
        if not (args.package / name).exists():
            errors.append(f"Missing required file: {name}")

    metadata = {}
    metadata_path = args.package / "metadata.json"
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        for field in [
            "spectrum_id",
            "source.reference_id",
            "compound.name",
            "compound.stereoisomer",
            "axes.x_unit",
            "axes.y_unit",
            "extraction.source_type",
            "human_validation.status",
        ]:
            value = nested(metadata, field)
            if value in (None, ""):
                warnings.append(f"Missing or empty metadata: {field}")
    canonical = args.package / "spectrum_canonical.csv"
    point_count = 0
    if canonical.exists():
        with canonical.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        point_count = len(rows)
        if point_count < 20:
            errors.append("Canonical spectrum has fewer than 20 points")
        wavelengths = []
        for row in rows:
            try:
                values = [
                    float(row["wavelength_nm"]),
                    float(row["energy_eV"]),
                    float(row["wavenumber_cm-1"]),
                    float(row["intensity"]),
                ]
            except (KeyError, TypeError, ValueError):
                errors.append("Canonical CSV has invalid or missing numeric columns")
                break
            if not all(math.isfinite(value) for value in values):
                errors.append("Canonical CSV contains non-finite values")
                break
            wavelengths.append(values[0])
        if wavelengths:
            if any(b <= a for a, b in zip(wavelengths, wavelengths[1:])):
                errors.append("Canonical wavelength axis is not strictly increasing")
            if min(wavelengths) < 80 or max(wavelengths) > 5000:
                warnings.append("Wavelength domain falls outside 80-5000 nm")
            if len(set(wavelengths)) != len(wavelengths):
                errors.append("Duplicate canonical wavelengths")

    validation = nested(metadata, "human_validation.status")
    if validation != "approved":
        warnings.append("Human validation has not been approved")
    status = "pass" if not errors and not warnings else ("warning" if not errors else "fail")
    report = {
        "status": status,
        "point_count": point_count,
        "errors": errors,
        "warnings": warnings,
        "human_validation_required": validation != "approved",
    }
    report_path = args.package / "quality_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
