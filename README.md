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

For multi-curve plots, the raster extractor preserves trace color identity,
rejects chromatic pixels when following black or gray curves, suppresses dense
vertical plot geometry, and records these decisions in the final report.
Ambiguous same-color crossings remain a supervised WebPlotDigitizer or Engauge
task.

The package also records stereochemical evidence from the article and
supporting information: crystal-structure availability and deposition
identifiers, absolute-structure refinement data, chemical or synthetic
correlations, chiroptical comparisons, optical rotation, and chromatographic
evidence. Each observation is linked to its source and to the measured sample;
spectral quality and stereochemical-assignment confidence are assessed
separately.

## Before you start

Choose a paper that contains experimental ECD spectra. Download both the
article and its Supporting Information as PDF files and put them together in a
new folder. The solvent, compound structure, and identity of the curve must be
clear in the paper; the plugin will stop when any of these links is ambiguous.

If you prefer a prepared training case, use the
[oxo-helicene example](examples/acs-omega-oxohelicene/README.md).

## Install in Codex from GitHub

1. Install and open the Codex desktop app.
2. Open its terminal and paste these two commands:

```powershell
codex plugin marketplace add marcostrasto/ecd-spectra
codex plugin add ecd-spectra@ecd-spectra
```

3. Restart Codex and open the folder containing your PDFs as a new project.
4. Start a new conversation and write:

```text
Use $extract-ecd-spectra with the article and Supporting Information in this
folder. First show me the experimental ECD curves that can be identified
unambiguously. Do not extract anything until I choose a candidate.
```

The plugin first shows a short candidate list. Select an eligible curve by its
number. It then displays a ten-step progress monitor and pauses only when it
needs you to confirm the candidate, an ambiguous calibration, or the final
curve overlay.

## What the result means

- **Complete**: that stage finished without a pending decision.
- **Review**: the files were produced, but a person must inspect a warning.
- **Blocked**: the available evidence is insufficient for a defensible result.

The final folder contains the numerical spectrum, metadata, source evidence,
diagnostic images, and an HTML report. A warning is not silently counted as a
fully completed validation.

## Technical requirements

The current beta uses Python 3.10 or newer, the packages in
`requirements.txt`, and Poppler (`pdftoppm`) for PDF rendering. Codex may ask
permission to install a missing local dependency. WebPlotDigitizer or Engauge
Digitizer is required only when curves cannot be separated safely by the
automatic workflow.

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

No reuse license has been assigned yet. The repository may be inspected and
tested publicly, but reuse terms must be selected before presenting it as an
open-source release.
