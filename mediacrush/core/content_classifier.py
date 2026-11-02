"""Automatic media content classification (Animation vs Live-Action)."""

from enum import Enum
from pathlib import Path
import subprocess
import tempfile
from typing import Set, Tuple


class ContentType(str, Enum):
    """Categorized content types for preset auto-selection."""
    ANIME = "anime"
    LIVE_ACTION = "film"
    UNKNOWN = "film"


class ContentClassifier:
    """Analyzes visual characteristics to determine whether video is animation or live-action."""

    @classmethod
    def detect(cls, path: Path, sample_count: int = 4) -> ContentType:
        """Samples frames and evaluates color uniformity characteristic of 2D animation."""
        if not path.exists():
            return ContentType.UNKNOWN

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir)
                # Extract a few representative frames scaled down to 320x180 PPM
                out_pattern = str(tmp_path / "frame_%02d.ppm")
                cmd = [
                    "ffmpeg", "-y", "-v", "error",
                    "-skip_frame", "nokey",
                    "-i", str(path),
                    "-vf", "scale=320:180",
                    "-vframes", str(sample_count),
                    out_pattern
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)

                ppm_files = list(tmp_path.glob("*.ppm"))
                if not ppm_files:
                    return ContentType.UNKNOWN

                ratios = []
                for p in ppm_files:
                    ratio = cls._analyze_frame_ppm(p)
                    if ratio is not None:
                        ratios.append(ratio)

                if not ratios:
                    return ContentType.UNKNOWN

                avg_ratio = sum(ratios) / len(ratios)
                # Anime typically has high color re-use (quantized ratio < 0.18)
                if avg_ratio < 0.18:
                    return ContentType.ANIME
                return ContentType.LIVE_ACTION

        except Exception:
            return ContentType.UNKNOWN

    @staticmethod
    def _analyze_frame_ppm(ppm_path: Path) -> float | None:
        """Parses a P6 binary PPM image and returns unique 12-bit color ratio."""
        try:
            with open(ppm_path, "rb") as f:
                header = f.readline().strip()
                if header != b"P6":
                    return None
                line = f.readline()
                while line.startswith(b"#"):
                    line = f.readline()
                w, h = map(int, line.split())
                max_val = int(f.readline().strip())
                if max_val != 255:
                    return None
                raw_data = f.read()

            total_pixels = w * h
            if total_pixels == 0 or len(raw_data) < total_pixels * 3:
                return None

            # Quantize colors to 4 bits per channel (12-bit palette: 4096 possible colors)
            unique_colors: Set[int] = set()
            for i in range(0, total_pixels * 3, 3):
                r = raw_data[i] >> 4
                g = raw_data[i + 1] >> 4
                b = raw_data[i + 2] >> 4
                unique_colors.add((r << 8) | (g << 4) | b)

            return len(unique_colors) / 4096.0
        except Exception:
            return None
