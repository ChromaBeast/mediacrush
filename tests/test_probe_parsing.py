"""Unit tests for MediaProbe ffprobe JSON parsing (subprocess mocked)."""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mediacrush.core.probe import MediaMetadata, MediaProbe


def _probe(tmp_path, payload=None, side_effect=None):
    f = tmp_path / "a.mkv"
    f.write_bytes(b"x" * 100)
    with patch("mediacrush.core.probe.subprocess.run") as run:
        if side_effect is not None:
            run.side_effect = side_effect
        else:
            run.return_value = MagicMock(stdout=json.dumps(payload))
        return MediaProbe.inspect(f), run


BASE = {
    "format": {"duration": "100.5", "size": "5000", "bit_rate": "400000"},
    "streams": [
        {"index": 0, "codec_type": "video", "codec_name": "h264", "width": 1920, "height": 1080,
         "r_frame_rate": "24000/1001", "bit_rate": "350000"},
        {"index": 1, "codec_type": "audio", "codec_name": "aac", "channels": 6, "tags": {"language": "jpn", "title": "Main"}},
        {"index": 2, "codec_type": "subtitle", "codec_name": "ass", "tags": {"language": "eng"}},
    ],
}


class TestResolutionLabel:
    @pytest.mark.parametrize("w,h,label", [
        (3840, 2160, "4K"), (3840, 1600, "4K"), (1920, 1080, "1080p"), (1920, 800, "1080p"),
        (1280, 720, "720p"), (1280, 534, "720p"), (640, 480, "640x480"), (0, 0, "0x0"),
    ])
    def test_labels(self, w, h, label):
        m = MediaMetadata(Path("x"), 1, 1, "h264", w, h, 24, 0, 0)
        assert m.resolution_label == label


class TestInspectParsing:
    def test_full_parse(self, tmp_path):
        meta, run = _probe(tmp_path, BASE)
        assert meta.duration_seconds == 100.5
        assert meta.file_size_bytes == 5000
        assert meta.overall_bitrate == 400000
        assert (meta.video_codec, meta.width, meta.height) == ("h264", 1920, 1080)
        assert meta.video_bitrate == 350000
        assert meta.fps == pytest.approx(23.976, abs=1e-3)
        assert len(meta.audio_streams) == 1 and meta.audio_streams[0].channels == 6
        assert meta.audio_streams[0].language == "jpn" and meta.audio_streams[0].title == "Main"
        assert len(meta.subtitle_streams) == 1 and meta.subtitle_streams[0].codec_name == "ass"
        assert meta.hdr_format is None

    def test_missing_file_returns_none(self, tmp_path):
        assert MediaProbe.inspect(tmp_path / "nope.mkv") is None

    def test_empty_file_returns_none(self, tmp_path):
        f = tmp_path / "empty.mkv"
        f.touch()
        assert MediaProbe.inspect(f) is None

    def test_ffprobe_failure_returns_none(self, tmp_path):
        meta, _ = _probe(tmp_path, side_effect=subprocess.CalledProcessError(1, "ffprobe"))
        assert meta is None

    def test_ffprobe_missing_binary_returns_none(self, tmp_path):
        meta, _ = _probe(tmp_path, side_effect=FileNotFoundError())
        assert meta is None

    def test_ffprobe_timeout_returns_none(self, tmp_path):
        meta, _ = _probe(tmp_path, side_effect=subprocess.TimeoutExpired("ffprobe", 15))
        assert meta is None

    def test_invalid_json_returns_none(self, tmp_path):
        f = tmp_path / "a.mkv"
        f.write_bytes(b"x")
        with patch("mediacrush.core.probe.subprocess.run", return_value=MagicMock(stdout="not json")):
            assert MediaProbe.inspect(f) is None

    def test_no_video_stream_defaults(self, tmp_path):
        meta, _ = _probe(tmp_path, {"format": {"duration": "5"}, "streams": []})
        assert meta.video_codec == "unknown"
        assert meta.width == 0 and meta.height == 0
        assert meta.fps == 24.0

    def test_size_falls_back_to_stat(self, tmp_path):
        meta, _ = _probe(tmp_path, {"format": {"duration": "5"}, "streams": []})
        assert meta.file_size_bytes == 100

    @pytest.mark.parametrize("rate,expected", [("30/1", 30.0), ("0/0", 24.0), ("garbage", 24.0), ("60000/1001", 59.94)])
    def test_fps_parsing(self, tmp_path, rate, expected):
        payload = {"format": {}, "streams": [{"index": 0, "codec_type": "video", "r_frame_rate": rate}]}
        meta, _ = _probe(tmp_path, payload)
        assert meta.fps == pytest.approx(expected, abs=0.01)

    def test_bitrate_from_tags_bps(self, tmp_path):
        payload = {"format": {}, "streams": [{"index": 0, "codec_type": "video", "tags": {"BPS": "1234567"}}]}
        meta, _ = _probe(tmp_path, payload)
        assert meta.video_bitrate == 1234567

    def test_non_numeric_bitrate_is_zero(self, tmp_path):
        payload = {"format": {}, "streams": [{"index": 0, "codec_type": "video", "bit_rate": "N/A"}]}
        meta, _ = _probe(tmp_path, payload)
        assert meta.video_bitrate == 0


class TestHdrDetection:
    def _video(self, **kw):
        s = {"index": 0, "codec_type": "video", "codec_name": "hevc", "width": 3840, "height": 2160}
        s.update(kw)
        return {"format": {"duration": "1"}, "streams": [s]}

    def test_hdr10_from_color_tags(self, tmp_path):
        meta, _ = _probe(tmp_path, self._video(color_primaries="bt2020", color_trc="smpte2084"))
        assert meta.hdr_format == "HDR10"
        assert meta.color_primaries == "bt2020"

    def test_hlg_detected_as_hdr10(self, tmp_path):
        meta, _ = _probe(tmp_path, self._video(color_primaries="bt2020", color_trc="arib-std-b67"))
        assert meta.hdr_format == "HDR10"

    def test_dolby_vision(self, tmp_path):
        meta, _ = _probe(tmp_path, self._video(side_data_list=[{"side_data_type": "DOVI configuration record"}]))
        assert meta.hdr_format == "DolbyVision"

    def test_hdr10_plus(self, tmp_path):
        meta, _ = _probe(tmp_path, self._video(side_data_list=[{"side_data_type": "HDR Dynamic Metadata SMPTE2094-40 (HDR10+)"}]))
        assert meta.hdr_format == "HDR10+"

    def test_sdr_bt709(self, tmp_path):
        meta, _ = _probe(tmp_path, self._video(color_primaries="bt709", color_trc="bt709"))
        assert meta.hdr_format is None

    def test_bt2020_sdr_transfer_not_hdr(self, tmp_path):
        meta, _ = _probe(tmp_path, self._video(color_primaries="bt2020", color_trc="bt709"))
        assert meta.hdr_format is None
