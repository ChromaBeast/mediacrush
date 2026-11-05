"""Unit tests for CLI formatters."""

from pathlib import Path

import pytest
from rich.console import Console

from conftest import make_meta
from mediacrush.cli import formatters
from mediacrush.core.hardware import EncoderInfo
from mediacrush.core.scanner import CandidateFile, ScanReport


@pytest.mark.parametrize("size,out", [
    (0, "0.0 MB"), (1024**2, "1.0 MB"), (5 * 1024**2, "5.0 MB"),
    (1024**3 - 1, "1024.0 MB"), (1024**3, "1.00 GB"), (int(2.5 * 1024**3), "2.50 GB"),
])
def test_format_bytes(size, out):
    assert formatters.format_bytes(size) == out


@pytest.fixture
def captured(monkeypatch):
    c = Console(record=True, width=200)
    monkeypatch.setattr(formatters, "console", c)
    return c


def test_banner(captured):
    formatters.print_banner()
    assert "MediaCrush" in captured.export_text()


def test_encoder_table_marks_active(captured):
    a = EncoderInfo("hevc", "hevc_nvenc", "NVIDIA", "cuda", "")
    b = EncoderInfo("hevc", "libx265", "CPU", None, "")
    formatters.print_encoders_table([a, b], a)
    text = captured.export_text()
    assert "hevc_nvenc" in text and "libx265" in text and text.count("Active") == 1


def test_scan_report_table(captured):
    cand = CandidateFile(make_meta("/lib/Show.mkv", size_mb=1000), "r", 300 * 1024**2, 700 * 1024**2)
    formatters.print_scan_report(ScanReport(Path("/lib"), [cand], 2, cand.metadata.file_size_bytes, cand.estimated_size_bytes))
    t = captured.export_text()
    assert "Show.mkv" in t and "H264" in t and "1080p" in t and "70.0%" in t and "Skipped 2" in t


def test_scan_report_empty(captured):
    formatters.print_scan_report(ScanReport(Path("/lib"), [], 0, 0, 0))
    assert "Found: 0" in captured.export_text()
