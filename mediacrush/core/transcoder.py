"""FFmpeg execution and real-time transcode progress parsing."""

from dataclasses import dataclass
import re
import subprocess
from typing import Callable, Optional
from mediacrush.core.hardware import EncoderInfo
from mediacrush.core.presets import PresetManager
from mediacrush.core.probe import MediaMetadata
from mediacrush.core.safety import SafetyManager


@dataclass
class TranscodeProgress:
    """Snapshot of active transcoding progress."""
    percent: float
    fps: float
    speed_multiplier: float
    current_time_seconds: float
    total_time_seconds: float
    eta_seconds: float


class TranscodeEngine:
    """Executes FFmpeg with hardware acceleration and parses live progress."""

    TIME_REGEX = re.compile(r"time=(\d+):(\d+):(\d+\.\d+)")
    FPS_REGEX = re.compile(r"fps=\s*(\d+(?:\.\d+)?)")
    SPEED_REGEX = re.compile(r"speed=\s*(\d+(?:\.\d+)?)x")

    def __init__(self):
        self._current_process: Optional[subprocess.Popen] = None
        self._is_cancelled = False

    def cancel(self):
        """Terminates active transcode process."""
        self._is_cancelled = True
        if self._current_process:
            self._current_process.terminate()

    def transcode(
        self,
        meta: MediaMetadata,
        encoder: EncoderInfo,
        preset_key: str = "anime",
        in_place: bool = True,
        keep_backup: bool = False,
        progress_callback: Optional[Callable[[TranscodeProgress], None]] = None
    ) -> bool:
        """Encodes media file using staging and verified atomic replacement."""
        self._is_cancelled = False
        staging = SafetyManager.get_staging_path(meta.path)
        SafetyManager.cleanup_staging(staging)

        # Assemble FFmpeg arguments
        encoder_args = PresetManager.build_ffmpeg_args(encoder, preset_key, meta=meta)
        cmd = ["ffmpeg", "-y"]
        if encoder.hwaccel and encoder.encoder_name not in {"hevc_vaapi", "av1_vaapi"}:
            cmd.extend(["-hwaccel", "auto"])
        cmd.extend(["-i", str(meta.path)])
        cmd.extend(encoder_args)
        cmd.append(str(staging))

        try:
            self._current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1
            )

            total_duration = max(1.0, meta.duration_seconds)
            for line in self._current_process.stdout:
                if self._is_cancelled:
                    break

                t_match = self.TIME_REGEX.search(line)
                if t_match and progress_callback:
                    h, m, s = t_match.groups()
                    curr_secs = int(h) * 3600 + int(m) * 60 + float(s)
                    pct = min(100.0, (curr_secs / total_duration) * 100)

                    fps_match = self.FPS_REGEX.search(line)
                    fps = float(fps_match.group(1)) if fps_match else 0.0

                    spd_match = self.SPEED_REGEX.search(line)
                    spd = float(spd_match.group(1)) if spd_match else 1.0

                    rem_secs = max(0.0, (total_duration - curr_secs) / max(0.1, spd))
                    progress_callback(TranscodeProgress(pct, fps, spd, curr_secs, total_duration, rem_secs))

            self._current_process.wait()
            ret_code = self._current_process.returncode

            if self._is_cancelled or ret_code != 0:
                SafetyManager.cleanup_staging(staging)
                return False

            # Verify integrity
            valid, reason = SafetyManager.verify_transcode(meta, staging)
            if not valid:
                SafetyManager.cleanup_staging(staging)
                return False

            # Atomically finalize
            SafetyManager.finalize_transcode(meta.path, staging, in_place, keep_backup)
            return True

        except Exception:
            SafetyManager.cleanup_staging(staging)
            return False
        finally:
            self._current_process = None
