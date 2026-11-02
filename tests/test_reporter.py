"""Unit tests for CompressionReporter HTML and JSON generation."""

import json
import tempfile
import unittest
from pathlib import Path
from mediacrush.core.reporter import CompressionReporter, ReportEntry


class TestCompressionReporter(unittest.TestCase):

    def test_savings_pct(self):
        """Calculates accurate savings percentage."""
        entry = ReportEntry("test.mkv", 1000, 400, "hevc_nvenc", 12.5, True)
        self.assertAlmostEqual(entry.savings_pct, 60.0)

    def test_write_json(self):
        """Verifies JSON report export."""
        rep = CompressionReporter()
        rep.add_result("ep01.mkv", 1_000_000_000, 400_000_000, "hevc_nvenc", 45.0, True)

        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "report.json"
            rep.write_json(out)
            self.assertTrue(out.exists())
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["file"], "ep01.mkv")

    def test_write_html(self):
        """Verifies HTML report export contains expected table elements."""
        rep = CompressionReporter()
        rep.add_result("movie.mkv", 2_000_000_000, 800_000_000, "libx265", 120.0, True)

        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "report.html"
            rep.write_html(out)
            self.assertTrue(out.exists())
            content = out.read_text(encoding="utf-8")
            self.assertIn("MediaCrush Compression Report", content)
            self.assertIn("movie.mkv", content)
            self.assertIn("Total saved:", content)


if __name__ == "__main__":
    unittest.main()
