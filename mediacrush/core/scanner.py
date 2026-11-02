"""Recursive library scanner with smart bloat detection and skip logic."""

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from mediacrush.core.probe import MediaMetadata, MediaProbe


@dataclass
class CandidateFile:
    """A file identified for optimization along with estimated savings."""
    metadata: MediaMetadata
    reason: str
    estimated_size_bytes: int
    potential_savings_bytes: int
    local_preset: Optional[str] = None

    @property
    def savings_percent(self) -> float:
        """Returns savings as a percentage."""
        if self.metadata.file_size_bytes == 0:
            return 0.0
        return (self.potential_savings_bytes / self.metadata.file_size_bytes) * 100


@dataclass
class ScanReport:
    """Summary of a scanned folder tree."""
    root_path: Path
    candidates: List[CandidateFile]
    skipped_count: int
    total_current_bytes: int
    total_estimated_bytes: int
    local_configs: Dict[str, dict] = field(default_factory=dict)

    @property
    def total_savings_bytes(self) -> int:
        return max(0, self.total_current_bytes - self.total_estimated_bytes)


class LibraryScanner:
    """Traverses folder structures and evaluates optimization candidates."""

    SUPPORTED_EXTS = {".mkv", ".mp4", ".avi", ".mov", ".m4v", ".webm", ".ts"}
    CONFIG_NAME = ".mediacrush.json"

    @classmethod
    def load_folder_config(cls, folder: Path) -> dict:
        """Loads optional per-folder .mediacrush.json configuration."""
        cfg_path = folder / cls.CONFIG_NAME
        if cfg_path.is_file():
            try:
                return json.loads(cfg_path.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    @classmethod
    def should_skip(cls, meta: MediaMetadata, skip_already_hevc: bool = True) -> Tuple[bool, str]:
        """Determines if a file is already sufficiently compressed."""
        codec = meta.video_codec.lower()
        br_mbps = (meta.video_bitrate or meta.overall_bitrate) / 1_000_000

        # Modern codecs already compressed reasonably
        if skip_already_hevc and codec in {"hevc", "h265", "av1"}:
            if meta.resolution_label == "4K" and br_mbps < 15.0:
                return True, "Already efficient 4K HEVC/AV1"
            if meta.resolution_label == "1080p" and br_mbps < 4.2:
                return True, "Already efficient 1080p HEVC/AV1"
            if meta.resolution_label == "720p" and br_mbps < 2.2:
                return True, "Already efficient 720p HEVC/AV1"

        # Tiny files under 40 MB usually don't need recompression
        if meta.file_size_bytes < 40 * 1024 * 1024:
            return True, "File under 40MB"

        return False, "Candidate for compression"

    @classmethod
    def estimate_savings(cls, meta: MediaMetadata) -> int:
        """Estimates target file size based on resolution and duration."""
        # For anime/web video: 1080p HEVC ~2.2-2.8 Mbps, 720p ~1.2 Mbps, 4K ~8-10 Mbps
        res = meta.resolution_label
        target_bps = 2_500_000 if res == "1080p" else (1_200_000 if res == "720p" else 8_500_000)
        audio_overhead = 192_000 * max(1, len(meta.audio_streams))
        total_target_bps = target_bps + audio_overhead

        est_bytes = int((total_target_bps / 8) * meta.duration_seconds)
        # Cap estimation between 20% and 75% of original
        min_size = int(meta.file_size_bytes * 0.20)
        max_size = int(meta.file_size_bytes * 0.70)
        return max(min_size, min(est_bytes, max_size))

    @classmethod
    def scan_path(cls, path: Path) -> ScanReport:
        """Recursively scans directory tree or single file for candidates."""
        target = Path(path)
        files_to_check: List[Path] = []

        if target.is_file() and target.suffix.lower() in cls.SUPPORTED_EXTS:
            files_to_check.append(target)
        elif target.is_dir():
            for p in target.rglob("*"):
                if p.is_file() and p.suffix.lower() in cls.SUPPORTED_EXTS:
                    files_to_check.append(p)

        candidates: List[CandidateFile] = []
        folder_configs: Dict[str, dict] = {}
        skipped = 0
        total_curr = 0
        total_est = 0

        for f in files_to_check:
            folder_key = str(f.parent)
            if folder_key not in folder_configs:
                folder_configs[folder_key] = cls.load_folder_config(f.parent)
            local_cfg = folder_configs[folder_key]

            meta = MediaProbe.inspect(f)
            if not meta:
                continue

            skip_hevc = local_cfg.get("skip_already_hevc", True)
            skip, reason = cls.should_skip(meta, skip_already_hevc=skip_hevc)
            if skip:
                skipped += 1
                continue

            est_size = cls.estimate_savings(meta)
            savings = max(0, meta.file_size_bytes - est_size)
            preset_override = local_cfg.get("preset")
            candidates.append(CandidateFile(meta, reason, est_size, savings, preset_override))
            total_curr += meta.file_size_bytes
            total_est += est_size

        return ScanReport(target, candidates, skipped, total_curr, total_est, folder_configs)
