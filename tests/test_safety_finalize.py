"""Unit tests for SafetyManager verify/finalize/cleanup using real temp files."""

from unittest.mock import patch

import pytest

from conftest import make_meta
from mediacrush.core.safety import SafetyManager


@pytest.fixture
def files(tmp_path):
    src = tmp_path / "movie.mkv"
    stg = SafetyManager.get_staging_path(src)
    src.write_bytes(b"ORIGINAL")
    stg.write_bytes(b"NEW")
    return src, stg


class TestFinalize:
    def test_in_place_replaces_source(self, files):
        src, stg = files
        out = SafetyManager.finalize_transcode(src, stg, in_place=True)
        assert out == src and src.read_bytes() == b"NEW" and not stg.exists()

    def test_in_place_keep_backup(self, files):
        src, stg = files
        SafetyManager.finalize_transcode(src, stg, in_place=True, keep_backup=True)
        bak = src.with_name("movie.mkv.bak")
        assert bak.read_bytes() == b"ORIGINAL" and src.read_bytes() == b"NEW"

    def test_side_by_side_preserves_original(self, files):
        src, stg = files
        out = SafetyManager.finalize_transcode(src, stg, in_place=False)
        assert out.name == "movie.crushed.mkv"
        assert src.read_bytes() == b"ORIGINAL" and out.read_bytes() == b"NEW"

    def test_side_by_side_overwrites_stale_output(self, files):
        src, stg = files
        stale = src.with_name("movie.crushed.mkv")
        stale.write_bytes(b"STALE")
        SafetyManager.finalize_transcode(src, stg, in_place=False)
        assert stale.read_bytes() == b"NEW"


class TestCleanup:
    def test_removes_existing(self, files):
        _, stg = files
        SafetyManager.cleanup_staging(stg)
        assert not stg.exists()

    def test_swallows_unlink_errors(self, files):
        _, stg = files
        with patch("pathlib.Path.unlink", side_effect=PermissionError):
            SafetyManager.cleanup_staging(stg)  # must not raise


class TestVerify:
    def _stage(self, tmp_path, size=2_000_000):
        s = tmp_path / "s.mkv"
        s.write_bytes(b"\0" * size)
        return s

    def test_too_small(self, tmp_path):
        ok, msg = SafetyManager.verify_transcode(make_meta(), self._stage(tmp_path, 10))
        assert not ok and "small" in msg

    def test_unreadable_output(self, tmp_path):
        with patch("mediacrush.core.safety.MediaProbe.inspect", return_value=None):
            ok, msg = SafetyManager.verify_transcode(make_meta(), self._stage(tmp_path))
        assert not ok and "corruption" in msg

    def test_duration_mismatch(self, tmp_path):
        out = make_meta(duration=1000.0)
        with patch("mediacrush.core.safety.MediaProbe.inspect", return_value=out):
            ok, msg = SafetyManager.verify_transcode(make_meta(duration=1400.0), self._stage(tmp_path))
        assert not ok and "Duration" in msg

    def test_duration_within_tolerance(self, tmp_path):
        out = make_meta(duration=1401.4)
        with patch("mediacrush.core.safety.MediaProbe.inspect", return_value=out):
            ok, _ = SafetyManager.verify_transcode(make_meta(duration=1400.0), self._stage(tmp_path))
        assert ok

    def test_audio_lost(self, tmp_path):
        out = make_meta(audio=0)
        with patch("mediacrush.core.safety.MediaProbe.inspect", return_value=out):
            ok, msg = SafetyManager.verify_transcode(make_meta(audio=1), self._stage(tmp_path))
        assert not ok and "Audio" in msg

    def test_silent_source_without_audio_ok(self, tmp_path):
        with patch("mediacrush.core.safety.MediaProbe.inspect", return_value=make_meta(audio=0)):
            ok, _ = SafetyManager.verify_transcode(make_meta(audio=0), self._stage(tmp_path))
        assert ok
