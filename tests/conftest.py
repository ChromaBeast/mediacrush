"""Shared fixtures and helpers for the MediaCrush test suite."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

import pytest

from mediacrush.core.probe import MediaMetadata, StreamInfo

HAS_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
requires_ffmpeg = pytest.mark.skipif(not HAS_FFMPEG, reason="ffmpeg/ffprobe not installed")


def make_meta(
    path: str = "/fake/video.mkv",
    codec: str = "h264",
    width: int = 1920,
    height: int = 1080,
    duration: float = 1400.0,
    size_mb: float = 500,
    video_bitrate: int = 8_000_000,
    overall_bitrate: Optional[int] = None,
    audio: int = 1,
    subs: int = 0,
    hdr: Optional[str] = None,
    primaries: str = "unknown",
    transfer: str = "unknown",
) -> MediaMetadata:
    """Builds MediaMetadata without touching disk or ffprobe."""
    audios: List[StreamInfo] = [StreamInfo(i + 1, "audio", "aac", "en", None, 2) for i in range(audio)]
    subtitles: List[StreamInfo] = [StreamInfo(i + 10, "subtitle", "ass", "en") for i in range(subs)]
    return MediaMetadata(
        path=Path(path),
        duration_seconds=duration,
        file_size_bytes=int(size_mb * 1024 * 1024),
        video_codec=codec,
        width=width,
        height=height,
        fps=24.0,
        video_bitrate=video_bitrate,
        overall_bitrate=overall_bitrate if overall_bitrate is not None else video_bitrate + 192_000,
        audio_streams=audios,
        subtitle_streams=subtitles,
        hdr_format=hdr,
        color_primaries=primaries,
        color_transfer=transfer,
    )


@pytest.fixture
def meta_factory():
    return make_meta


def generate_video(
    path: Path,
    seconds: float = 12,
    size: str = "320x240",
    audio: bool = True,
    codec: str = "libx264",
    pattern: str = "testsrc2",
    extra: Optional[List[str]] = None,
) -> Path:
    """Creates a real, tiny test video with ffmpeg (requires ffmpeg)."""
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"{pattern}{':' if '=' in pattern else '='}s={size}:r=24:d={seconds}"]
    if audio:
        cmd += ["-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}"]
    cmd += ["-c:v", codec, "-pix_fmt", "yuv420p"]
    if audio:
        cmd += ["-c:a", "aac", "-shortest"]
    cmd += (extra or []) + [str(path)]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
    return path


@pytest.fixture
def video_factory(tmp_path):
    """Returns a callable that writes real videos into tmp_path."""
    def _make(name: str = "clip.mp4", **kwargs) -> Path:
        return generate_video(tmp_path / name, **kwargs)
    return _make


@pytest.fixture
def cli_args():
    """Builds an argparse.Namespace mirroring `mediacrush compress` flags."""
    import argparse

    def _make(**overrides):
        base = dict(
            path=".", preset="auto", side_by_side=False, keep_backup=False,
            dry_run=False, report=None, pause=False, quality_check=False,
        )
        base.update(overrides)
        return argparse.Namespace(**base)
    return _make
