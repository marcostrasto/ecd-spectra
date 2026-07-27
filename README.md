# ECD Spectra

Codex plugin for auditable extraction, digitization, standardization, and
validation of experimental electronic circular dichroism (ECD/CD) spectra from
scholarly PDFs and plot images.

The plugin contains the `extract-ecd-spectra` skill. It prioritizes original
numerical data and vector recovery, supports raster tracing when appropriate,
and requires human confirmation of chemical identity, calibration, sign, and
the final extraction overlay.

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

## Validation policy

Automated extraction is provisional. A spectrum is accepted only after a person
checks the isolated curve and overlay, verifies axes and sign, and records
approval in the package metadata.

No open-source license has been assigned yet. Add one only after choosing the
intended reuse terms.
