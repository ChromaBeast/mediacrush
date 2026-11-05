"""Unit tests for content classifier and PPM analysis."""

import tempfile
import unittest
from pathlib import Path
from mediacrush.core.content_classifier import ContentClassifier, ContentType


class TestContentClassifier(unittest.TestCase):

    def test_enum_values(self):
        """Verifies enum preset mappings."""
        self.assertEqual(ContentType.ANIME.value, "anime")
        self.assertEqual(ContentType.LIVE_ACTION.value, "film")
        self.assertEqual(ContentType.UNKNOWN.value, "unknown")
        self.assertEqual(ContentType.UNKNOWN.preset_key, "film")

    def test_analyze_frame_ppm_flat_colors(self):
        """Synthetic PPM with flat colors should have low unique color ratio."""
        with tempfile.NamedTemporaryFile(suffix=".ppm", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            # Write a 10x10 binary P6 PPM with a single solid red color
            header = b"P6\n10 10\n255\n"
            pixels = b"\xff\x00\x00" * 100
            tmp.write(header + pixels)

        try:
            ratio = ContentClassifier._analyze_frame_ppm(tmp_path)
            self.assertIsNotNone(ratio)
            # Only 1 unique color in 4096 palette -> 1/4096 ~= 0.000244
            self.assertLess(ratio, 0.01)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()


if __name__ == "__main__":
    unittest.main()
