from pathlib import Path

from wms_export_checker.core import check_export, load_schema, render_markdown
from wms_export_checker.__main__ import main

ROOT = Path(__file__).resolve().parent.parent
EX = ROOT / "examples"


def checks(findings):
    return sorted({(f["table"], f["row"], f["check"]) for f in findings})


def test_sample_export_findings():
    f = check_export(EX / "sample_export", load_schema(EX / "schema.json"))
    got = checks(f)
    assert ("skus", 6, "duplicate_key") in got
    assert ("skus", 7, "bad_type") in got
    assert ("inbound_lines", 6, "orphan_reference") in got
    assert ("inbound_lines", 7, "out_of_range") in got
    assert ("inbound_lines", 8, "bad_type") in got
    assert ("inbound_lines", 9, "duplicate_key") in got
    assert ("inbound_lines", 10, "empty_required") in got
    assert ("inbound_lines", 5, "mixed_units") in got
    assert len(f) == 8


def test_clean_export(tmp_path):
    (tmp_path / "skus.csv").write_text("sku,description,unit,weight_kg\nA,a,EA,1\n")
    (tmp_path / "inbound_lines.csv").write_text(
        "line_id,po_number,sku,qty,unit,received_on\nL1,P1,A,2,EA,2026-01-02\n")
    assert check_export(tmp_path, load_schema(EX / "schema.json")) == []


def test_missing_file_and_column(tmp_path):
    (tmp_path / "skus.csv").write_text("sku,description\nA,a\n")
    f = check_export(tmp_path, load_schema(EX / "schema.json"))
    kinds = {x["check"] for x in f}
    assert {"missing_column", "missing_file"} <= kinds


def test_markdown_and_exit_code(tmp_path, capsys):
    out = tmp_path / "r.md"
    code = main([str(EX / "sample_export"), "--schema", str(EX / "schema.json"),
                 "--out", str(out)])
    assert code == 1
    text = out.read_text()
    assert "8 findings" in text and "invented example data" in text
    assert "Export looks ready" in render_markdown([])
