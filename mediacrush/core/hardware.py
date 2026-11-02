"""Hardware detection and encoder discovery for GPU and CPU backends."""

from dataclasses import dataclass
import subprocess
from typing import List, Optional


@dataclass
class EncoderInfo:
    """Represents a validated encoder and its backend vendor."""
    codec: str
    encoder_name: str
    vendor: str
    hwaccel: Optional[str]
    description: str


class HardwareDetector:
    """Probes host hardware and discovers functional video encoders."""

    PROBE_CANDIDATES = [
        # Apple VideoToolbox (Apple Silicon M1-M4 & Intel Macs)
        EncoderInfo("hevc", "hevc_videotoolbox", "Apple", "videotoolbox", "Apple VideoToolbox H.265 (Apple Silicon & Intel Mac)"),
        EncoderInfo("av1", "av1_videotoolbox", "Apple", "videotoolbox", "Apple VideoToolbox AV1 (Apple Silicon)"),
        EncoderInfo("h264", "h264_videotoolbox", "Apple", "videotoolbox", "Apple VideoToolbox H.264 (Intel Mac Hardware)"),
        # NVIDIA NVENC (Windows & Linux)
        EncoderInfo("hevc", "hevc_nvenc", "NVIDIA", "cuda", "NVIDIA NVENC H.265 (Fastest)"),
        EncoderInfo("av1", "av1_nvenc", "NVIDIA", "cuda", "NVIDIA NVENC AV1"),
        # AMD AMF (Windows)
        EncoderInfo("hevc", "hevc_amf", "AMD", "d3d11va", "AMD AMF H.265"),
        EncoderInfo("av1", "av1_amf", "AMD", "d3d11va", "AMD AMF AV1"),
        # Intel QuickSync (Windows & Linux)
        EncoderInfo("hevc", "hevc_qsv", "Intel", "qsv", "Intel QuickSync H.265"),
        EncoderInfo("av1", "av1_qsv", "Intel", "qsv", "Intel QuickSync AV1"),
        # Linux VAAPI (AMD Radeon & Intel on Linux)
        EncoderInfo("hevc", "hevc_vaapi", "Linux/VAAPI", "vaapi", "Linux VAAPI H.265 (Hardware)"),
        EncoderInfo("av1", "av1_vaapi", "Linux/VAAPI", "vaapi", "Linux VAAPI AV1"),
        # Snapdragon X Elite / Plus & Windows Media Foundation
        EncoderInfo("hevc", "hevc_mf", "Qualcomm/Windows", "d3d11va", "Windows Media Foundation (Snapdragon / D3D11)"),
        EncoderInfo("av1", "av1_mf", "Qualcomm/Windows", "d3d11va", "Windows Media Foundation AV1"),
        # High efficiency CPU Fallbacks (Universal)
        EncoderInfo("hevc", "libx265", "CPU", None, "CPU x265 (High Efficiency)"),
        EncoderInfo("av1", "libsvtav1", "CPU", None, "CPU SVT-AV1 (High Efficiency)"),
        EncoderInfo("h264", "libx264", "CPU", None, "CPU x264"),
    ]

    @classmethod
    def test_encoder(cls, candidate: EncoderInfo) -> bool:
        """Runs a 1-frame dummy transcode to verify hardware support."""
        cmd = [
            "ffmpeg", "-y", "-v", "error",
            "-f", "lavfi", "-i", "color=c=black:s=256x256:d=0.04",
            "-frames:v", "1"
        ]
        if candidate.encoder_name in {"hevc_vaapi", "av1_vaapi"}:
            cmd.extend(["-vaapi_device", "/dev/dri/renderD128", "-vf", "format=nv12,hwupload"])
        cmd.extend(["-c:v", candidate.encoder_name, "-f", "null", "-"])
        try:
            res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=4)
            return res.returncode == 0
        except Exception:
            return False

    @classmethod
    def discover_encoders(cls) -> List[EncoderInfo]:
        """Returns all working encoders verified on this machine."""
        available = []
        for candidate in cls.PROBE_CANDIDATES:
            if cls.test_encoder(candidate):
                available.append(candidate)
        return available

    @classmethod
    def get_best_encoder(cls, preferred_codec: str = "hevc") -> EncoderInfo:
        """Selects the best available encoder for the requested codec."""
        available = cls.discover_encoders()
        # Prefer matching codec
        matching = [e for e in available if e.codec == preferred_codec]
        if matching:
            # First matching is highest priority in candidate list
            return matching[0]
        # Fallback to any working encoder
        return available[0] if available else EncoderInfo("hevc", "libx265", "CPU", None, "CPU Fallback")
