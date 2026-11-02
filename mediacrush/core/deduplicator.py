"""Duplicate video file identification and cleanup recommendation engine."""

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Dict, List
from mediacrush.core.probe import MediaMetadata, MediaProbe
from mediacrush.core.scanner import LibraryScanner


@dataclass
class DuplicateGroup:
    """A cluster of video files identified as duplicates of the same content."""
    files: List[MediaMetadata]
    recommended_keep: MediaMetadata
    removable_size_bytes: int


class DuplicateDetector:
    """Finds redundant copies of media across libraries based on duration and specs."""

    @classmethod
    def _normalize_name(cls, name: str) -> str:
        """Strips resolution tags, release groups, and years for grouping."""
        s = name.lower()
        s = re.sub(r"\b(1080p|720p|2160p|4k|x264|x265|hevc|web-dl|bluray|aac|ac3)\b", "", s)
        s = re.sub(r"[._\- ]+", " ", s).strip()
        return s

    @classmethod
    def find(cls, target_path: Path) -> List[DuplicateGroup]:
        """Scans path recursively and clusters duplicate media."""
        path = Path(target_path)
        files_to_check: List[Path] = []
        if path.is_file() and path.suffix.lower() in LibraryScanner.SUPPORTED_EXTS:
            files_to_check.append(path)
        elif path.is_dir():
            for p in path.rglob("*"):
                if p.is_file() and p.suffix.lower() in LibraryScanner.SUPPORTED_EXTS:
                    files_to_check.append(p)

        probed: List[MediaMetadata] = []
        for f in files_to_check:
            meta = MediaProbe.inspect(f)
            if meta and meta.duration_seconds > 10:
                probed.append(meta)

        # Bucket by duration bucket (rounded to nearest 4 seconds)
        duration_buckets: Dict[int, List[MediaMetadata]] = {}
        for m in probed:
            bucket_key = int(round(m.duration_seconds / 4.0)) * 4
            duration_buckets.setdefault(bucket_key, []).append(m)

        groups: List[DuplicateGroup] = []
        res_rank = {"4K": 3, "1080p": 2, "720p": 1}

        for _, bucket in duration_buckets.items():
            if len(bucket) < 2:
                continue

            # Within duration bucket, match if durations are within 3s
            cluster: List[MediaMetadata] = []
            for item in bucket:
                if not cluster:
                    cluster.append(item)
                else:
                    if abs(cluster[0].duration_seconds - item.duration_seconds) <= 3.0:
                        cluster.append(item)

            if len(cluster) >= 2:
                # Pick best: highest resolution rank, then largest file
                sorted_files = sorted(
                    cluster,
                    key=lambda x: (res_rank.get(x.resolution_label, 0), x.file_size_bytes),
                    reverse=True
                )
                keep = sorted_files[0]
                removable = sum(f.file_size_bytes for f in sorted_files[1:])
                groups.append(DuplicateGroup(sorted_files, keep, removable))

        return groups
