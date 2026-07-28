from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


HC_EV_NM = 1239.8419843320026


def wavelength_nm(value: float, unit: str) -> float:
    if unit == "nm":
        return value
    if unit == "eV":
        return HC_EV_NM / value
    if unit == "cm-1":
        return 10_000_000.0 / value
    raise ValueError(f"Unsupported x unit: {unit}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create canonical ECD spectral axes.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--x-unit", choices=["nm", "eV", "cm-1"], required=True)
    parser.add_argument("--y-unit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    points = []
    with args.input.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not {"x", "y"}.issubset(reader.fieldnames):
            raise SystemExit("Input CSV must contain x,y columns")
        for row in reader:
            x, y = float(row["x"]), float(row["y"])
            if not math.isfinite(x) or not math.isfinite(y) or x <= 0:
                raise SystemExit("All x,y values must be finite and x must be positive")
            nm = wavelength_nm(x, args.x_unit)
            points.append(
                (
                    nm,
                    HC_EV_NM / nm,
                    10_000_000.0 / nm,
                    y,
                    row.get("point_status", "observed"),
                )
            )
    points.sort(key=lambda point: point[0])

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "wavelength_nm",
                "energy_eV",
                "wavenumber_cm-1",
                "intensity",
                "intensity_unit",
                "point_status",
            ]
        )
        writer.writerows(
            (
                f"{nm:.10g}",
                f"{ev:.10g}",
                f"{wn:.10g}",
                f"{y:.10g}",
                args.y_unit,
                status,
            )
            for nm, ev, wn, y, status in points
        )
    print(f"Wrote {len(points)} canonical points to {args.output}")


if __name__ == "__main__":
    main()
