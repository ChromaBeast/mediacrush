"""Unit tests for PresetManager.build_ffmpeg_args per encoder / preset / HDR."""

import pytest

from conftest import make_meta
from mediacrush.core.hardware import EncoderInfo
from mediacrush.core.presets import PresetManager


def enc(name, vendor="X", hw=None):
    return EncoderInfo("hevc", name, vendor, hw, name)


def val(args, flag):
    return args[args.index(flag) + 1]


class TestCommonArgs:
    @pytest.mark.parametrize("name", [
        "hevc_nvenc", "hevc_amf", "hevc_qsv", "hevc_mf", "hevc_videotoolbox",
        "h264_videotoolbox", "hevc_vaapi", "libx265", "libsvtav1",
    ])
    def test_every_encoder_maps_streams_and_copies_audio_subs(self, name):
        args = PresetManager.build_ffmpeg_args(enc(name), "film")
        assert args[:2] == ["-map", "0"]
        assert val(args, "-c:v") == name
        assert val(args, "-c:a") == "copy"
        assert val(args, "-c:s") == "copy"
        assert val(args, "-map_metadata") == "0"

    def test_unknown_preset_falls_back_to_anime(self):
        a = PresetManager.build_ffmpeg_args(enc("libx265"), "bogus")
        b = PresetManager.build_ffmpeg_args(enc("libx265"), "anime")
        assert a == b

    def test_all_args_are_strings(self):
        for name in ("hevc_nvenc", "libx265", "hevc_videotoolbox"):
            assert all(isinstance(x, str) for x in PresetManager.build_ffmpeg_args(enc(name), "saver"))

    def test_saver_is_more_aggressive_than_film(self):
        assert PresetManager.PRESETS["saver"].cpu_crf > PresetManager.PRESETS["film"].cpu_crf
        assert PresetManager.PRESETS["saver"].nvenc_cq > PresetManager.PRESETS["film"].nvenc_cq


class TestEncoderSpecific:
    def test_nvenc_uses_cq_and_vbr(self):
        a = PresetManager.build_ffmpeg_args(enc("hevc_nvenc"), "saver")
        assert val(a, "-cq") == "24" and val(a, "-rc") == "vbr" and val(a, "-b:v") == "0"

    def test_amf_uses_cqp(self):
        a = PresetManager.build_ffmpeg_args(enc("hevc_amf"), "film")
        assert val(a, "-rc") == "cqp" and val(a, "-qp_i") == "20"

    def test_qsv_global_quality(self):
        assert val(PresetManager.build_ffmpeg_args(enc("hevc_qsv"), "anime"), "-global_quality") == "20"

    def test_vaapi_includes_device_and_hwupload(self):
        a = PresetManager.build_ffmpeg_args(enc("hevc_vaapi"), "anime")
        assert "-vaapi_device" in a and "hwupload" in val(a, "-vf")

    @pytest.mark.parametrize("preset,q", [("anime", "70"), ("film", "65"), ("saver", "55")])
    def test_videotoolbox_quality_per_preset(self, preset, q):
        a = PresetManager.build_ffmpeg_args(enc("hevc_videotoolbox"), preset)
        assert val(a, "-q:v") == q and val(a, "-tag:v") == "hvc1"

    def test_h264_videotoolbox_has_no_hvc1_tag(self):
        a = PresetManager.build_ffmpeg_args(enc("h264_videotoolbox"), "film")
        assert "-tag:v" not in a

    def test_x265_animation_tune_only_for_anime(self):
        assert "-tune" in PresetManager.build_ffmpeg_args(enc("libx265"), "anime")
        assert "-tune" not in PresetManager.build_ffmpeg_args(enc("libx265"), "film")
        assert val(PresetManager.build_ffmpeg_args(enc("libx265"), "film"), "-crf") == "20"

    def test_svtav1_crf_offset(self):
        a = PresetManager.build_ffmpeg_args(enc("libsvtav1"), "film")
        assert val(a, "-crf") == "22"

    def test_unrecognized_encoder_still_valid(self):
        a = PresetManager.build_ffmpeg_args(enc("mystery"), "film")
        assert val(a, "-c:v") == "mystery"


class TestHdr:
    def test_hdr_flags_added(self):
        m = make_meta(hdr="HDR10", primaries="bt2020", transfer="smpte2084")
        a = PresetManager.build_ffmpeg_args(enc("hevc_nvenc"), "film", meta=m)
        assert val(a, "-color_primaries") == "bt2020"
        assert val(a, "-color_trc") == "smpte2084"
        assert val(a, "-colorspace") == "bt2020nc"
        assert "-x265-params" not in a

    def test_x265_hdr_params(self):
        m = make_meta(hdr="HDR10", primaries="bt2020", transfer="smpte2084")
        a = PresetManager.build_ffmpeg_args(enc("libx265"), "film", meta=m)
        assert "hdr-opt=1" in val(a, "-x265-params")

    def test_sdr_no_hdr_flags(self):
        a = PresetManager.build_ffmpeg_args(enc("libx265"), "film", meta=make_meta())
        assert "-color_primaries" not in a

    def test_videotoolbox_main10_for_hdr(self):
        m = make_meta(hdr="HDR10", primaries="bt2020", transfer="smpte2084")
        a = PresetManager.build_ffmpeg_args(enc("hevc_videotoolbox"), "film", meta=m)
        assert val(a, "-profile:v") == "main10"

    def test_videotoolbox_main10_for_anime_even_sdr(self):
        a = PresetManager.build_ffmpeg_args(enc("hevc_videotoolbox"), "anime", meta=make_meta())
        assert val(a, "-pix_fmt") == "p010le"

    def test_videotoolbox_film_sdr_stays_8bit(self):
        a = PresetManager.build_ffmpeg_args(enc("hevc_videotoolbox"), "film", meta=make_meta())
        assert "-pix_fmt" not in a
