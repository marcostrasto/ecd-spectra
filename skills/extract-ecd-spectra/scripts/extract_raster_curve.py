from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def contiguous_centers(values: np.ndarray) -> list[float]:
    if len(values) == 0:
        return []
    breaks = np.where(np.diff(values) > 1)[0] + 1
    return [float(np.median(group)) for group in np.split(values, breaks)]


def choose_trace(mask: np.ndarray, max_jump: float) -> list[tuple[int, float]]:
    trace: list[tuple[int, float]] = []
    previous: float | None = None
    for x in range(mask.shape[1]):
        centers = contiguous_centers(np.flatnonzero(mask[:, x]))
        if not centers:
            continue
        if previous is None:
            chosen = centers[len(centers) // 2]
        else:
            chosen = min(centers, key=lambda value: abs(value - previous))
            if abs(chosen - previous) > max_jump:
                continue
        trace.append((x, chosen))
        previous = chosen
    return trace


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract an isolated raster spectral trace using explicit calibration."
    )
    parser.add_argument("image", type=Path)
    parser.add_argument("config", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    cal = config["calibration"]
    trace_config = config["trace"]
    left, right = int(cal["plot_left_px"]), int(cal["plot_right_px"])
    top, bottom = int(cal["plot_top_px"]), int(cal["plot_bottom_px"])
    image = Image.open(args.image).convert("RGB")
    if not (0 <= left < right < image.width and 0 <= top < bottom < image.height):
        raise SystemExit("Plot pixel bounds fall outside the image")

    crop = np.asarray(image)[top : bottom + 1, left : right + 1].astype(float)
    mode = trace_config.get("mode", "color")
    tolerance = float(trace_config.get("tolerance", 70))
    if mode == "color":
        target = np.asarray(trace_config["target_rgb"], dtype=float)
        mask = np.linalg.norm(crop - target, axis=2) <= tolerance
    elif mode == "dark":
        luminance = crop @ np.asarray([0.2126, 0.7152, 0.0722])
        mask = luminance <= tolerance
    else:
        raise SystemExit("trace.mode must be 'color' or 'dark'")

    max_jump = float(trace_config.get("max_jump_px", max(8, crop.shape[0] * 0.08)))
    trace = choose_trace(mask, max_jump)
    if len(trace) < 10:
        raise SystemExit("Too few trace columns detected; revise crop, color, or tolerance")

    x_min, x_max = float(cal["x_min"]), float(cal["x_max"])
    y_min, y_max = float(cal["y_min"]), float(cal["y_max"])
    rows = []
    for local_x, local_y in trace:
        x_fraction = local_x / max(1, crop.shape[1] - 1)
        y_fraction = local_y / max(1, crop.shape[0] - 1)
        x_value = x_min + x_fraction * (x_max - x_min)
        y_value = y_max - y_fraction * (y_max - y_min)
        rows.append((x_value, y_value, local_x, local_y))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_csv = args.output_dir / "spectrum_raw.csv"
    with raw_csv.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["x", "y"])
        writer.writerows((f"{x:.10g}", f"{y:.10g}") for x, y, _, _ in rows)

    shutil.copy2(args.image, args.output_dir / "source_page.png")
    source_crop = image.crop((left, top, right + 1, bottom + 1))
    source_crop.save(args.output_dir / "source_figure.png")

    mask_image = Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L")
    mask_image.save(args.output_dir / "trace_mask.png")

    white = Image.new("RGB", source_crop.size, (255, 255, 255))
    overlay = Image.blend(source_crop, white, 0.68)
    draw = ImageDraw.Draw(overlay)
    radius = max(2, round(source_crop.width / 500))
    max_gap = int(trace_config.get("max_gap_columns", 6))
    segment: list[tuple[int, float]] = []
    segments: list[list[tuple[int, float]]] = []
    for _, _, px, py in rows:
        if segment and px - segment[-1][0] > max_gap:
            segments.append(segment)
            segment = []
        segment.append((px, py))
    if segment:
        segments.append(segment)
    for points in segments:
        if len(points) > 1:
            draw.line(points, fill=(255, 0, 255), width=radius * 2)
    for _, _, px, py in rows[:: max(1, len(rows) // 120)]:
        draw.ellipse((px - radius, py - radius, px + radius, py + radius), fill=(0, 0, 0))
    overlay.save(args.output_dir / "extraction_overlay.png")

    plot_width, plot_height = 1200, 700
    margin_left, margin_right, margin_top, margin_bottom = 105, 35, 45, 85
    plot = Image.new("RGB", (plot_width, plot_height), (255, 255, 255))
    plot_draw = ImageDraw.Draw(plot)
    x0, x1 = margin_left, plot_width - margin_right
    y0, y1 = margin_top, plot_height - margin_bottom
    plot_draw.rectangle((x0, y0, x1, y1), outline=(70, 70, 70), width=2)
    if y_min <= 0 <= y_max:
        zero_y = y1 - (0 - y_min) / (y_max - y_min) * (y1 - y0)
        plot_draw.line((x0, zero_y, x1, zero_y), fill=(170, 170, 170), width=2)
    for index in range(6):
        fraction = index / 5
        tick_x = x0 + fraction * (x1 - x0)
        tick_value = x_min + fraction * (x_max - x_min)
        plot_draw.line((tick_x, y1, tick_x, y1 + 8), fill=(70, 70, 70), width=2)
        plot_draw.text((tick_x - 18, y1 + 14), f"{tick_value:g}", fill=(20, 20, 20))
    for index in range(5):
        fraction = index / 4
        tick_y = y1 - fraction * (y1 - y0)
        tick_value = y_min + fraction * (y_max - y_min)
        plot_draw.line((x0 - 8, tick_y, x0, tick_y), fill=(70, 70, 70), width=2)
        plot_draw.text((12, tick_y - 7), f"{tick_value:+g}", fill=(20, 20, 20))
    plot_draw.text(((x0 + x1) / 2 - 55, plot_height - 34), f"x / {cal['x_unit']}", fill=(20, 20, 20))
    plot_draw.text((x0, 15), str(config.get("spectrum_id", "ECD spectrum")), fill=(20, 20, 20))
    plot_draw.text((x0 + 250, 15), f"y / {cal['y_unit']}", fill=(20, 20, 20))
    curve_color = tuple(int(value) for value in trace_config.get("target_rgb", [0, 0, 0]))
    plot_points = [
        (
            x0 + (x_value - x_min) / (x_max - x_min) * (x1 - x0),
            y1 - (y_value - y_min) / (y_max - y_min) * (y1 - y0),
        )
        for x_value, y_value, _, _ in rows
    ]
    plot_segments: list[list[tuple[float, float]]] = []
    plot_segment: list[tuple[float, float]] = []
    previous_source_x: int | None = None
    for point, row in zip(plot_points, rows):
        source_x = row[2]
        if previous_source_x is not None and source_x - previous_source_x > max_gap:
            plot_segments.append(plot_segment)
            plot_segment = []
        plot_segment.append(point)
        previous_source_x = source_x
    if plot_segment:
        plot_segments.append(plot_segment)
    for points in plot_segments:
        if len(points) > 1:
            plot_draw.line(points, fill=curve_color, width=5)
    plot.save(args.output_dir / "isolated_spectrum.png")

    detected_columns = len({row[2] for row in rows})
    report = {
        "status": "needs_human_review",
        "trace_mode": mode,
        "points": len(rows),
        "plot_width_columns": crop.shape[1],
        "detected_column_fraction": detected_columns / crop.shape[1],
        "x_range": [min(row[0] for row in rows), max(row[0] for row in rows)],
        "y_range": [min(row[1] for row in rows), max(row[1] for row in rows)],
        "warnings": [],
    }
    if report["detected_column_fraction"] < 0.65:
        report["warnings"].append("Trace covers less than 65% of calibrated plot width")
    if not all(math.isfinite(v) for row in rows for v in row[:2]):
        report["warnings"].append("Non-finite extracted coordinates")
    (args.output_dir / "quality_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )

    metadata = {
        **{key: value for key, value in config.items() if key not in {"calibration", "trace"}},
        "axes": {
            "x_quantity": "wavelength" if cal["x_unit"] == "nm" else "energy",
            "x_unit": cal["x_unit"],
            "y_quantity": "published_intensity",
            "y_unit": cal["y_unit"],
        },
        "extraction": {
            "source_type": "raster",
            "tool": "extract_raster_curve.py",
            "calibration": cal,
            "trace": trace_config,
        },
        "human_validation": {"status": "pending", "validator": None, "date": None, "notes": None},
    }
    (args.output_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Extracted {len(rows)} points to {args.output_dir}")


if __name__ == "__main__":
    main()
