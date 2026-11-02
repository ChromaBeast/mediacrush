"""Unit tests for hardware encoder discovery."""

import shutil
import unittest
from unittest.mock import patch
from mediacrush.core.hardware import HardwareDetector, EncoderInfo


class TestHardwareDetector(unittest.TestCase):

    def test_candidates_not_empty(self):
        """Ensures hardware candidates matrix has valid presets."""
        self.assertGreater(len(HardwareDetector.PROBE_CANDIDATES), 3)

    def test_encoder_discovery(self):
        """Tests that at least one encoder is functional on the system if FFmpeg is installed."""
        if not shutil.which("ffmpeg"):
            self.skipTest("FFmpeg is not installed on this environment")
        encoders = HardwareDetector.discover_encoders()
        self.assertTrue(len(encoders) > 0, "No working encoders found")

    def test_encoder_discovery_mocked(self):
        """Tests discovery logic when encoders return valid."""
        with patch.object(HardwareDetector, "test_encoder", return_value=True):
            encoders = HardwareDetector.discover_encoders()
            self.assertEqual(len(encoders), len(HardwareDetector.PROBE_CANDIDATES))

    def test_get_best_encoder(self):
        """Verifies that the preferred encoder is selected cleanly."""
        best = HardwareDetector.get_best_encoder()
        self.assertIsInstance(best, EncoderInfo)
        self.assertIsNotNone(best.encoder_name)


if __name__ == "__main__":
    unittest.main()
