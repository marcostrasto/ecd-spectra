# Spectrum package metadata

`metadata.json` must contain:

- `spectrum_id`
- `source.reference_id`, DOI when known, page, figure, panel, and file
- `compound.name`, stereoisomer, and assignment source
- `experiment.solvent`, temperature, concentration, path length when reported
- `axes.x_quantity`, `axes.x_unit`, `axes.y_quantity`, `axes.y_unit`
- `extraction.source_type`: original, vector, raster, or supervised_digitizer
- extraction tool, resolution, calibration points, and trace-selection rule
- every processing operation
- quality metrics and warnings
- `human_validation.status`, validator, date, and notes

Use `null` for information not reported. Do not replace missing values with
assumptions.

Required package files:

```text
spectrum_raw.csv
spectrum_canonical.csv
metadata.json
source_figure.png
source_page.png
trace_mask.png
extraction_overlay.png
isolated_spectrum.png
quality_report.json
```
