# ECD Spectra

Codex plugin for precise, auditable extraction and standardization of
experimental electronic circular dichroism (ECD/CD) spectra and their
measurement conditions from scientific literature.

The plugin contains the `extract-ecd-spectra` skill. It prioritizes original
numerical data and vector recovery, supports raster tracing when appropriate,
and requires human confirmation of chemical identity, calibration, sign, and
the final extraction overlay. During execution it shows numbered progress,
figure crops, calibration views, isolated curves, and curve-level overlays.
Each completed spectrum package includes a self-contained visual HTML report
and a Markdown report; neither requires a server or network connection. It
preserves the reported solvent description and
also records structured solvent components, mixture ratios, provenance,
concentration, path length, temperature, and other available acquisition
conditions needed for subsequent simulation.

The package also records stereochemical evidence from the article and
supporting information: crystal-structure availability and deposition
identifiers, absolute-structure refinement data, chemical or synthetic
correlations, chiroptical comparisons, optical rotation, and chromatographic
evidence. Each observation is linked to its source and to the measured sample;
spectral quality and stereochemical-assignment confidence are assessed
separately.

## Requirements

- Codex with personal or team plugins enabled
- Python 3.10 or newer
- Python packages listed in `requirements.txt`
- Poppler (`pdftoppm`) for rendering PDF pages
- WebPlotDigitizer or Engauge Digitizer for curves that cannot be separated
  reliably by the automated raster workflow

Install Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Installation in Codex

Clone this repository, then install or load the repository root as a Codex
plugin. The manifest is in `.codex-plugin/plugin.json`; the skill is discovered
from `skills/`.

Invoke it explicitly with:

```text
$extract-ecd-spectra
```

## Reproducibility and copyright

The repository contains workflow code, templates, and documentation only. It
does not include publisher PDFs or digitized literature spectra. Keep those
materials in a separate, access-controlled research directory and record their
bibliographic identifiers in each spectrum package.

## Worked example

[`examples/acs-omega-oxohelicene/`](examples/acs-omega-oxohelicene/)
provides an end-to-end training case based on a rigid organic
7,12,17-trioxa[11]helicene. It includes:

- an official-source download script with SHA-256 verification;
- direct article, Supporting Information, DOI, and PubMed Central links;
- an exact Codex prompt for running `$extract-ecd-spectra`;
- an expected inventory of ECD conditions and stereochemical evidence;
- explicit guidance to separate the experimental E1 and E2 curves in Figure 3.
- visual progress in the conversation and a final HTML/Markdown report.

The publisher PDFs remain outside version control and are downloaded locally
only when the example is run.

## Validation policy

Automated extraction is provisional. A spectrum is accepted only after a person
checks the isolated curve and overlay, verifies axes and sign, and records
approval in the package metadata.

No open-source license has been assigned yet. Add one only after choosing the
intended reuse terms.
