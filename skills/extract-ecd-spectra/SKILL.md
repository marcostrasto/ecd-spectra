---
name: extract-ecd-spectra
description: Extract, digitize, standardize, and validate experimental electronic circular dichroism (ECD/CD) spectra from scholarly PDFs or plot images. Use for locating ECD figures, rendering or cropping spectral panels, recovering vector or raster curves, calibrating wavelength or energy axes, preserving sign and enantiomer identity, converting spectra to analysis-ready CSV/JSON packages, generating overlays, and quality-checking literature spectra before comparison with computed ECD.
---

# Extract ECD Spectra

Create an auditable spectrum package. Never silently smooth, normalize, shift,
rescale, invert, or assign an enantiomer.

## Required workflow

1. Locate candidate pages:

```powershell
python scripts/locate_spectral_figures.py article.pdf --output candidates.json
```

2. Read the candidate page and its caption. Confirm compound, stereoisomer,
   solvent, temperature, x quantity/unit, y quantity/unit, figure and panel.
   Stop for human confirmation if sign, curve identity, or units are ambiguous.

3. Render the selected page:

```powershell
python scripts/inspect_pdf_graphics.py article.pdf --pages 7 --output graphics.json
python scripts/render_pdf_page.py article.pdf --page 7 --dpi 900 --output page.png
```

4. Prefer numerical source data. If unavailable, inspect whether the curve can
   be isolated by color or darkness. Record pixel calibration and metadata in a
   JSON configuration based on `assets/extraction-config.template.json`.

5. Extract and overlay:

```powershell
python scripts/extract_raster_curve.py page.png config.json --output-dir ECD-SPEC-0001
```

Use the automatic result only when the overlay follows the printed trace.
Inspect the cropped `source_figure.png`, binary `trace_mask.png`, and enlarged
`extraction_overlay.png`. Inspect `isolated_spectrum.png` to verify the actual
curve exported to CSV; never validate from a full PDF page thumbnail.
For inseparable curves, use WebPlotDigitizer or Engauge and place its untouched
CSV in `spectrum_raw.csv`; still generate and review an overlay.

6. Normalize axes without altering intensity:

```powershell
python scripts/normalize_spectrum.py ECD-SPEC-0001/spectrum_raw.csv \
  --x-unit nm --y-unit M-1_cm-1 \
  --output ECD-SPEC-0001/spectrum_canonical.csv
```

7. Complete `metadata.json`, then validate:

```powershell
python scripts/validate_spectrum_package.py ECD-SPEC-0001
```

8. Require human approval of `extraction_overlay.png` and the report before
   setting `human_validation.status` to `approved`.

## Branching rules

- Prefer original supporting data over digitization.
- Prefer vector recovery over raster tracing when a clean PDF path can be
  identified. Preserve the original PDF and path-selection evidence.
- Use raster extraction for isolated solid traces with adequate resolution.
- Use supervised WebPlotDigitizer/Engauge for overlapping, dashed, grayscale,
  annotated, or low-resolution curves.
- Reject a quantitative extraction when axes, zero line, units, enantiomer, or
  trace identity cannot be established.
- Keep spectra in mdeg when concentration and path length are unavailable. Do
  not label them as delta epsilon.

## Human checkpoints

Require human confirmation at:

1. chemical identity, stereoisomer, curve and units;
2. calibration points when OCR or ticks are ambiguous;
3. final overlay and sign.

All other checks may run automatically. Escalate any validator warning.

## References

- Read `references/ecd-units-and-conventions.md` before converting axes or
  intensities.
- Read `references/metadata-schema.md` when creating or repairing a package.
- Read `references/quality-criteria.md` when accepting, rejecting, or assigning
  a quality grade.
