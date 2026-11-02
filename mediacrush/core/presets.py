"""Encoding presets and rate-control parameters for all hardware backends."""

from dataclasses import dataclass
from typing import Dict, List, Optional
from mediacrush.core.hardware import EncoderInfo
from mediacrush.core.probe import MediaMetadata


@dataclass
class Preset:
    """Preset settings providing specific rate-control arguments."""
    name: str
    description: str
    nvenc_cq: int
    cpu_crf: int
    tune_animation: bool


class PresetManager:
    """Configures visually lossless FFmpeg parameters per hardware encoder."""

    PRESETS: Dict[str, Preset] = {
        "anime": Preset(
            name="Anime / Animation",
            description="Visually lossless tuning for 2D animation and line art.",
            nvenc_cq=20,
            cpu_crf=19,
            tune_animation=True
        ),
        "film": Preset(
            name="Movies / Live Action",
            description="High fidelity preserving natural film grain and textures.",
            nvenc_cq=20,
            cpu_crf=20,
            tune_animation=False
        ),
        "saver": Preset(
            name="Ultra Space Saver",
            description="Aggressive size reduction while retaining good 1080p quality.",
            nvenc_cq=24,
            cpu_crf=23,
            tune_animation=False
        )
    }

    @classmethod
    def build_ffmpeg_args(
        cls,
        encoder: EncoderInfo,
        preset_key: str = "anime",
        meta: Optional[MediaMetadata] = None,
    ) -> List[str]:
        """Generates the optimal FFmpeg arguments for the selected encoder."""
        preset = cls.PRESETS.get(preset_key, cls.PRESETS["anime"])
        args: List[str] = ["-map", "0"]  # Include all video, audio, and subtitle streams

        # 1. Video encoder options
        args.extend(["-c:v", encoder.encoder_name])

        if encoder.encoder_name == "hevc_nvenc":
            args.extend([
                "-preset", "p6",
                "-rc", "vbr",
                "-cq", str(preset.nvenc_cq),
                "-b:v", "0",
                "-tune", "hq",
                "-spatial-aq", "1",
                "-temporal-aq", "1"
            ])
        elif encoder.encoder_name == "hevc_amf":
            args.extend([
                "-quality", "quality",
                "-rc", "cqp",
                "-qp_i", str(preset.nvenc_cq),
                "-qp_p", str(preset.nvenc_cq)
            ])
        elif encoder.encoder_name == "hevc_qsv":
            args.extend([
                "-preset", "veryslow",
                "-global_quality", str(preset.nvenc_cq),
                "-look_ahead", "1"
            ])
        elif encoder.encoder_name == "hevc_mf":
            # Windows Media Foundation (Snapdragon X Elite / Plus / D3D11)
            args.extend([
                "-quality", "100"
            ])
        elif encoder.encoder_name in {"hevc_videotoolbox", "av1_videotoolbox"}:
            # Apple VideoToolbox (Apple Silicon M-series & Intel Macs)
            q_val = 70 if preset_key == "anime" else (65 if preset_key == "film" else 55)
            args.extend([
                "-q:v", str(q_val),
                "-tag:v", "hvc1",
                "-realtime", "0",
                "-spatial_aq", "1",
                "-allow_sw", "1"
            ])
            if meta and (meta.hdr_format or preset.tune_animation):
                args.extend(["-profile:v", "main10", "-pix_fmt", "p010le"])
        elif encoder.encoder_name == "h264_videotoolbox":
            # Apple VideoToolbox H.264 (Legacy Intel Macs)
            q_val = 70 if preset_key == "anime" else (65 if preset_key == "film" else 55)
            args.extend([
                "-q:v", str(q_val),
                "-realtime", "0"
            ])
        elif encoder.encoder_name in {"hevc_vaapi", "av1_vaapi"}:
            # Linux VAAPI (AMD Radeon & Intel on Linux)
            args.extend([
                "-vaapi_device", "/dev/dri/renderD128",
                "-vf", "format=nv12,hwupload",
                "-rc_mode", "CQP",
                "-qp", str(preset.nvenc_cq)
            ])
        elif encoder.encoder_name == "libx265":
            args.extend([
                "-preset", "slow",
                "-crf", str(preset.cpu_crf)
            ])
            if preset.tune_animation:
                args.extend(["-tune", "animation"])
        elif encoder.encoder_name == "libsvtav1":
            args.extend([
                "-preset", "5",
                "-crf", str(preset.cpu_crf + 2)
            ])

        # HDR passthrough flags if source has HDR
        if meta and meta.hdr_format:
            args.extend([
                "-color_primaries", meta.color_primaries,
                "-color_trc", meta.color_transfer,
                "-colorspace", "bt2020nc",
            ])
            if encoder.encoder_name == "libx265":
                args.extend([
                    "-x265-params",
                    "hdr-opt=1:repeat-headers=1:colorprim=bt2020:transfer=smpte2084:colormatrix=bt2020nc"
                ])

        # 2. Perfect lossless preservation of audio, subtitles, and metadata
        args.extend([
            "-c:a", "copy",
            "-c:s", "copy",
            "-map_metadata", "0"
        ])

        return args
