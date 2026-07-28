import ast
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


review = load(
    "generate_candidate_review",
    "skills/extract-ecd-spectra/scripts/generate_candidate_review.py",
)
report = load(
    "generate_visual_report",
    "skills/extract-ecd-spectra/scripts/generate_visual_report.py",
)
preflight = load(
    "preflight_environment",
    "skills/extract-ecd-spectra/scripts/preflight_environment.py",
)
renderer = load(
    "render_pdf_page",
    "skills/extract-ecd-spectra/scripts/render_pdf_page.py",
)


def test_all_scripts_parse_with_declared_python_310_grammar():
    scripts = ROOT / "skills" / "extract-ecd-spectra" / "scripts"
    for path in scripts.glob("*.py"):
        ast.parse(
            path.read_text(encoding="utf-8-sig"),
            filename=str(path),
            feature_version=(3, 10),
        )


def test_preflight_reports_current_python_and_required_packages():
    result = preflight.inspect_environment(Path(preflight.sys.executable))
    assert result["python_supported"] is True
    assert set(result["missing_packages"]).issubset(set(preflight.REQUIRED))
    assert result["python_executable"]


def test_pymupdf_renderer_needs_no_poppler(tmp_path):
    pdf = tmp_path / "one-page.pdf"
    output = tmp_path / "page.png"
    document = renderer.fitz.open()
    document.new_page(width=200, height=100)
    document.save(pdf)
    document.close()

    renderer.render_page(pdf, 1, 144, output)

    assert output.exists()
    assert output.stat().st_size > 0


def test_candidate_requires_experimental_structure_and_solvent():
    item = {
        "candidate_id": "ECD-C01",
        "experimental": True,
        "compound": "E1",
        "structure_reference": "Scheme 1",
        "solvent": "MeCN",
        "source_location": "Figure 3",
        "curve_identity": "black",
        "axes_units": "nm; delta epsilon",
        "ambiguities": [],
    }
    assert review.assess(item) == ("eligible", [])
    item["solvent"] = ""
    status, reasons = review.assess(item)
    assert status == "blocked"
    assert "missing: solvent" in reasons


def test_candidate_ambiguity_blocks_extraction():
    item = {
        key: "known" for key in review.REQUIRED
    }
    item["experimental"] = True
    item["ambiguities"] = ["red/black legend assignment conflicts with caption"]
    status, reasons = review.assess(item)
    assert status == "blocked"
    assert reasons == ["red/black legend assignment conflicts with caption"]


def test_repeated_renderings_are_one_candidate_with_occurrences():
    base = {
        "experimental": True,
        "spectrum_key": "compound-e2|thf|experiment-1",
        "compound": "E2",
        "structure_reference": "Figure 1",
        "solvent": "THF",
        "axes_units": "nm; delta epsilon",
        "ambiguities": [],
    }
    candidates = [
        {
            **base,
            "candidate_id": "ECD-C02",
            "source_location": "Figure 3 top",
            "curve_identity": "red solid",
        },
        {
            **base,
            "candidate_id": "ECD-C03",
            "source_location": "Figure 3 bottom",
            "curve_identity": "black solid",
        },
    ]
    merged = review.deduplicate(candidates)
    assert len(merged) == 1
    assert merged[0]["candidate_id"] == "ECD-C02"
    assert merged[0]["merged_candidate_ids"] == ["ECD-C03"]
    assert len(merged[0]["occurrences"]) == 2


def test_final_report_reuses_ten_stage_monitor_and_escalates_warnings(tmp_path):
    stages = [
        {
            "id": stage_id,
            "label": stage_id.title(),
            "status": "complete",
            "detail": "done",
        }
        for stage_id in (
            "sources",
            "candidates",
            "selection",
            "conditions",
            "calibration",
            "separation",
            "reconstruction",
            "normalization",
            "validation",
            "report",
        )
    ]
    (tmp_path / "visual-progress.json").write_text(
        json.dumps({"stages": stages}), encoding="utf-8"
    )

    progress = report.build_progress(
        tmp_path,
        {},
        {"status": "warning", "warnings": ["Temperature not reported"]},
    )

    assert len(progress) == 10
    validation = next(item for item in progress if item["id"] == "validation")
    assert validation["status"] == "needs_review"
    assert "1 warning" in validation["detail"]
