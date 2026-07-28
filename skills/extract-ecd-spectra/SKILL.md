---
name: extract-ecd-spectra
description: Discover, present for confirmation, extract, separate, digitize, standardize, and validate experimental electronic circular dichroism (ECD/CD) spectra, measurement conditions, and stereochemical evidence from scholarly PDFs or plot images. Use for finding eligible ECD curves in articles and supporting information, linking each curve unambiguously to a structure and solvent before extraction, recovering individual traces from multi-curve plots, tracking visual progress, and producing auditable CSV/JSON packages.
---

# Extract ECD Spectra

Create an auditable spectrum package. Never silently smooth, normalize, shift,
rescale, invert, or assign an enantiomer.

## Beginner-first start

Assume the user has never used Codex or a spectroscopy plugin. Start with one
plain sentence: "I will first check the PDFs and show you the experimental ECD
curves I can identify; nothing will be extracted until you choose one."

Before reading PDFs, run:

```powershell
python scripts/preflight_environment.py --runtime WORKDIR/.ecd-runtime --output WORKDIR/ecd-setup-status.json
```

If the result is `ready`, continue without discussing dependencies. If it is
`needs_setup` only because packages are missing, explain in one sentence that
the plugin needs to prepare its local PDF tools, ask permission once, and then
run:

```powershell
python scripts/preflight_environment.py --install --runtime WORKDIR/.ecd-runtime --output WORKDIR/ecd-setup-status.json
```

Never ask the user to install individual Python packages or Poppler. Do not
show commands, file paths, JSON, masks, thresholds, or implementation jargon
unless setup fails or the user asks for technical detail. If Python itself is
unavailable or too old, stop with one concrete instruction appropriate to the
user's operating system.

After preflight, read `python_executable` from `ecd-setup-status.json` and use
that executable instead of the generic `python` command for every remaining
plugin script. The private `.ecd-runtime` belongs to the working directory;
do not expose it as a user deliverable.

Find the article and Supporting Information PDFs in the open project folder.
If there is exactly one plausible article/SI pair, state their filenames and
continue. Ask the user to identify files only when there are multiple plausible
pairs or a required source is missing.

## Mandatory discovery gate

Do not begin calibration or digitization immediately after locating an ECD
figure. First inspect the complete article and all supplied supporting
information and build `candidate-curves.json`. Inspect every plotted curve,
but present one candidate per distinct experimental spectrum, not one per
appearance, page, or panel. Assign a stable `spectrum_key` from sample,
stereoisomer, experiment, and acquisition conditions. Merge repeated
renderings with the same key into `occurrences`, preserve every source
location, and recommend the cleanest panel for extraction. Never merge spectra
merely because they have similar shapes.

A candidate is eligible only when the source establishes all of:

- the plot is an experimental ECD/CD spectrum rather than a computed trace;
- the curve can be linked unambiguously to a named compound and displayed
  chemical structure;
- the stereoisomer/enantiomer identity is explicit when the plot distinguishes
  stereoisomers;
- the measurement solvent is explicit and applies to that curve;
- the figure, page, caption/legend, curve label or color, axes, and units are
  identifiable.

Never infer a curve-to-structure or solvent link from proximity alone. Mark a
record `blocked` and state the missing or conflicting facts when any required
link is ambiguous.

Generate the review artifacts before asking the user:

```powershell
python scripts/generate_candidate_review.py candidate-curves.json --output-dir candidate-review
```

Show the user a compact numbered candidate table containing compound,
stereoisomer, curve label/color, solvent, source location, and eligibility.
Link `candidate-review.html` and display useful figure crops. Ask the user to
select one or more eligible candidates by number or name; keep internal IDs
available in the audit files but do not require the user to type them.
**Stop here.** Do not render at high
resolution, calibrate, trace, reconstruct, normalize, or validate a spectrum
until the user confirms the IDs. Record the confirmation, exact IDs, and UTC
time in `candidate-selection.json`.

If there are no eligible candidates, report the blocked records and stop
without offering extraction.

## Visual progress

Show progress in the conversation throughout the workflow. Maintain
`visual-progress.json` and `workflow-progress.html` from the beginning, not
only in the final package. Update them after every material transition:

```powershell
python scripts/update_workflow_progress.py WORKDIR --stage sources --status in_progress
python scripts/update_workflow_progress.py WORKDIR --stage candidates --status needs_review --detail "3 eligible candidates"
```

Use these ten stages and keep the status line ultrashort:

```text
[###-------] 3/10 · Candidate selection · REVIEW
```

Allowed states are `pending`, `in_progress`, `needs_review`, `complete`, and
`blocked`. Never count `needs_review` as complete. The ten stages are:
sources, candidates, selection, conditions, calibration, separation,
reconstruction, normalization, validation, report.

At candidates, calibration, separation, and validation, display the relevant
local image when available: candidate figure crops, calibration view, isolated
spectrum, and curve-level overlay.
Do not show the same full PDF page as evidence for multiple stages. Explain
what changed and what the user must inspect. Pause only at the human
checkpoints below.

Use user-facing labels `PENDIENTE`, `EN CURSO`, `REVISAR`, `COMPLETADO`, and
`BLOQUEADO` when speaking Spanish. At each checkpoint say only: what was
found, why the decision matters, and the single action required from the user.

## Required workflow

1. Inspect the article and every supplied supporting-information PDF. Locate
   candidate pages in each source:

```powershell
python scripts/locate_spectral_figures.py article.pdf --output candidates.json
```

2. Read each candidate page, caption, legend, experimental section, supporting
   information, and nearby tables. Search the complete article and supporting
   information for absolute-configuration assignments, crystal structures,
   deposition identifiers, synthetic correlation, chiroptical comparisons,
   optical rotation, chiral chromatography, and other stereochemical evidence.
   Confirm that each item refers to the measured sample or an explicitly
   correlated compound. Also confirm all measurement conditions and axes.
   Record the source location for every fact. Build and validate the
   curve-level candidate catalog, present eligible and blocked candidates, and
   require user selection as specified in the mandatory discovery gate.

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
When a different-color curve briefly overprints the selected trace, preserve
the observation-only data in `spectrum_raw.csv`. The extractor may bridge only
short, bracketed gaps up to `reconstruct_max_gap_columns`, writing every
derived point with `point_status=reconstructed_linear` to
`spectrum_reconstructed.csv`. Show reconstructed segments in orange and leave
long gaps open in the overlay, isolated spectrum, and HTML plot. Never replace
the raw CSV or silently connect an unresolved gap.
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
`extraction-report.md`, `workflow-progress.html`, `visual-progress.json`,
`candidate-curves.json`, `candidate-selection.json`, the CSV files, and
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

1. candidate selection after verifying experimental origin, chemical
   identity/structure, stereoisomer, curve, solvent, units, and source links;
2. calibration points when OCR or ticks are ambiguous;
3. final overlay and sign.

All other checks may run automatically. Escalate any validator warning.

## Final handoff

Summarize the final status of all ten stages. Link the candidate review,
progress monitor, and final HTML and Markdown
reports and each canonical CSV. State explicitly which spectra are approved,
pending review, rejected, or unsuitable for simulation comparison.

## References

- Read `references/ecd-units-and-conventions.md` before converting axes or
  intensities.
- Read `references/metadata-schema.md` when creating or repairing a package.
- Read `references/quality-criteria.md` when accepting, rejecting, or assigning
  a quality grade.
