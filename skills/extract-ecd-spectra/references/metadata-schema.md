# Spectrum package metadata

`metadata.json` must contain:

- `spectrum_id`
- `source.reference_id`, DOI when known, page, figure, panel, and file
- `compound.name`, stereoisomer, and assignment source
- `compound.stereochemistry.reported_assignment`, `assignment_status`,
  `assignment_scope`, evidence list, crystal-structure search, and human
  assessment
- `experiment.solvent.reported_as`: verbatim solvent description
- `experiment.solvent.components`: one entry per solvent, with `name`,
  `normalized_name`, optional identifier, fraction, and fraction unit
- `experiment.solvent.mixture_ratio_reported_as`, `source_location`, and
  `status`: `resolved`, `partially_resolved`, `unreported`, or `unresolved`
- `experiment.temperature_K`, concentration, path length, instrument, cell
  material, bandwidth, scan rate, number of scans, pH, and other reported
  conditions
- `axes.x_quantity`, `axes.x_unit`, `axes.y_quantity`, `axes.y_unit`
- `extraction.source_type`: original, vector, raster, or supervised_digitizer
- extraction tool, resolution, calibration points, and trace-selection rule
- every processing operation
- quality metrics and warnings
- `human_validation.status`, validator, date, and notes

Use `null` for information not reported. Do not replace missing values with
assumptions.

## Stereochemistry rules

Set `assignment_status` to `assigned`, `relative_only`, `racemic`,
`unreported`, or `unresolved`. For every evidence item record:

- `type`: `xray_anomalous`, `xray_relative`, `chemical_correlation`,
  `stereospecific_synthesis`, `ecd_comparison`, `vcd_comparison`,
  `optical_rotation_comparison`, `nmr_chiral_reagent`,
  `chiral_chromatography`, or `other`;
- `reported_observation` and `reported_conclusion`;
- supported configuration and whether the evidence applies directly to the
  measured sample;
- source location, related compound or precursor, and bibliographic or
  deposition identifier;
- `directness`: `direct`, `indirect`, or `supporting_only`;
- author-reported confidence and reviewer notes.

Keep evidence and conclusion separate. Optical-rotation or ECD sign alone,
enantiomeric excess, and chiral-chromatography retention order establish
neither absolute configuration nor identity without an explicit correlation.

For `crystal_structure`, record:

- `availability`: `available`, `reported_no_deposition`,
  `reported_not_accessible`, `not_found`, or `not_searched`;
- whether it is the same compound and stereoisomer as the measured sample;
- CCDC, ICSD, COD, PDB, DOI, or other deposition identifiers;
- whether absolute structure was determined and the reported Flack, Hooft, or
  equivalent refinement statistics;
- source locations, resources searched, search date, and notes.

Use `not_found` only after documenting the searched sources. A crystal of a
precursor, derivative, salt, solvate, or related compound is correlation
evidence, not automatically a structure of the measured analyte.

Example evidence item:

```json
{
  "type": "chemical_correlation",
  "reported_observation": "Product obtained from a precursor of known configuration",
  "reported_conclusion": "Assigned as (P)",
  "supports_assignment": "(P)",
  "applies_to_measured_sample": true,
  "related_compound": "precursor 7",
  "identifier": null,
  "source_location": "Supporting Information, page S18",
  "directness": "indirect",
  "author_reported_confidence": null,
  "reviewer_notes": "Requires verification that no stereomutation occurs."
}
```

## Solvent rules

- Preserve the exact published wording in `reported_as`.
- Normalize names only when the identity is unambiguous. Do not silently map a
  generic term such as "alcohol" or an unexplained abbreviation.
- For mixtures, create one component per solvent and preserve the reported
  ratio separately. Populate numeric fractions only when both values and their
  basis (`v/v`, `w/w`, `mol/mol`, or another explicit unit) are given.
- Record where the condition was found: caption, main-text page, experimental
  section, supporting-information page, table, or deposited data.
- Do not infer solvent from a synthesis, purification, NMR, or chromatography
  section unless the source explicitly associates it with the ECD measurement.
- Set `status` to `unreported` when the searched sources contain no measurement
  solvent, and to `unresolved` when a reported description cannot be assigned
  confidently.

Example:

```json
{
  "experiment": {
    "solvent": {
      "reported_as": "MeCN/H2O (9:1, v/v)",
      "components": [
        {
          "name": "MeCN",
          "normalized_name": "acetonitrile",
          "identifier": "CAS 75-05-8",
          "fraction": 0.9,
          "fraction_unit": "v/v"
        },
        {
          "name": "H2O",
          "normalized_name": "water",
          "identifier": "CAS 7732-18-5",
          "fraction": 0.1,
          "fraction_unit": "v/v"
        }
      ],
      "mixture_ratio_reported_as": "9:1, v/v",
      "source_location": "Figure 2 caption, page 5",
      "status": "resolved"
    }
  }
}
```

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
visual-progress.json
extraction-report.html
extraction-report.md
```
