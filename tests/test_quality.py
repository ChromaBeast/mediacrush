"""Unit tests for QualityChecker verdict evaluation."""

import unittest
from mediacrush.core.quality import QualityChecker, QualityScore


class TestQualityChecker(unittest.TestCase):

    def test_verdict_thresholds(self):
        """Verifies VMAF threshold bands map to appropriate quality verdicts."""
        self.assertEqual(QualityChecker._calculate_verdict(95.0), "Excellent")
        self.assertEqual(QualityChecker._calculate_verdict(92.0), "Excellent")
        self.assertEqual(QualityChecker._calculate_verdict(85.0), "Good")
        self.assertEqual(QualityChecker._calculate_verdict(80.0), "Good")
        self.assertEqual(QualityChecker._calculate_verdict(70.0), "Acceptable")
        self.assertEqual(QualityChecker._calculate_verdict(65.0), "Acceptable")
        self.assertEqual(QualityChecker._calculate_verdict(50.0), "Poor")

    def test_quality_score_dataclass(self):
        """QualityScore fields initialized properly."""
        score = QualityScore(vmaf=94.5, ssim=0.9912, verdict="Excellent")
        self.assertEqual(score.vmaf, 94.5)
        self.assertEqual(score.ssim, 0.9912)
        self.assertEqual(score.verdict, "Excellent")


if __name__ == "__main__":
    unittest.main()
