"""Unit tests for PresetManager.build_ffmpeg_args."""

import unittest
from mediacrush.core.hardware import EncoderInfo
from mediacrush.core.presets import PresetManager


def nvenc_encoder() -> EncoderInfo:
    return EncoderInfo("hevc", "hevc_nvenc", "NVIDIA", "cuda", "NVIDIA NVENC H.265")


def cpu_encoder() -> EncoderInfo:
    return EncoderInfo("hevc", "libx265", "CPU", None, "CPU x265")


def mac_videotoolbox_encoder() -> EncoderInfo:
    return EncoderInfo("hevc", "hevc_videotoolbox", "Apple", "videotoolbox", "Apple VideoToolbox H.265")


def linux_vaapi_encoder() -> EncoderInfo:
    return EncoderInfo("hevc", "hevc_vaapi", "Linux/VAAPI", "vaapi", "Linux VAAPI H.265")


class TestBuildFFmpegArgs(unittest.TestCase):

    def test_returns_list_of_strings(self):
        """build_ffmpeg_args must return a list of strings."""
        args = PresetManager.build_ffmpeg_args(nvenc_encoder(), "anime")
        self.assertIsInstance(args, list)
        self.assertTrue(all(isinstance(a, str) for a in args))

    def test_map_zero_present(self):
        """-map 0 must be included."""
        args = PresetManager.build_ffmpeg_args(nvenc_encoder(), "anime")
        self.assertIn("-map", args)
        idx = args.index("-map")
        self.assertEqual(args[idx + 1], "0")

    def test_audio_copy_present(self):
        """-c:a copy must be present."""
        args = PresetManager.build_ffmpeg_args(cpu_encoder(), "film")
        self.assertIn("-c:a", args)
        idx = args.index("-c:a")
        self.assertEqual(args[idx + 1], "copy")

    def test_subtitle_copy_present(self):
        """-c:s copy must be present."""
        args = PresetManager.build_ffmpeg_args(cpu_encoder(), "film")
        self.assertIn("-c:s", args)
        idx = args.index("-c:s")
        self.assertEqual(args[idx + 1], "copy")

    def test_nvenc_video_codec(self):
        """-c:v hevc_nvenc for NVENC encoder."""
        args = PresetManager.build_ffmpeg_args(nvenc_encoder(), "anime")
        self.assertIn("-c:v", args)
        idx = args.index("-c:v")
        self.assertEqual(args[idx + 1], "hevc_nvenc")

    def test_cpu_video_codec(self):
        """-c:v libx265 for CPU encoder."""
        args = PresetManager.build_ffmpeg_args(cpu_encoder(), "anime")
        self.assertIn("-c:v", args)
        idx = args.index("-c:v")
        self.assertEqual(args[idx + 1], "libx265")

    def test_videotoolbox_mac_args(self):
        """VideoToolbox encoder for Apple Silicon and Intel Macs uses -q:v, hvc1, and spatial_aq."""
        enc = mac_videotoolbox_encoder()
        args = PresetManager.build_ffmpeg_args(enc, "anime")
        self.assertIn("-c:v", args)
        self.assertEqual(args[args.index("-c:v") + 1], "hevc_videotoolbox")
        self.assertIn("-q:v", args)
        self.assertIn("-tag:v", args)
        self.assertEqual(args[args.index("-tag:v") + 1], "hvc1")
        self.assertIn("-spatial_aq", args)

    def test_vaapi_linux_args(self):
        """VAAPI encoder for Linux AMD/Intel uses /dev/dri/renderD128 and CQP."""
        enc = linux_vaapi_encoder()
        args = PresetManager.build_ffmpeg_args(enc, "anime")
        self.assertIn("-c:v", args)
        self.assertEqual(args[args.index("-c:v") + 1], "hevc_vaapi")
        self.assertIn("-vaapi_device", args)
        self.assertIn("-rc_mode", args)
        self.assertEqual(args[args.index("-rc_mode") + 1], "CQP")

    def test_crf_differs_anime_vs_saver(self):
        """CRF value should differ between anime and saver presets for CPU."""
        enc = cpu_encoder()
        anime_args = PresetManager.build_ffmpeg_args(enc, "anime")
        saver_args = PresetManager.build_ffmpeg_args(enc, "saver")
        anime_crf = anime_args[anime_args.index("-crf") + 1]
        saver_crf = saver_args[saver_args.index("-crf") + 1]
        self.assertNotEqual(anime_crf, saver_crf)


if __name__ == "__main__":
    unittest.main()
