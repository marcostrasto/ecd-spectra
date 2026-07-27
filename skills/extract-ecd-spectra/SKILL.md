---
name: extract-ecd-spectra
description: Extract, separate, digitize, standardize, and validate experimental electronic circular dichroism (ECD/CD) spectra, measurement conditions, and stereochemical evidence from scholarly PDFs or plot images. Use for locating ECD figures, recovering individual traces from multi-curve plots, capturing solvents and acquisition conditions, finding crystal structures and direct or indirect stereochemical assignments, calibrating axes, preserving sign and sample identity, producing analysis-ready CSV/JSON packages, and quality-checking literature spectra before comparison with computed ECD.
---

# Extract ECD Spectra

Create an auditable spectrum package. Never silently smooth, normalize, shift,
rescale, invert, or assign an enantiomer.

## Visual progress

Show progress in the conversation throughout the workflow. Use a numbered
nine-stage status line and update it after each material step:

```text
[1/9] Sources inspected       complete
[2/9] ECD figure located      complete - Figure 3, PDF page 3
[3/9] Curves identified       needs review
```

At stages 2, 5, 6, and 7, display the relevant local image when available:
the figure crop, calibration view, isolated spectrum, and curve-level overlay.
Do not show the same full PDF page as evidence for multiple stages. Explain
what changed and what the user must inspect. Pause only at the human
checkpoints below.

## Required workflow

1. Locate candidate pages:

```powershell
python scripts/locate_spectral_figures.py article.pdf --output candidates.json
```

2. Read the candidate page, caption, experimental section, supporting
   information, and nearby tables. Search the complete article and supporting
   information for absolute-configuration assignments, crystal structures,
   deposition identifiers, synthetic correlation, chiroptical comparisons,
   optical rotation, chiral chromatography, and other stereochemical evidence.
   Confirm that each item refers to the measured sample or an explicitly
   correlated compound. Also confirm all measurement conditions and axes.
   Record the source location for every fact. Stop for human confirmation if
   sample identity, stereochemical assignment, sign, curve identity, solvent,
   mixture ratio, or units are ambiguous.

3. Render the selected page:

```powershell
python scripts/inspect_pdf_graphics.py article.pdf --pages 7 --output graphics.json
python scripts/render_pdf_page.py article.pdf --page 7 --dpi 900 --output page.png
```

4. Prefer numerical source data. If unavailable, inspect whether the curve can
   be isolated by color or darkness. Record pixel calibration and metadata in a
   JSON configuration based on `assets/extraction-config.template.json`.
   In plots with multiple colors, use `color` for a known RGB trace or
   `neutral_dark`/`dark` for a black or gray trace. Dark modes reject chromatic
   pixels by default using `max_chroma`; never set `allow_chromatic_dark` to
   true for a multi-color plot. A luminance threshold alone can include
   saturated red or blue ink and cause the tracker to switch curves at a
   crossing. Use `edge_guard_columns` when the calibrated crop includes a
   vertical plot border and retain the resolution-scaled
   `edge_guard_fraction`; the larger guard is applied and remains visibly
   documented in the mask and extraction metadata. Keep
   `max_mask_fraction_per_column` enabled so columns dominated by vertical
   axes, borders, or annotations are rejected as non-curve geometry.

5. Extract and overlay:

```powershell
python scripts/extract_raster_curve.py page.png config.json --output-dir ECD-SPEC-0001
```

Use the automatic result only when the overlay follows the printed trace.
Inspect the cropped `source_figure.png`, binary `trace_mask.png`, and enlarged
`extraction_overlay.png`. Inspect `isolated_spectrum.png` to verify the actual
curve exported to CSV; never validate from a full PDF page thumbnail.
Inspect every crossing in a multi-curve plot. If the selected trace changes
color, follows a mirror-image band, or resumes on another curve after a gap,
reject the automatic extraction and revise the mask. Curves with the same
color, unresolved overprinting, or ambiguous identity require supervised
digitization.
For inseparable curves, use WebPlotDigitizer or Engauge and place its untouched
CSV in `spectrum_raw.csv`; still generate and review an overlay.

6. Normalize axes without altering intensity:

```powershell
python scripts/normalize_spectrum.py ECD-SPEC-0001/spectrum_raw.csv \
  --x-unit nm --y-unit M-1_cm-1 \
  --output ECD-SPEC-0001/spectrum_canonical.csv
```

7. Complete `metadata.json`. Preserve the reported solvent string, create a
   structured solvent record, and record each stereochemical evidence item and
   crystal-structure search result following `references/metadata-schema.md`.
   Never infer an unreported condition or configuration. Then validate:

```powershell
python scripts/validate_spectrum_package.py ECD-SPEC-0001
```

8. Require human approval of `extraction_overlay.png` and the report before
   setting `human_validation.status` to `approved`.

9. Generate the self-contained visual report:

```powershell
python scripts/generate_visual_report.py ECD-SPEC-0001
```

Open or link `extraction-report.html` for visual review and also deliver
`extraction-report.md`, `visual-progress.json`, the CSV files, and
`metadata.json`. Regenerate the reports after any metadata, validation, or
extraction change. The HTML report is read-only and requires no server or
network connection.

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
- Treat anomalous-dispersion X-ray assignment or an explicitly justified
  crystallographic absolute structure as direct evidence. Record deposition
  identifiers, structure relationship, refinement statistic, and source.
- Treat chemical correlation, stereospecific synthesis from a known precursor,
  comparison with independently assigned material, and validated chiroptical
  comparison as indirect evidence. Preserve the complete inference chain.
- Do not treat optical-rotation sign, ECD sign, chiral HPLC retention order, or
  enantiomeric excess alone as an absolute-configuration assignment.
- Record `not_found` for a crystal structure only after searching the article,
  supporting information, and named deposition resources; record the search
  scope and date.
- Keep spectra in mdeg when concentration and path length are unavailable. Do
  not label them as delta epsilon.

## Human checkpoints

Require human confirmation at:

1. chemical identity, stereoisomer, stereochemical evidence, crystal-structure
   relationship, curve, units, and experimental conditions;
2. calibration points when OCR or ticks are ambiguous;
3. final overlay and sign.

All other checks may run automatically. Escalate any validator warning.

## Final handoff

Summarize the final status of all nine stages. Link the HTML and Markdown
reports and each canonical CSV. State explicitly which spectra are approved,
pending review, rejected, or unsuitable for simulation comparison.

## References

- Read `references/ecd-units-and-conventions.md` before converting axes or
  intensities.
- Read `references/metadata-schema.md` when creating or repairing a package.
- Read `references/quality-criteria.md` when accepting, rejecting, or assigning
  a quality grade.
