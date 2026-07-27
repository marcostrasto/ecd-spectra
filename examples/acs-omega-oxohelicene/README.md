# Worked example: an organic oxo-helicene

This example uses the open-access ACS Omega article:

> T. B. Demissie et al., "Origins of Optical Activity in an
> Oxo-Helicene: Experimental and Computational Studies", *ACS Omega*
> **2021**, *6*, 2420-2428. DOI:
> [10.1021/acsomega.0c06079](https://doi.org/10.1021/acsomega.0c06079).

It is a useful training case because it concerns a large, relatively rigid
organic 7,12,17-trioxa[11]helicene and reports experimental ECD spectra for
both enantiomers. The article also provides the solvent and acquisition
conditions, an independent crystal structure from the preceding synthesis
paper, chiral HPLC resolution, optical rotations, and computed spectra.

The publisher material is distributed under CC BY-NC-ND. It is not committed
to this repository. The download script obtains an unmodified archive from the
official PubMed Central distribution service and verifies the PDFs against
known SHA-256 hashes. Consult the publisher license before redistributing the
downloaded files or any adapted figures.

## 1. Download the source PDFs

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File `
  examples/acs-omega-oxohelicene/download-source.ps1
```

This creates an ignored `source/` directory containing:

- `article.pdf`
- `supporting-information.pdf`

## 2. Run the skill

Use this prompt in Codex:

```text
Use $extract-ecd-spectra on
examples/acs-omega-oxohelicene/source/article.pdf and
examples/acs-omega-oxohelicene/source/supporting-information.pdf.
First inventory all experimental ECD curves, experimental conditions, sample
identities, and stereochemical evidence. Then extract the separate E1 and E2
experimental curves from Figure 3 into auditable spectrum packages. Do not
extract the calculated E2 curve as experimental data. Stop for my approval of
the calibration and each final overlay.
```

## 3. What the user should see

The automatic locator should rank article page 3 (printed page 2422) first.
Figure 3 contains two panels:

- top: experimental E1 and E2 ECD curves;
- bottom: experimental and calculated E2 curves.

The curves overlap and use line style as part of their identity. This makes the
case a supervised digitization example: use WebPlotDigitizer or Engauge unless
clean vector paths can be isolated and verified. A whole-page overlay is not
acceptable. The user must review a crop of the actual panel and a curve-level
overlay for each exported trace.

Compare the extracted inventory with
[`expected-observations.json`](expected-observations.json). That file is a
checkpoint, not pre-extracted spectrum data.

## Source links

- [ACS article and Supporting Information](https://pubs.acs.org/doi/10.1021/acsomega.0c06079)
- [PubMed Central record](https://pmc.ncbi.nlm.nih.gov/articles/PMC7841950/)
- [Supporting Information at ACS](https://pubs.acs.org/doi/suppl/10.1021/acsomega.0c06079/suppl_file/ao0c06079_si_001.pdf)

