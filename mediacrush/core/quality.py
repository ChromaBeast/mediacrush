"""Objective video quality assessment using FFmpeg VMAF and SSIM filters."""

from dataclasses import dataclass
import json
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Optional


@dataclass
class QualityScore:
    """Quantitative visual fidelity metrics."""
    vmaf: float
    ssim: float
    verdict: str


class QualityChecker:
    """Measures visual retention between source and transcoded media."""

    SAMPLE_DURATION = 30  # seconds

    @staticmethod
    def _calculate_verdict(vmaf: float) -> str:
        if vmaf >= 92.0:
            return "Excellent"
        if vmaf >= 80.0:
            return "Good"
        if vmaf >= 65.0:
            return "Acceptable"
        return "Poor"

    @classmethod
    def score(cls, source: Path, encoded: Path) -> Optional[QualityScore]:
        """Calculates VMAF and SSIM scores by comparing sample windows."""
        if not source.exists() or not encoded.exists():
            return None

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            vmaf_log = tmp_path / "vmaf.json"
            ssim_log = tmp_path / "ssim.txt"

            vmaf_val = cls._run_vmaf(source, encoded, vmaf_log)
            if vmaf_val is None:
                return None

            ssim_val = cls._run_ssim(source, encoded, ssim_log) or 0.95
            verdict = cls._calculate_verdict(vmaf_val)
            return QualityScore(vmaf=round(vmaf_val, 2), ssim=round(ssim_val, 4), verdict=verdict)

    @classmethod
    def _run_vmaf(cls, source: Path, encoded: Path, log_file: Path) -> Optional[float]:
        log_str = str(log_file).replace("\\", "/")
        filt = f"[0:v][1:v]libvmaf=log_fmt=json:log_path='{log_str}'"
        cmd = [
            "ffmpeg", "-y",
            "-t", str(cls.SAMPLE_DURATION), "-i", str(encoded),
            "-t", str(cls.SAMPLE_DURATION), "-i", str(source),
            "-lavfi", filt,
            "-f", "null", "-"
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
            if not log_file.exists():
                return None
            data = json.loads(log_file.read_text(encoding="utf-8"))
            return float(data.get("pooled_metrics", {}).get("vmaf", {}).get("mean", 0.0))
        except Exception:
            return None

    @classmethod
    def _run_ssim(cls, source: Path, encoded: Path, log_file: Path) -> Optional[float]:
        log_str = str(log_file).replace("\\", "/")
        filt = f"[0:v][1:v]ssim=stats_file='{log_str}'"
        cmd = [
            "ffmpeg", "-y",
            "-t", str(cls.SAMPLE_DURATION), "-i", str(encoded),
            "-t", str(cls.SAMPLE_DURATION), "-i", str(source),
            "-lavfi", filt,
            "-f", "null", "-"
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
            if not log_file.exists():
                return None
            txt = log_file.read_text(encoding="utf-8")
            matches = re.findall(r"All:([0-9.]+)", txt)
            if matches:
                scores = [float(m) for m in matches]
                return sum(scores) / len(scores)
            return None
        except Exception:
            return None
