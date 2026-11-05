"""Unit tests for LibraryScanner.scan_path, folder configs, and estimate bounds."""

import json
from unittest.mock import patch

import pytest

from conftest import make_meta
from mediacrush.core.scanner import CandidateFile, LibraryScanner, ScanReport


def scan(tmp_path, mapping):
    """mapping: relative filename -> MediaMetadata|None. Creates files and mocks probe."""
    for rel in mapping:
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"x")
    with patch("mediacrush.core.scanner.MediaProbe.inspect", side_effect=lambda p: mapping.get(p.relative_to(tmp_path).as_posix())):
        return LibraryScanner.scan_path(tmp_path)


class TestScanPath:
    def test_empty_dir(self, tmp_path):
        r = scan(tmp_path, {})
        assert r.candidates == [] and r.skipped_count == 0 and r.total_savings_bytes == 0

    def test_nonexistent(self, tmp_path):
        r = LibraryScanner.scan_path(tmp_path / "nope")
        assert r.candidates == []

    def test_candidate_and_skip_counts(self, tmp_path):
        big = make_meta(codec="h264", size_mb=1000, video_bitrate=9_000_000)
        small = make_meta(codec="h264", size_mb=10)
        r = scan(tmp_path, {"big.mkv": big, "small.mkv": small})
        assert len(r.candidates) == 1 and r.skipped_count == 1
        assert r.total_current_bytes == big.file_size_bytes
        assert 0 < r.total_estimated_bytes < r.total_current_bytes

    def test_unprobeable_not_counted_as_skipped(self, tmp_path):
        r = scan(tmp_path, {"bad.mkv": None})
        assert r.candidates == [] and r.skipped_count == 0

    def test_ignores_unsupported_extensions(self, tmp_path):
        (tmp_path / "a.txt").write_text("x")
        (tmp_path / "b.jpg").write_bytes(b"x")
        with patch("mediacrush.core.scanner.MediaProbe.inspect") as probe:
            LibraryScanner.scan_path(tmp_path)
        probe.assert_not_called()

    def test_extension_case_insensitive(self, tmp_path):
        r = scan(tmp_path, {"A.MKV": make_meta(size_mb=900)})
        assert len(r.candidates) == 1

    def test_recursive(self, tmp_path):
        r = scan(tmp_path, {"a/b/c/deep.mp4": make_meta(size_mb=900)})
        assert len(r.candidates) == 1

    def test_single_file_target(self, tmp_path):
        f = tmp_path / "one.mkv"
        f.write_bytes(b"x")
        with patch("mediacrush.core.scanner.MediaProbe.inspect", return_value=make_meta(size_mb=900)):
            r = LibraryScanner.scan_path(f)
        assert len(r.candidates) == 1

    def test_single_unsupported_file(self, tmp_path):
        f = tmp_path / "one.txt"
        f.write_text("x")
        assert LibraryScanner.scan_path(f).candidates == []


class TestFolderConfig:
    def test_missing_config(self, tmp_path):
        assert LibraryScanner.load_folder_config(tmp_path) == {}

    def test_valid_config(self, tmp_path):
        (tmp_path / ".mediacrush.json").write_text('{"preset": "saver"}')
        assert LibraryScanner.load_folder_config(tmp_path) == {"preset": "saver"}

    def test_corrupt_config_ignored(self, tmp_path):
        (tmp_path / ".mediacrush.json").write_text("{nope")
        assert LibraryScanner.load_folder_config(tmp_path) == {}

    def test_preset_override_propagates(self, tmp_path):
        (tmp_path / ".mediacrush.json").write_text(json.dumps({"preset": "film"}))
        r = scan(tmp_path, {"a.mkv": make_meta(size_mb=900)})
        assert r.candidates[0].local_preset == "film"

    def test_config_is_per_folder(self, tmp_path):
        (tmp_path / "x").mkdir()
        (tmp_path / "x" / ".mediacrush.json").write_text('{"preset": "saver"}')
        r = scan(tmp_path, {"x/a.mkv": make_meta("/f/a.mkv", size_mb=900), "b.mkv": make_meta("/f/b.mkv", size_mb=900)})
        presets = {c.metadata.path.name: c.local_preset for c in r.candidates}
        assert list(presets.values()).count("saver") == 1 and list(presets.values()).count(None) == 1

    def test_skip_already_hevc_false_disables_skip(self, tmp_path):
        eff = make_meta(codec="hevc", size_mb=300, video_bitrate=1_800_000)
        assert len(scan(tmp_path, {"a.mkv": eff}).candidates) == 0
        (tmp_path / ".mediacrush.json").write_text('{"skip_already_hevc": false}')
        assert len(scan(tmp_path, {"a.mkv": eff}).candidates) == 1


class TestShouldSkipEdges:
    @pytest.mark.parametrize("codec", ["hevc", "h265", "av1", "HEVC"])
    def test_modern_codecs_skipped_when_efficient(self, codec):
        assert LibraryScanner.should_skip(make_meta(codec=codec, size_mb=300, video_bitrate=1_000_000))[0]

    def test_hevc_high_bitrate_not_skipped(self):
        assert not LibraryScanner.should_skip(make_meta(codec="hevc", size_mb=900, video_bitrate=9_000_000))[0]

    def test_exactly_40mb_not_skipped(self):
        assert not LibraryScanner.should_skip(make_meta(size_mb=40))[0]

    def test_just_under_40mb_skipped(self):
        assert LibraryScanner.should_skip(make_meta(size_mb=39.9))[0]

    def test_falls_back_to_overall_bitrate(self):
        m = make_meta(codec="hevc", size_mb=300, video_bitrate=0, overall_bitrate=1_000_000)
        assert LibraryScanner.should_skip(m)[0]


class TestEstimate:
    @pytest.mark.parametrize("w,h", [(3840, 2160), (1920, 1080), (1280, 720), (640, 480)])
    def test_always_between_20_and_70_percent(self, w, h):
        m = make_meta(width=w, height=h, size_mb=1000, duration=3600)
        est = LibraryScanner.estimate_savings(m)
        assert m.file_size_bytes * 0.20 <= est <= m.file_size_bytes * 0.70

    def test_more_audio_streams_not_smaller(self):
        a = LibraryScanner.estimate_savings(make_meta(size_mb=10_000, duration=600, audio=1))
        b = LibraryScanner.estimate_savings(make_meta(size_mb=10_000, duration=600, audio=4))
        assert b >= a


class TestModels:
    def test_savings_percent(self):
        c = CandidateFile(make_meta(size_mb=100), "r", 40 * 1024 * 1024, 60 * 1024 * 1024)
        assert c.savings_percent == pytest.approx(60.0)

    def test_savings_percent_zero_size(self):
        assert CandidateFile(make_meta(size_mb=0), "r", 0, 0).savings_percent == 0.0

    def test_total_savings_never_negative(self, tmp_path):
        assert ScanReport(tmp_path, [], 0, 10, 50).total_savings_bytes == 0
