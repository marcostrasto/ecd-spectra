# Quality criteria

## Mandatory rejection conditions

- unknown x-axis calibration or unit;
- unresolved curve identity;
- unresolved experimental sign or enantiomer;
- missing zero line when the y sign cannot otherwise be calibrated;
- severe overlap that prevents trace separation;
- overlay visibly following axes, labels, or another curve;
- unrecorded smoothing, normalization, shifting, or scaling.
- unresolved association between the spectrum and the stated stereoisomer.

An unresolved solvent does not invalidate the digitized curve itself, but it
does reject a package for direct solvent-aware simulation comparison.

## Automatic checks

- finite numeric points;
- strictly monotonic canonical wavelength;
- plausible wavelength/energy domain;
- both positive and negative values permitted;
- no duplicated x values after canonicalization;
- sufficient number and coverage of extracted columns;
- no long internal gaps;
- required files and metadata present.
- solvent identity, mixture composition, provenance, concentration, path
  length, and temperature metadata;
- explicit simulation-readiness status when solvent information is incomplete.
- structured stereochemical evidence, evidence-to-sample relationship, crystal
  structure availability, deposition identifiers, and source locations.

## Grades

- **A:** original numerical data or clean vector recovery, full spectral and
  experimental metadata.
- **B:** high-resolution raster, clean trace, approved overlay.
- **C:** supervised extraction with limited resolution or minor ambiguity;
  suitable for qualitative shape comparison only.
- **Reject:** any mandatory rejection condition.

Record the grade and intended comparison type. Human overlay approval is
mandatory for B and C.

Report spectral-extraction quality separately from stereochemical-assignment
confidence. A high-quality curve does not compensate for an uncertain
enantiomer assignment.
