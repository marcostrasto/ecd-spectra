from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import numpy as np


SCRIPT = (
    Path(__file__).parents[1]
    / "skills"
    / "extract-ecd-spectra"
    / "scripts"
    / "extract_raster_curve.py"
)
SPEC = importlib.util.spec_from_file_location("extract_raster_curve", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class MultiCurveMaskTests(unittest.TestCase):
    def test_short_gap_reconstruction_is_explicit_and_long_gap_stays_open(self) -> None:
        trace = [(0, 10.0), (1, 11.0), (4, 14.0), (10, 20.0)]

        reconstructed, gaps = MODULE.reconstruct_short_gaps(
            trace, max_gap_columns=3
        )

        statuses = {x: status for x, _, status in reconstructed}
        self.assertEqual(statuses[2], "reconstructed_linear")
        self.assertEqual(statuses[3], "reconstructed_linear")
        self.assertNotIn(5, statuses)
        self.assertEqual(gaps[0]["status"], "reconstructed_linear")
        self.assertEqual(gaps[1]["status"], "unresolved")

    def test_gap_reconstruction_does_not_modify_observed_points(self) -> None:
        trace = [(2, 25.0), (5, 55.0)]

        reconstructed, _ = MODULE.reconstruct_short_gaps(
            trace, max_gap_columns=5
        )

        self.assertEqual(reconstructed[0], (2, 25.0, "observed"))
        self.assertEqual(reconstructed[-1], (5, 55.0, "observed"))
        self.assertEqual(reconstructed[1], (3, 35.0, "reconstructed_linear"))
        self.assertEqual(reconstructed[2], (4, 45.0, "reconstructed_linear"))

    def test_dark_mode_rejects_red_curve_and_tracks_black_across_crossing(self) -> None:
        height, width = 101, 121
        image = np.full((height, width, 3), 255.0)
        black_rows = []
        red_rows = []
        for x in range(width):
            black_y = int(round(50 + 30 * np.sin(x / 18)))
            red_y = int(round(50 - 30 * np.sin(x / 18)))
            black_rows.append(black_y)
            red_rows.append(red_y)
            image[max(0, black_y - 1) : black_y + 2, x] = (0, 0, 0)
            image[max(0, red_y - 1) : red_y + 2, x] = (255, 0, 0)

        mask, diagnostics = MODULE.build_trace_mask(
            image,
            {
                "mode": "dark",
                "tolerance": 90,
                "max_chroma": 24,
            },
        )
        trace = MODULE.choose_trace(mask, max_jump=12)
        traced = {x: y for x, y in trace}

        self.assertGreater(diagnostics["chromatic_dark_pixels_rejected"], 0)
        self.assertGreater(len(trace), width * 0.9)
        for x in (10, 35, 60, 85, 110):
            self.assertAlmostEqual(traced[x], black_rows[x], delta=2)
            if abs(black_rows[x] - red_rows[x]) > 5:
                self.assertGreater(abs(traced[x] - red_rows[x]), 5)

    def test_chromatic_dark_requires_explicit_opt_in(self) -> None:
        image = np.array([[[255.0, 0.0, 0.0], [0.0, 0.0, 0.0]]])
        safe_mask, _ = MODULE.build_trace_mask(
            image,
            {
                "mode": "dark",
                "tolerance": 90,
                "max_chroma": 24,
                "max_mask_fraction_per_column": 1,
            },
        )
        permissive_mask, _ = MODULE.build_trace_mask(
            image,
            {
                "mode": "dark",
                "tolerance": 90,
                "max_chroma": 24,
                "allow_chromatic_dark": True,
                "max_mask_fraction_per_column": 1,
            },
        )

        self.assertFalse(bool(safe_mask[0, 0]))
        self.assertTrue(bool(safe_mask[0, 1]))
        self.assertTrue(bool(permissive_mask[0, 0]))

    def test_edge_guard_excludes_vertical_plot_borders(self) -> None:
        image = np.full((20, 30, 3), 255.0)
        image[:, 0:3] = (0, 0, 0)
        image[:, -3:] = (0, 0, 0)
        image[10, 3:-3] = (0, 0, 0)

        mask, diagnostics = MODULE.build_trace_mask(
            image,
            {
                "mode": "dark",
                "tolerance": 90,
                "max_chroma": 24,
                "edge_guard_columns": 3,
            },
        )

        self.assertFalse(mask[:, :3].any())
        self.assertFalse(mask[:, -3:].any())
        self.assertTrue(mask[10, 3:-3].all())
        self.assertEqual(diagnostics["edge_guard_columns"], 3)

    def test_edge_guard_scales_with_plot_width(self) -> None:
        image = np.full((20, 1000, 3), 255.0)
        image[10, :] = (0, 0, 0)

        mask, diagnostics = MODULE.build_trace_mask(
            image,
            {
                "mode": "neutral_dark",
                "tolerance": 90,
                "max_chroma": 24,
                "edge_guard_columns": 3,
                "edge_guard_fraction": 0.008,
                "max_mask_fraction_per_column": 0.20,
            },
        )

        self.assertEqual(diagnostics["edge_guard_columns"], 8)
        self.assertFalse(mask[:, :8].any())
        self.assertFalse(mask[:, -8:].any())
        self.assertTrue(mask[10, 8:-8].all())

    def test_dense_vertical_geometry_is_not_a_curve(self) -> None:
        image = np.full((100, 40, 3), 255.0)
        image[:, 20] = (0, 0, 0)
        image[55:58, :] = (0, 0, 0)

        mask, diagnostics = MODULE.build_trace_mask(
            image,
            {
                "mode": "dark",
                "tolerance": 90,
                "max_chroma": 24,
                "max_mask_fraction_per_column": 0.2,
            },
        )

        self.assertFalse(mask[:, 20].any())
        self.assertTrue(mask[55:58, 10].all())
        self.assertEqual(diagnostics["dense_columns_rejected"], 1)

    def test_dense_column_threshold_is_configurable_for_low_resolution_curves(self) -> None:
        image = np.full((100, 20, 3), 255.0)
        image[47:53, :] = (0, 0, 0)

        strict_mask, _ = MODULE.build_trace_mask(
            image,
            {
                "mode": "neutral_dark",
                "tolerance": 90,
                "max_chroma": 24,
                "max_mask_fraction_per_column": 0.05,
            },
        )
        permissive_mask, _ = MODULE.build_trace_mask(
            image,
            {
                "mode": "neutral_dark",
                "tolerance": 90,
                "max_chroma": 24,
                "max_mask_fraction_per_column": 0.20,
            },
        )

        self.assertFalse(strict_mask.any())
        self.assertTrue(permissive_mask[47:53, :].all())


if __name__ == "__main__":
    unittest.main()
