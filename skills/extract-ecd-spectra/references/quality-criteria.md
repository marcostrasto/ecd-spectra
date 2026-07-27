# Quality criteria

## Mandatory rejection conditions

- unknown x-axis calibration or unit;
- unresolved curve identity;
- unresolved experimental sign or enantiomer;
- missing zero line when the y sign cannot otherwise be calibrated;
- severe overlap that prevents trace separation;
- overlay visibly following axes, labels, or another curve;
- unrecorded smoothing, normalization, shifting, or scaling.

## Automatic checks

- finite numeric points;
- strictly monotonic canonical wavelength;
- plausible wavelength/energy domain;
- both positive and negative values permitted;
- no duplicated x values after canonicalization;
- sufficient number and coverage of extracted columns;
- no long internal gaps;
- required files and metadata present.

## Grades

- **A:** original numerical data or clean vector recovery, full metadata.
- **B:** high-resolution raster, clean trace, approved overlay.
- **C:** supervised extraction with limited resolution or minor ambiguity;
  suitable for qualitative shape comparison only.
- **Reject:** any mandatory rejection condition.

Record the grade and intended comparison type. Human overlay approval is
mandatory for B and C.

