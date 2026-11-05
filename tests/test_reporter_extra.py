"""Additional reporter tests: JSON round-trip, HTML structure, formatting, known defects."""

import json

import pytest

from mediacrush.core.reporter import CompressionReporter, ReportEntry


def filled():
    r = CompressionReporter()
    r.add_result("a.mkv", 1000, 400, "libx265", 12.34, True)
    r.add_result("b.mkv", 2000, 2000, "libx265", 1.0, False)
    return r


class TestEntry:
    @pytest.mark.parametrize("o,f,pct", [(1000, 400, 60.0), (1000, 1000, 0.0), (1000, 1500, 0.0), (0, 0, 0.0)])
    def test_savings_pct(self, o, f, pct):
        assert ReportEntry("x", o, f, "e", 1, True).savings_pct == pytest.approx(pct)


class TestOutputs:
    def test_json_round_trip(self, tmp_path):
        p = tmp_path / "r.json"
        filled().write_json(p)
        data = json.loads(p.read_text())
        assert [d["file"] for d in data] == ["a.mkv", "b.mkv"]
        assert data[0]["success"] is True and data[1]["success"] is False

    def test_html_contains_rows_and_totals(self, tmp_path):
        p = tmp_path / "r.html"
        filled().write_html(p)
        html = p.read_text(encoding="utf-8")
        assert html.startswith("<!DOCTYPE html>") and "a.mkv" in html and "b.mkv" in html
        assert "✓" in html and "✗" in html
        assert "Total saved" in html and "20.0%" in html

    def test_empty_report_no_division_error(self, tmp_path):
        p = tmp_path / "e.html"
        CompressionReporter().write_html(p)
        assert "0.0%" in p.read_text(encoding="utf-8")

    @pytest.mark.parametrize("b,expected", [(0, "0.0 B"), (1023, "1023.0 B"), (1024, "1.0 KB"), (1024**2, "1.0 MB"), (1024**3, "1.0 GB")])
    def test_fmt_exact_units(self, b, expected):
        assert CompressionReporter._fmt(b) == expected

    def test_fmt_keeps_fraction(self):
        assert CompressionReporter._fmt(1536) == "1.5 KB"

    def test_html_escapes_filenames(self, tmp_path):
        r = CompressionReporter()
        r.add_result("<script>alert(1)</script>.mkv", 10, 5, "e", 1, True)
        p = tmp_path / "x.html"
        r.write_html(p)
        assert "<script>alert(1)" not in p.read_text(encoding="utf-8")
