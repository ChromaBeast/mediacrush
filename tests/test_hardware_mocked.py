"""Unit tests for HardwareDetector command construction and encoder selection."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from mediacrush.core.hardware import EncoderInfo, HardwareDetector

NAMES = [c.encoder_name for c in HardwareDetector.PROBE_CANDIDATES]


class TestCandidates:
    def test_names_unique(self):
        assert len(NAMES) == len(set(NAMES))

    def test_cpu_fallbacks_present_for_hevc_av1_h264(self):
        cpu = {c.codec for c in HardwareDetector.PROBE_CANDIDATES if c.vendor == "CPU"}
        assert cpu == {"hevc", "av1", "h264"}

    def test_cpu_candidates_come_last(self):
        vendors = [c.vendor for c in HardwareDetector.PROBE_CANDIDATES]
        first_cpu = vendors.index("CPU")
        assert all(v == "CPU" for v in vendors[first_cpu:])

    def test_hardware_candidates_have_hwaccel(self):
        for c in HardwareDetector.PROBE_CANDIDATES:
            assert (c.hwaccel is None) == (c.vendor == "CPU")


class TestTestEncoder:
    def _run(self, cand, rc=0, exc=None):
        with patch("mediacrush.core.hardware.subprocess.run") as run:
            if exc:
                run.side_effect = exc
            else:
                run.return_value = MagicMock(returncode=rc)
            ok = HardwareDetector.test_encoder(cand)
        return ok, run

    def test_success(self):
        assert self._run(HardwareDetector.PROBE_CANDIDATES[0])[0] is True

    def test_failure_returncode(self):
        assert self._run(HardwareDetector.PROBE_CANDIDATES[0], rc=1)[0] is False

    @pytest.mark.parametrize("exc", [subprocess.TimeoutExpired("ffmpeg", 4), FileNotFoundError(), OSError()])
    def test_exceptions_mean_unsupported(self, exc):
        assert self._run(HardwareDetector.PROBE_CANDIDATES[0], exc=exc)[0] is False

    def test_vaapi_adds_device_flags(self):
        cand = next(c for c in HardwareDetector.PROBE_CANDIDATES if c.encoder_name == "hevc_vaapi")
        _, run = self._run(cand)
        cmd = run.call_args[0][0]
        assert "-vaapi_device" in cmd and "format=nv12,hwupload" in cmd

    def test_non_vaapi_has_no_device_flags(self):
        _, run = self._run(HardwareDetector.PROBE_CANDIDATES[0])
        assert "-vaapi_device" not in run.call_args[0][0]

    def test_command_uses_encoder_and_null_sink(self):
        cand = HardwareDetector.PROBE_CANDIDATES[3]
        _, run = self._run(cand)
        cmd = run.call_args[0][0]
        assert cmd[cmd.index("-c:v") + 1] == cand.encoder_name
        assert cmd[-3:] == ["-f", "null", "-"]


class TestSelection:
    def _avail(self, *names):
        return [c for c in HardwareDetector.PROBE_CANDIDATES if c.encoder_name in names]

    def test_prefers_requested_codec_first_match(self):
        with patch.object(HardwareDetector, "discover_encoders", return_value=self._avail("hevc_nvenc", "libx265", "libx264")):
            assert HardwareDetector.get_best_encoder("hevc").encoder_name == "hevc_nvenc"

    def test_other_codec(self):
        with patch.object(HardwareDetector, "discover_encoders", return_value=self._avail("hevc_nvenc", "libsvtav1")):
            assert HardwareDetector.get_best_encoder("av1").encoder_name == "libsvtav1"

    def test_falls_back_to_any_working(self):
        with patch.object(HardwareDetector, "discover_encoders", return_value=self._avail("libx264")):
            assert HardwareDetector.get_best_encoder("hevc").encoder_name == "libx264"

    def test_nothing_available_returns_cpu_default(self):
        with patch.object(HardwareDetector, "discover_encoders", return_value=[]):
            e = HardwareDetector.get_best_encoder()
        assert isinstance(e, EncoderInfo) and e.encoder_name == "libx265" and e.hwaccel is None

    def test_discover_filters_failures(self):
        with patch.object(HardwareDetector, "test_encoder", side_effect=lambda c: c.vendor == "CPU"):
            found = HardwareDetector.discover_encoders()
        assert found and all(c.vendor == "CPU" for c in found)
