"""Unit tests for metadata probe and candidate detection."""

from pathlib import Path
import unittest
from mediacrush.core.probe import MediaProbe, MediaMetadata
from mediacrush.core.scanner import LibraryScanner


class TestMediaProbe(unittest.TestCase):

    def test_nonexistent_file(self):
        """Ensures probing a non-existent file returns None without throwing."""
        res = MediaProbe.inspect(Path("C:/nonexistent/file.mkv"))
        self.assertIsNone(res)

    def test_skip_logic_hevc(self):
        """Ensures low bitrate HEVC files are skipped to avoid redundant work."""
        mock_meta = MediaMetadata(
            path=Path("mock.mkv"),
            duration_seconds=1400.0,
            file_size_bytes=300 * 1024 * 1024,
            video_codec="hevc",
            width=1920,
            height=1080,
            fps=23.976,
            video_bitrate=1_800_000,
            overall_bitrate=2_000_000
        )
        skip, reason = LibraryScanner.should_skip(mock_meta)
        self.assertTrue(skip)
        self.assertIn("Already efficient", reason)

    def test_skip_logic_bloated_h264(self):
        """Ensures high bitrate H.264 files are flagged as candidates."""
        mock_meta = MediaMetadata(
            path=Path("bloated.mkv"),
            duration_seconds=1430.0,
            file_size_bytes=1800 * 1024 * 1024,
            video_codec="h264",
            width=1920,
            height=1080,
            fps=23.976,
            video_bitrate=9_900_000,
            overall_bitrate=10_100_000
        )
        skip, reason = LibraryScanner.should_skip(mock_meta)
        self.assertFalse(skip)
        self.assertIn("Candidate", reason)


if __name__ == "__main__":
    unittest.main()
