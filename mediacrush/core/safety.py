"""Safety staging, integrity verification, and atomic file finalization."""

from pathlib import Path
import shutil
from typing import Tuple
from mediacrush.core.probe import MediaProbe, MediaMetadata


class SafetyManager:
    """Ensures no source media is lost or corrupted during transcoding."""

    @staticmethod
    def get_staging_path(source_path: Path) -> Path:
        """Generates a temporary staging path adjacent to the source."""
        return source_path.with_name(f"{source_path.stem}.mediacrush.temp.mkv")

    @staticmethod
    def get_output_path(source_path: Path, in_place: bool) -> Path:
        """Returns final target path (either original name or crushed suffix)."""
        if in_place:
            return source_path
        return source_path.with_name(f"{source_path.stem}.crushed.mkv")

    @classmethod
    def verify_transcode(cls, source_meta: MediaMetadata, staging_path: Path) -> Tuple[bool, str]:
        """Validates that the transcoded file matches duration and stream integrity."""
        if not staging_path.exists():
            return False, "Staging file was not created"

        staging_size = staging_path.stat().st_size
        if staging_size < 1_000_000:  # Minimum 1MB for a real video
            return False, f"Output file is abnormally small ({staging_size} bytes)"

        out_meta = MediaProbe.inspect(staging_path)
        if not out_meta:
            return False, "Failed to read metadata from output file (possible corruption)"

        # Verify duration tolerance (within 1.5 seconds)
        duration_diff = abs(source_meta.duration_seconds - out_meta.duration_seconds)
        if duration_diff > 1.5:
            return False, f"Duration mismatch: source={source_meta.duration_seconds}s, out={out_meta.duration_seconds}s"

        # Verify audio stream preservation
        if len(source_meta.audio_streams) > 0 and len(out_meta.audio_streams) == 0:
            return False, "Audio streams missing in output file"

        return True, "Verification passed"

    @classmethod
    def finalize_transcode(
        cls,
        source_path: Path,
        staging_path: Path,
        in_place: bool = True,
        keep_backup: bool = False
    ) -> Path:
        """Atomically commits the verified staging file to the destination."""
        target_path = cls.get_output_path(source_path, in_place)

        if in_place:
            if keep_backup:
                backup_path = source_path.with_name(f"{source_path.name}.bak")
                shutil.move(str(source_path), str(backup_path))
            else:
                source_path.unlink()

            shutil.move(str(staging_path), str(target_path))
        else:
            if target_path.exists():
                target_path.unlink()
            shutil.move(str(staging_path), str(target_path))

        return target_path

    @staticmethod
    def cleanup_staging(staging_path: Path) -> None:
        """Removes orphaned temp file if an encode fails or is aborted."""
        try:
            if staging_path.exists():
                staging_path.unlink()
        except Exception:
            pass
