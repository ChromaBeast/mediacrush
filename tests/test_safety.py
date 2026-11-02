"""Unit tests for SafetyManager staging, output path, cleanup, and verify."""

import unittest
from pathlib import Path
from unittest.mock import patch
from mediacrush.core.safety import SafetyManager
from mediacrush.core.probe import MediaMetadata, StreamInfo


def make_source_meta(path: str = "/videos/movie.mkv", duration: float = 3600.0) -> MediaMetadata:
    return MediaMetadata(
        path=Path(path),
        duration_seconds=duration,
        file_size_bytes=500 * 1024 * 1024,
        video_codec="h264",
        width=1920,
        height=1080,
        fps=24.0,
        video_bitrate=8_000_000,
        overall_bitrate=8_200_000,
        audio_streams=[StreamInfo(1, "audio", "aac", "en", None, 2)],
        subtitle_streams=[],
    )


class TestStagingPath(unittest.TestCase):

    def test_staging_path_suffix(self):
        """get_staging_path must end with .mediacrush.temp.mkv."""
        source = Path("/videos/movie.mkv")
        staging = SafetyManager.get_staging_path(source)
        self.assertTrue(str(staging).endswith(".mediacrush.temp.mkv"))

    def test_staging_path_same_dir(self):
        """Staging file should be in the same folder as source."""
        source = Path("/videos/sub/movie.mkv")
        staging = SafetyManager.get_staging_path(source)
        self.assertEqual(staging.parent, source.parent)


class TestOutputPath(unittest.TestCase):

    def test_in_place_returns_original(self):
        """In-place mode must return the original file path."""
        source = Path("/videos/movie.mkv")
        out = SafetyManager.get_output_path(source, in_place=True)
        self.assertEqual(out, source)

    def test_side_by_side_crushed_suffix(self):
        """Side-by-side mode must return a .crushed.mkv path."""
        source = Path("/videos/movie.mkv")
        out = SafetyManager.get_output_path(source, in_place=False)
        self.assertTrue(str(out).endswith(".crushed.mkv"))
        self.assertNotEqual(out, source)


class TestCleanupStaging(unittest.TestCase):

    def test_cleanup_nonexistent_no_raise(self):
        """cleanup_staging on non-existent path must not raise."""
        try:
            SafetyManager.cleanup_staging(Path("/nonexistent/path/file.temp.mkv"))
        except Exception as exc:
            self.fail(f"cleanup_staging raised unexpectedly: {exc}")


class TestVerifyTranscode(unittest.TestCase):

    def test_verify_missing_staging_file(self):
        """verify_transcode returns (False, ...) when staging file doesn't exist."""
        source_meta = make_source_meta()
        staging = Path("/nonexistent/staging.mediacrush.temp.mkv")
        ok, msg = SafetyManager.verify_transcode(source_meta, staging)
        self.assertFalse(ok)
        self.assertIsInstance(msg, str)

    def test_verify_good_output(self):
        """verify_transcode returns (True, ...) when MediaProbe returns matching metadata."""
        source_meta = make_source_meta(duration=3600.0)
        staging = Path("/fake/staging.mkv")
        good_meta = make_source_meta(path="/fake/staging.mkv", duration=3600.0)

        with patch("mediacrush.core.safety.MediaProbe.inspect", return_value=good_meta):
            with patch.object(Path, "exists", return_value=True):
                with patch.object(Path, "stat") as mock_stat:
                    mock_stat.return_value.st_size = 50 * 1024 * 1024
                    ok, msg = SafetyManager.verify_transcode(source_meta, staging)
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
