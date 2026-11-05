"""Integration tests that run the real ffmpeg/ffprobe pipeline on tiny generated clips.

Skipped automatically when ffmpeg/ffprobe are not installed.
"""

import json

import pytest

from conftest import generate_video, requires_ffmpeg
from mediacrush.core.content_classifier import ContentClassifier, ContentType
from mediacrush.core.deduplicator import DuplicateDetector
from mediacrush.core.hardware import EncoderInfo, HardwareDetector
from mediacrush.core.probe import MediaProbe
from mediacrush.core.safety import SafetyManager
from mediacrush.core.scanner import LibraryScanner
from mediacrush.core.transcoder import TranscodeEngine

pytestmark = requires_ffmpeg

X264 = EncoderInfo("h264", "libx264", "CPU", None, "x264")


def cpu_hevc():
    """A CPU encoder that actually works on this machine (libx265 may be absent)."""
    for c in HardwareDetector.PROBE_CANDIDATES:
        if c.vendor == "CPU" and c.codec == "hevc" and HardwareDetector.test_encoder(c):
            return c
    return None


@pytest.fixture(scope="module")
def src_dir(tmp_path_factory):
    d = tmp_path_factory.mktemp("media")
    generate_video(d / "clip.mp4", seconds=12, size="640x360")
    return d


@pytest.fixture
def clip(tmp_path, src_dir):
    dst = tmp_path / "clip.mp4"
    dst.write_bytes((src_dir / "clip.mp4").read_bytes())
    return dst


class TestProbeReal:
    def test_reads_real_metadata(self, clip):
        m = MediaProbe.inspect(clip)
        assert m is not None
        assert m.video_codec == "h264" and (m.width, m.height) == (640, 360)
        assert m.duration_seconds == pytest.approx(12, abs=0.5)
        assert m.fps == pytest.approx(24, abs=0.1)
        assert len(m.audio_streams) == 1 and m.audio_streams[0].codec_name == "aac"
        assert m.hdr_format is None and m.file_size_bytes == clip.stat().st_size

    def test_corrupt_file_returns_none(self, tmp_path):
        bad = tmp_path / "bad.mkv"
        bad.write_bytes(b"this is not a video" * 100)
        assert MediaProbe.inspect(bad) is None

    def test_silent_video_has_no_audio(self, tmp_path):
        v = generate_video(tmp_path / "silent.mp4", seconds=2, audio=False)
        assert MediaProbe.inspect(v).audio_streams == []


class TestHardwareReal:
    def test_cpu_encoder_discoverable(self):
        names = {e.encoder_name for e in HardwareDetector.discover_encoders()}
        assert names & {"libx264", "libx265", "libsvtav1"}

    def test_best_encoder_is_functional(self):
        best = HardwareDetector.get_best_encoder()
        if best.description != "CPU Fallback":
            assert HardwareDetector.test_encoder(best)


class TestClassifierReal:
    def test_flat_animation_like_clip_detected_as_anime(self, tmp_path):
        v = generate_video(tmp_path / "flat.mp4", seconds=12, pattern="color=c=blue", extra=[])
        assert ContentClassifier.detect(v) == ContentType.ANIME

    def test_noisy_clip_is_live_action(self, tmp_path):
        v = tmp_path / "noise.mp4"
        import subprocess
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=gray:s=320x180:r=24:d=6,noise=alls=100:allf=t+u",
                        "-c:v", "libx264", "-qp", "0", "-pix_fmt", "yuv444p", str(v)], check=True, timeout=60)
        assert ContentClassifier.detect(v) in (ContentType.LIVE_ACTION, ContentType.UNKNOWN)  # both map to 'film'


class TestScannerReal:
    def test_small_clip_skipped_as_under_40mb(self, src_dir):
        r = LibraryScanner.scan_path(src_dir)
        assert r.candidates == [] and r.skipped_count == 1


class TestDedupeReal:
    def test_identical_clips_detected(self, tmp_path, src_dir):
        data = (src_dir / "clip.mp4").read_bytes()
        (tmp_path / "a.mp4").write_bytes(data)
        (tmp_path / "b.mp4").write_bytes(data)
        groups = DuplicateDetector.find(tmp_path)
        assert len(groups) == 1 and len(groups[0].files) == 2
        assert groups[0].removable_size_bytes == len(data)


class TestTranscodeEndToEnd:
    """Full pipeline: probe -> preset args -> ffmpeg -> verify -> finalize."""

    @pytest.fixture(autouse=True)
    def _relax_min_size(self, monkeypatch):
        # Tiny generated clips are far below the production 1 MB sanity floor, so swap in a
        # verifier that keeps the duration/audio/readability checks but drops the size floor.
        monkeypatch.setattr(SafetyManager, "verify_transcode",
                            classmethod(lambda cls, meta, staging: self._verify_ignoring_size(meta, staging)))

    @staticmethod
    def _verify_ignoring_size(source_meta, staging):
        out = MediaProbe.inspect(staging)
        if not out:
            return False, "unreadable"
        if abs(source_meta.duration_seconds - out.duration_seconds) > 1.5:
            return False, "duration"
        if source_meta.audio_streams and not out.audio_streams:
            return False, "audio"
        return True, "ok"

    def test_in_place_transcode(self, clip):
        meta = MediaProbe.inspect(clip)
        progress = []
        ok = TranscodeEngine().transcode(meta, X264, "film", in_place=True, progress_callback=progress.append)
        assert ok is True
        assert clip.exists() and not SafetyManager.get_staging_path(clip).exists()
        out = MediaProbe.inspect(clip)
        assert out.duration_seconds == pytest.approx(meta.duration_seconds, abs=1.5)
        assert len(out.audio_streams) == 1
        if progress:
            assert progress[-1].percent <= 100.0

    def test_side_by_side_keeps_original(self, clip):
        original = clip.read_bytes()
        meta = MediaProbe.inspect(clip)
        assert TranscodeEngine().transcode(meta, X264, "saver", in_place=False) is True
        assert clip.read_bytes() == original
        assert (clip.parent / "clip.crushed.mkv").exists()

    def test_keep_backup(self, clip):
        original = clip.read_bytes()
        meta = MediaProbe.inspect(clip)
        assert TranscodeEngine().transcode(meta, X264, "film", in_place=True, keep_backup=True) is True
        assert (clip.parent / "clip.mp4.bak").read_bytes() == original

    def test_bad_encoder_fails_and_preserves_source(self, clip):
        original = clip.read_bytes()
        meta = MediaProbe.inspect(clip)
        bogus = EncoderInfo("hevc", "no_such_encoder", "X", None, "")
        assert TranscodeEngine().transcode(meta, bogus, "film") is False
        assert clip.read_bytes() == original
        assert not SafetyManager.get_staging_path(clip).exists()

    def test_hevc_cpu_when_available(self, clip):
        enc = cpu_hevc()
        if enc is None:
            pytest.skip("no working CPU HEVC encoder")
        meta = MediaProbe.inspect(clip)
        assert TranscodeEngine().transcode(meta, enc, "anime", in_place=False) is True
        assert MediaProbe.inspect(clip.parent / "clip.crushed.mkv").video_codec in {"hevc", "av1"}


class TestCliEndToEnd:
    def test_scan_command_on_real_dir(self, src_dir, capsys, monkeypatch):
        import argparse
        from rich.console import Console
        from mediacrush.cli import commands, formatters
        c = Console(record=True, width=200)
        monkeypatch.setattr(commands, "console", c)
        monkeypatch.setattr(formatters, "console", c)
        commands.cmd_scan(argparse.Namespace(path=str(src_dir)))
        assert "Skipped 1" in c.export_text()

    def test_main_entry_scan(self, src_dir, monkeypatch):
        from mediacrush.cli import main as m
        monkeypatch.setattr("sys.argv", ["mediacrush", "scan", str(src_dir)])
        m.main()  # must not raise
