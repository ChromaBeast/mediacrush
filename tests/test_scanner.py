"""Unit tests for LibraryScanner.should_skip and estimate_savings."""

import unittest
from pathlib import Path
from mediacrush.core.probe import MediaMetadata, StreamInfo
from mediacrush.core.scanner import LibraryScanner


def make_meta(
    codec: str,
    width: int,
    height: int,
    bitrate_mbps: float,
    file_size_mb: float = 500,
    duration_s: float = 3600,
    audio_streams=None,
) -> MediaMetadata:
    """Helper to create mock MediaMetadata without touching disk or FFmpeg."""
    bps = int(bitrate_mbps * 1_000_000)
    return MediaMetadata(
        path=Path("/fake/video.mkv"),
        duration_seconds=duration_s,
        file_size_bytes=int(file_size_mb * 1024 * 1024),
        video_codec=codec,
        width=width,
        height=height,
        fps=24.0,
        video_bitrate=bps,
        overall_bitrate=bps + 192_000,
        audio_streams=audio_streams or [],
        subtitle_streams=[],
    )


class TestShouldSkip(unittest.TestCase):

    def test_hevc_1080p_efficient_skip(self):
        """HEVC 1080p below 4.2 Mbps → skip."""
        meta = make_meta("hevc", 1920, 1080, 3.0)
        skip, reason = LibraryScanner.should_skip(meta)
        self.assertTrue(skip)
        self.assertIn("efficient", reason.lower())

    def test_hevc_4k_efficient_skip(self):
        """HEVC 4K below 15 Mbps → skip."""
        meta = make_meta("hevc", 3840, 2160, 8.0)
        skip, reason = LibraryScanner.should_skip(meta)
        self.assertTrue(skip)
        self.assertIn("efficient", reason.lower())

    def test_hevc_720p_efficient_skip(self):
        """HEVC 720p below 2.2 Mbps → skip."""
        meta = make_meta("hevc", 1280, 720, 1.5)
        skip, reason = LibraryScanner.should_skip(meta)
        self.assertTrue(skip)
        self.assertIn("efficient", reason.lower())

    def test_h264_bloated_candidate(self):
        """H.264 1080p at 8 Mbps → candidate for compression."""
        meta = make_meta("h264", 1920, 1080, 8.0)
        skip, _ = LibraryScanner.should_skip(meta)
        self.assertFalse(skip)

    def test_tiny_file_skip(self):
        """File under 40 MB → skip regardless of codec."""
        meta = make_meta("h264", 1920, 1080, 8.0, file_size_mb=10)
        skip, reason = LibraryScanner.should_skip(meta)
        self.assertTrue(skip)
        self.assertIn("40MB", reason)


class TestEstimateSavings(unittest.TestCase):

    def test_savings_capped_above_20_percent(self):
        """estimate_savings result should be >= 20% of original size."""
        meta = make_meta("h264", 1920, 1080, 30.0, file_size_mb=5000, duration_s=60)
        est = LibraryScanner.estimate_savings(meta)
        min_size = int(meta.file_size_bytes * 0.20)
        self.assertGreaterEqual(est, min_size)

    def test_savings_capped_below_75_percent(self):
        """estimate_savings result should be <= 75% of original size."""
        meta = make_meta("h264", 1920, 1080, 1.0, file_size_mb=1000, duration_s=10)
        est = LibraryScanner.estimate_savings(meta)
        max_size = int(meta.file_size_bytes * 0.75)
        self.assertLessEqual(est, max_size)

    def test_savings_returns_int(self):
        """estimate_savings should return an integer."""
        meta = make_meta("h264", 1920, 1080, 8.0)
        est = LibraryScanner.estimate_savings(meta)
        self.assertIsInstance(est, int)


if __name__ == "__main__":
    unittest.main()
