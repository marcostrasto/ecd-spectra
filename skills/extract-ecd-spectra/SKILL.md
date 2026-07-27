---
name: extract-ecd-spectra
description: Extract, digitize, standardize, and validate experimental electronic circular dichroism (ECD/CD) spectra and their measurement conditions from scholarly PDFs or plot images. Use for locating ECD figures, recovering vector or raster curves, capturing solvent and other experimental conditions, calibrating axes, preserving sign and enantiomer identity, producing analysis-ready CSV/JSON packages, and quality-checking literature spectra before comparison with computed ECD.
---

# Extract ECD Spectra

Create an auditable spectrum package. Never silently smooth, normalize, shift,
rescale, invert, or assign an enantiomer.

## Required workflow

1. Locate candidate pages:

```powershell
python scripts/locate_spectral_figures.py article.pdf --output candidates.json
```

2. Read the candidate page, caption, experimental section, supporting
   information, and nearby tables. Confirm compound, stereoisomer, solvent,
   mixture composition, concentration, path length, temperature, x
   quantity/unit, y quantity/unit, figure and panel. Record the source location
   for every condition. Stop for human confirmation if sign, curve identity,
   solvent identity, mixture ratio, or units are ambiguous.

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

7. Complete `metadata.json`. Preserve the reported solvent string and also
   create a structured solvent record following
   `references/metadata-schema.md`. Never infer an unreported solvent,
   composition, concentration, or temperature. Then validate:

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
- Mark the package unsuitable for direct simulation comparison when solvent
  identity is unresolved. Preserve spectra with an unreported solvent, but
  expose the omission as a validation warning.
- Represent solvent mixtures component by component. Record ratio values and
  their basis only when stated; do not convert volume, mass, or mole fractions
  without the required physical data.
- Keep spectra in mdeg when concentration and path length are unavailable. Do
  not label them as delta epsilon.

## Human checkpoints

Require human confirmation at:

1. chemical identity, stereoisomer, curve, units, and experimental conditions;
2. calibration points when OCR or ticks are ambiguous;
3. final overlay and sign.

All other checks may run automatically. Escalate any validator warning.

## References

- Read `references/ecd-units-and-conventions.md` before converting axes or
  intensities.
- Read `references/metadata-schema.md` when creating or repairing a package.
- Read `references/quality-criteria.md` when accepting, rejecting, or assigning
  a quality grade.
