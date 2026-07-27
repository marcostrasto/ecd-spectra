# ECD units and conventions

## Spectral axis

Preserve the published x values in `spectrum_raw.csv`. In the canonical file
store all derivable axes:

- `wavelength_nm`
- `energy_eV = 1239.8419843320026 / wavelength_nm`
- `wavenumber_cm-1 = 10000000 / wavelength_nm`

Reject zero or negative wavelengths/energies. Sorting by increasing wavelength
reverses data originally published with increasing energy; this is not a sign
change.

## Intensity

Preserve the published quantity and unit. Common quantities include:

- differential molar extinction, delta epsilon, usually `M-1_cm-1`;
- ellipticity or instrument signal in `mdeg`;
- molar ellipticity;
- arbitrary or normalized intensity.

Do not convert mdeg to delta epsilon without the required concentration, path
length, and an unambiguous definition. Never infer an intensity scale from the
visual height of a normalized plot.

## Sign and handedness

Record exactly which enantiomer the curve represents and how the source assigns
it. Do not infer P/M or R/S solely from the sign of a band. Never invert a curve
to match a calculation. Store any deliberate inversion as a new derived
dataset with explicit provenance.

## Transformations

Keep raw and canonical data distinct. Record interpolation, smoothing,
normalization, baseline correction, wavelength shift, and amplitude scaling.
The default is none.

