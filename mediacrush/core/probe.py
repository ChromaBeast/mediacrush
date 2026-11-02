"""ffprobe wrapper to extract media metadata safely."""

from dataclasses import dataclass, field
import json
from pathlib import Path
import subprocess
from typing import List, Optional


@dataclass
class StreamInfo:
    """Represents an individual audio, video, or subtitle stream."""
    index: int
    codec_type: str
    codec_name: str
    language: Optional[str] = None
    title: Optional[str] = None
    channels: Optional[int] = None
    bitrate: Optional[int] = None


@dataclass
class MediaMetadata:
    """Structured media information extracted from a video container."""
    path: Path
    duration_seconds: float
    file_size_bytes: int
    video_codec: str
    width: int
    height: int
    fps: float
    video_bitrate: int
    overall_bitrate: int
    audio_streams: List[StreamInfo] = field(default_factory=list)
    subtitle_streams: List[StreamInfo] = field(default_factory=list)

    @property
    def resolution_label(self) -> str:
        """Returns standard label (e.g. 1080p, 4K, 720p)."""
        if self.width >= 3800 or self.height >= 2100:
            return "4K"
        if self.width >= 1900 or self.height >= 1000:
            return "1080p"
        if self.width >= 1200 or self.height >= 700:
            return "720p"
        return f"{self.width}x{self.height}"


class MediaProbe:
    """Executes ffprobe to extract full container and stream metadata."""

    @staticmethod
    def inspect(file_path: Path) -> Optional[MediaMetadata]:
        """Probes file with ffprobe and returns structured MediaMetadata."""
        path_obj = Path(file_path)
        if not path_obj.exists() or path_obj.stat().st_size == 0:
            return None

        cmd = [
            "ffprobe", "-v", "error",
            "-show_format", "-show_streams",
            "-of", "json",
            str(path_obj)
        ]
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True,
                timeout=15
            )
            data = json.loads(res.stdout)
        except Exception:
            return None

        format_data = data.get("format", {})
        streams = data.get("streams", [])

        duration = float(format_data.get("duration", 0.0))
        file_size = int(format_data.get("size", path_obj.stat().st_size))
        overall_bitrate = int(format_data.get("bit_rate", 0))

        v_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
        video_codec = v_stream.get("codec_name", "unknown")
        width = int(v_stream.get("width", 0))
        height = int(v_stream.get("height", 0))

        # Bitrate can be in stream tags (e.g. BPS or bit_rate)
        v_tags = v_stream.get("tags", {})
        v_bps = v_stream.get("bit_rate") or v_tags.get("BPS") or v_tags.get("bps")
        video_bitrate = int(v_bps) if v_bps and str(v_bps).isdigit() else 0

        # Calculate FPS
        r_fps = v_stream.get("r_frame_rate", "24/1")
        try:
            num, den = map(int, r_fps.split("/"))
            fps = round(num / den, 3) if den != 0 else 24.0
        except Exception:
            fps = 24.0

        audios: List[StreamInfo] = []
        subs: List[StreamInfo] = []
        for s in streams:
            c_type = s.get("codec_type")
            idx = int(s.get("index", 0))
            codec = s.get("codec_name", "")
            tags = s.get("tags", {})
            lang = tags.get("language")
            title = tags.get("title")

            if c_type == "audio":
                audios.append(StreamInfo(idx, c_type, codec, lang, title, s.get("channels")))
            elif c_type == "subtitle":
                subs.append(StreamInfo(idx, c_type, codec, lang, title))

        return MediaMetadata(
            path=path_obj,
            duration_seconds=duration,
            file_size_bytes=file_size,
            video_codec=video_codec,
            width=width,
            height=height,
            fps=fps,
            video_bitrate=video_bitrate,
            overall_bitrate=overall_bitrate,
            audio_streams=audios,
            subtitle_streams=subs
        )
