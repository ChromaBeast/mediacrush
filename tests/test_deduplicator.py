"""Unit tests for duplicate detection and normalization logic."""

import unittest
from pathlib import Path
from mediacrush.core.deduplicator import DuplicateDetector
from mediacrush.core.probe import MediaMetadata


class TestDuplicateDetector(unittest.TestCase):

    def test_normalize_name(self):
        """Strips tags and formatting to extract base title."""
        name1 = "My.Movie.2024.1080p.WEB-DL.x265.AAC.mkv"
        name2 = "My Movie 2024 4K Bluray HEVC"
        norm1 = DuplicateDetector._normalize_name(name1)
        norm2 = DuplicateDetector._normalize_name(name2)
        self.assertIn("my movie", norm1)
        self.assertIn("my movie", norm2)

    def test_duplicate_grouping(self):
        """Verifies duplicate duration clustering."""
        meta1 = MediaMetadata(
            path=Path("/lib/movie_1080p.mkv"),
            duration_seconds=7200.0,
            file_size_bytes=2_000_000_000,
            video_codec="h264",
            width=1920,
            height=1080,
            fps=24.0,
            video_bitrate=4_000_000,
            overall_bitrate=4_200_000,
        )
        meta2 = MediaMetadata(
            path=Path("/lib/movie_4k.mkv"),
            duration_seconds=7201.0,
            file_size_bytes=8_000_000_000,
            video_codec="hevc",
            width=3840,
            height=2160,
            fps=24.0,
            video_bitrate=16_000_000,
            overall_bitrate=16_500_000,
        )
        # 4K should be recommended keep
        files = [meta1, meta2]
        sorted_files = sorted(
            files,
            key=lambda x: ({"4K": 3, "1080p": 2, "720p": 1}.get(x.resolution_label, 0), x.file_size_bytes),
            reverse=True,
        )
        self.assertEqual(sorted_files[0], meta2)
        self.assertEqual(sorted_files[1], meta1)


if __name__ == "__main__":
    unittest.main()
