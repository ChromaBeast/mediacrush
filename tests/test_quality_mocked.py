"""Unit tests for QualityChecker verdicts and log parsing (ffmpeg mocked)."""

import json
from unittest.mock import patch

import pytest

from mediacrush.core.quality import QualityChecker, QualityScore


@pytest.mark.parametrize("vmaf,verdict", [
    (100, "Excellent"), (92.0, "Excellent"), (91.99, "Good"), (80.0, "Good"),
    (79.9, "Acceptable"), (65.0, "Acceptable"), (64.9, "Poor"), (0, "Poor"),
])
def test_verdict_boundaries(vmaf, verdict):
    assert QualityChecker._calculate_verdict(vmaf) == verdict


class TestScore:
    def test_missing_inputs(self, tmp_path):
        f = tmp_path / "a.mkv"
        f.write_bytes(b"x")
        assert QualityChecker.score(f, tmp_path / "none.mkv") is None
        assert QualityChecker.score(tmp_path / "none.mkv", f) is None

    def test_combines_vmaf_ssim(self, tmp_path):
        f = tmp_path / "a.mkv"
        f.write_bytes(b"x")
        with patch.object(QualityChecker, "_run_vmaf", return_value=93.456), \
             patch.object(QualityChecker, "_run_ssim", return_value=0.98765):
            s = QualityChecker.score(f, f)
        assert s == QualityScore(93.46, 0.9877, "Excellent")

    def test_vmaf_failure_returns_none(self, tmp_path):
        f = tmp_path / "a.mkv"
        f.write_bytes(b"x")
        with patch.object(QualityChecker, "_run_vmaf", return_value=None):
            assert QualityChecker.score(f, f) is None

    def test_ssim_failure_uses_default(self, tmp_path):
        f = tmp_path / "a.mkv"
        f.write_bytes(b"x")
        with patch.object(QualityChecker, "_run_vmaf", return_value=70.0), \
             patch.object(QualityChecker, "_run_ssim", return_value=None):
            assert QualityChecker.score(f, f).ssim == 0.95


class TestLogParsing:
    def test_vmaf_json(self, tmp_path):
        log = tmp_path / "v.json"
        log.write_text(json.dumps({"pooled_metrics": {"vmaf": {"mean": 88.5}}}))
        with patch("mediacrush.core.quality.subprocess.run"):
            assert QualityChecker._run_vmaf(tmp_path / "s", tmp_path / "e", log) == 88.5

    def test_vmaf_no_log(self, tmp_path):
        with patch("mediacrush.core.quality.subprocess.run"):
            assert QualityChecker._run_vmaf(tmp_path / "s", tmp_path / "e", tmp_path / "none.json") is None

    def test_vmaf_corrupt_log(self, tmp_path):
        log = tmp_path / "v.json"
        log.write_text("{{")
        with patch("mediacrush.core.quality.subprocess.run"):
            assert QualityChecker._run_vmaf(tmp_path / "s", tmp_path / "e", log) is None

    def test_vmaf_ffmpeg_missing(self, tmp_path):
        with patch("mediacrush.core.quality.subprocess.run", side_effect=FileNotFoundError):
            assert QualityChecker._run_vmaf(tmp_path / "s", tmp_path / "e", tmp_path / "l") is None

    def test_ssim_average(self, tmp_path):
        log = tmp_path / "s.txt"
        log.write_text("n:1 Y:1 U:1 V:1 All:0.90 (10)\nn:2 Y:1 U:1 V:1 All:1.00 (20)\n")
        with patch("mediacrush.core.quality.subprocess.run"):
            assert QualityChecker._run_ssim(tmp_path / "s", tmp_path / "e", log) == pytest.approx(0.95)

    def test_ssim_empty_log(self, tmp_path):
        log = tmp_path / "s.txt"
        log.write_text("")
        with patch("mediacrush.core.quality.subprocess.run"):
            assert QualityChecker._run_ssim(tmp_path / "s", tmp_path / "e", log) is None

    def test_windows_paths_normalized_in_filter(self, tmp_path):
        with patch("mediacrush.core.quality.subprocess.run") as run:
            QualityChecker._run_vmaf(tmp_path / "s", tmp_path / "e", tmp_path / "v.json")
        filt = run.call_args[0][0][run.call_args[0][0].index("-lavfi") + 1]
        assert "\\" not in filt
