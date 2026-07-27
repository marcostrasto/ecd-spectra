from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


REQUIRED_FILES = [
    "spectrum_raw.csv",
    "spectrum_canonical.csv",
    "metadata.json",
    "source_page.png",
    "source_figure.png",
    "trace_mask.png",
    "extraction_overlay.png",
    "isolated_spectrum.png",
]


def nested(data: dict, path: str):
    value = data
    for key in path.split("."):
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate an ECD spectrum package.")
    parser.add_argument("package", type=Path)
    args = parser.parse_args()

    errors, warnings = [], []
    for name in REQUIRED_FILES:
        if not (args.package / name).exists():
            errors.append(f"Missing required file: {name}")

    metadata = {}
    solvent_status = "missing"
    stereochemistry_status = "missing"
    metadata_path = args.package / "metadata.json"
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        for field in [
            "spectrum_id",
            "source.reference_id",
            "compound.name",
            "compound.stereoisomer",
            "axes.x_unit",
            "axes.y_unit",
            "extraction.source_type",
            "human_validation.status",
        ]:
            value = nested(metadata, field)
            if value in (None, ""):
                warnings.append(f"Missing or empty metadata: {field}")

        solvent = nested(metadata, "experiment.solvent")
        if not isinstance(solvent, dict):
            warnings.append(
                "Missing structured solvent metadata: experiment.solvent"
            )
            solvent_status = "missing"
        else:
            solvent_status = solvent.get("status")
            if solvent_status not in {
                "resolved",
                "partially_resolved",
                "unreported",
                "unresolved",
            }:
                warnings.append("Invalid or missing experiment.solvent.status")
            if not solvent.get("reported_as") and solvent_status not in {
                "unreported",
                "unresolved",
            }:
                warnings.append("Missing experiment.solvent.reported_as")
            if not solvent.get("source_location"):
                warnings.append("Missing experiment.solvent.source_location")
            components = solvent.get("components")
            if solvent_status in {"resolved", "partially_resolved"}:
                if not isinstance(components, list) or not components:
                    warnings.append("Missing experiment.solvent.components")
                elif any(
                    not isinstance(component, dict) or not component.get("name")
                    for component in components
                ):
                    warnings.append(
                        "Each experiment.solvent component requires a name"
                    )
            if isinstance(components, list) and len(components) > 1:
                if not solvent.get("mixture_ratio_reported_as"):
                    warnings.append(
                        "Solvent mixture lacks mixture_ratio_reported_as"
                    )
                fraction_units = {
                    component.get("fraction_unit")
                    for component in components
                    if isinstance(component, dict)
                    and component.get("fraction") is not None
                }
                if len(fraction_units) > 1:
                    warnings.append(
                        "Solvent component fractions use inconsistent units"
                    )

        for field in [
            "experiment.concentration.value",
            "experiment.path_length.value",
            "experiment.temperature_K",
        ]:
            if nested(metadata, field) is None:
                warnings.append(f"Experimental condition not reported: {field}")

        stereochemistry = nested(metadata, "compound.stereochemistry")
        if not isinstance(stereochemistry, dict):
            warnings.append(
                "Missing structured stereochemical metadata: "
                "compound.stereochemistry"
            )
        else:
            stereochemistry_status = stereochemistry.get("assignment_status")
            if stereochemistry_status not in {
                "assigned",
                "relative_only",
                "racemic",
                "unreported",
                "unresolved",
            }:
                warnings.append(
                    "Invalid or missing stereochemistry.assignment_status"
                )
            evidence = stereochemistry.get("evidence")
            if not isinstance(evidence, list):
                warnings.append("stereochemistry.evidence must be a list")
                evidence = []
            for index, item in enumerate(evidence):
                if not isinstance(item, dict):
                    warnings.append(
                        f"Invalid stereochemical evidence item: {index}"
                    )
                    continue
                for field in [
                    "type",
                    "reported_observation",
                    "reported_conclusion",
                    "source_location",
                    "directness",
                ]:
                    if item.get(field) in (None, ""):
                        warnings.append(
                            "Missing stereochemical evidence field "
                            f"{index}.{field}"
                        )
                if item.get("type") in {
                    "optical_rotation_comparison",
                    "ecd_comparison",
                    "chiral_chromatography",
                } and item.get("directness") == "direct":
                    warnings.append(
                        f"Evidence item {index} should not be marked direct "
                        "without an independent absolute-configuration link"
                    )

            crystal = stereochemistry.get("crystal_structure")
            if not isinstance(crystal, dict):
                warnings.append(
                    "Missing stereochemistry.crystal_structure record"
                )
            else:
                availability = crystal.get("availability")
                if availability not in {
                    "available",
                    "reported_no_deposition",
                    "reported_not_accessible",
                    "not_found",
                    "not_searched",
                }:
                    warnings.append(
                        "Invalid crystal_structure.availability"
                    )
                if availability == "available" and not crystal.get(
                    "deposition_identifiers"
                ):
                    warnings.append(
                        "Available crystal structure lacks deposition identifier"
                    )
                if availability == "not_found" and (
                    not crystal.get("resources_searched")
                    or not crystal.get("search_date")
                ):
                    warnings.append(
                        "Crystal structure not_found requires search scope and date"
                    )
            assessment = stereochemistry.get("human_assessment")
            if not isinstance(assessment, dict) or assessment.get(
                "status"
            ) != "approved":
                warnings.append(
                    "Stereochemical evidence has not received human approval"
                )
    canonical = args.package / "spectrum_canonical.csv"
    point_count = 0
    if canonical.exists():
        with canonical.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        point_count = len(rows)
        if point_count < 20:
            errors.append("Canonical spectrum has fewer than 20 points")
        wavelengths = []
        for row in rows:
            try:
                values = [
                    float(row["wavelength_nm"]),
                    float(row["energy_eV"]),
                    float(row["wavenumber_cm-1"]),
                    float(row["intensity"]),
                ]
            except (KeyError, TypeError, ValueError):
                errors.append("Canonical CSV has invalid or missing numeric columns")
                break
            if not all(math.isfinite(value) for value in values):
                errors.append("Canonical CSV contains non-finite values")
                break
            wavelengths.append(values[0])
        if wavelengths:
            if any(b <= a for a, b in zip(wavelengths, wavelengths[1:])):
                errors.append("Canonical wavelength axis is not strictly increasing")
            if min(wavelengths) < 80 or max(wavelengths) > 5000:
                warnings.append("Wavelength domain falls outside 80-5000 nm")
            if len(set(wavelengths)) != len(wavelengths):
                errors.append("Duplicate canonical wavelengths")

    validation = nested(metadata, "human_validation.status")
    if validation != "approved":
        warnings.append("Human validation has not been approved")
    status = "pass" if not errors and not warnings else ("warning" if not errors else "fail")
    report = {
        "status": status,
        "point_count": point_count,
        "errors": errors,
        "warnings": warnings,
        "human_validation_required": validation != "approved",
        "simulation_readiness": {
            "solvent_aware_comparison": solvent_status == "resolved",
            "solvent_status": solvent_status,
            "stereoisomer_specific_comparison": (
                stereochemistry_status == "assigned"
                and nested(
                    metadata,
                    "compound.stereochemistry.human_assessment.status",
                )
                == "approved"
            ),
            "stereochemistry_status": stereochemistry_status,
        },
    }
    report_path = args.package / "quality_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
