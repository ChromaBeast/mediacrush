"""Unit tests for TranscodeEngine progress parsing, cancellation, and failure paths."""

from unittest.mock import MagicMock, patch

import pytest

from conftest import make_meta
from mediacrush.core.hardware import EncoderInfo
from mediacrush.core.transcoder import TranscodeEngine, TranscodeProgress

CPU = EncoderInfo("hevc", "libx265", "CPU", None, "cpu")
HW = EncoderInfo("hevc", "hevc_nvenc", "NVIDIA", "cuda", "nv")
VAAPI = EncoderInfo("hevc", "hevc_vaapi", "Linux", "vaapi", "va")


def fake_popen(lines, returncode=0):
    p = MagicMock()
    p.stdout = iter(lines)
    p.returncode = returncode
    return p


class TestRegexes:
    def test_time_regex(self):
        m = TranscodeEngine.TIME_REGEX.search("frame=1 fps=24 time=01:02:03.50 speed=2.0x")
        assert m.groups() == ("01", "02", "03.50")

    def test_fps_and_speed(self):
        line = "frame=100 fps= 48.5 q=-0.0 time=00:00:04.00 bitrate=1000kbits/s speed=1.50x"
        assert TranscodeEngine.FPS_REGEX.search(line).group(1) == "48.5"
        assert TranscodeEngine.SPEED_REGEX.search(line).group(1) == "1.50"

    def test_no_match_on_noise(self):
        assert TranscodeEngine.TIME_REGEX.search("Stream mapping:") is None


class TestTranscodeFlow:
    def setup_method(self):
        self.meta = make_meta(path="/v/movie.mkv", duration=100.0)

    def _run(self, lines, rc=0, verify=(True, "ok"), enc=CPU, cb=None, **kw):
        engine = TranscodeEngine()
        with patch("mediacrush.core.transcoder.subprocess.Popen", return_value=fake_popen(lines, rc)) as popen, \
             patch("mediacrush.core.transcoder.SafetyManager.verify_transcode", return_value=verify), \
             patch("mediacrush.core.transcoder.SafetyManager.finalize_transcode") as fin, \
             patch("mediacrush.core.transcoder.SafetyManager.cleanup_staging") as clean:
            ok = engine.transcode(self.meta, enc, "film", progress_callback=cb, **kw)
        return ok, popen, fin, clean

    def test_success_finalizes(self):
        ok, _, fin, _ = self._run(["frame=1 fps=10 time=00:00:50.00 speed=2.0x\n"])
        assert ok is True
        fin.assert_called_once()

    def test_progress_values(self):
        got = []
        self._run(["frame=1 fps=30 time=00:00:25.00 speed=2.0x\n"], cb=got.append)
        p: TranscodeProgress = got[0]
        assert p.percent == pytest.approx(25.0)
        assert p.fps == 30.0 and p.speed_multiplier == 2.0
        assert p.current_time_seconds == 25.0 and p.total_time_seconds == 100.0
        assert p.eta_seconds == pytest.approx(37.5)

    def test_progress_capped_at_100(self):
        got = []
        self._run(["time=00:05:00.00 speed=1.0x\n"], cb=got.append)
        assert got[0].percent == 100.0 and got[0].eta_seconds == 0.0

    def test_missing_fps_speed_defaults(self):
        got = []
        self._run(["time=00:00:10.00\n"], cb=got.append)
        assert got[0].fps == 0.0 and got[0].speed_multiplier == 1.0

    def test_no_callback_ok(self):
        ok, *_ = self._run(["time=00:00:10.00\n"], cb=None)
        assert ok

    def test_nonzero_exit_fails_and_cleans(self):
        ok, _, fin, clean = self._run([], rc=1)
        assert ok is False
        fin.assert_not_called()
        assert clean.call_count >= 2  # pre-clean and post-failure clean

    def test_verification_failure_does_not_finalize(self):
        ok, _, fin, _ = self._run([], verify=(False, "bad"))
        assert ok is False
        fin.assert_not_called()

    def test_popen_exception_returns_false(self):
        engine = TranscodeEngine()
        with patch("mediacrush.core.transcoder.subprocess.Popen", side_effect=OSError("no ffmpeg")), \
             patch("mediacrush.core.transcoder.SafetyManager.cleanup_staging"):
            assert engine.transcode(self.meta, CPU) is False

    def test_hwaccel_flag_for_hardware_encoder(self):
        _, popen, *_ = self._run([], enc=HW)
        cmd = popen.call_args[0][0]
        assert cmd[cmd.index("-hwaccel") + 1] == "auto"

    def test_no_hwaccel_for_cpu_encoder(self):
        _, popen, *_ = self._run([], enc=CPU)
        assert "-hwaccel" not in popen.call_args[0][0]

    def test_no_hwaccel_flag_for_vaapi(self):
        _, popen, *_ = self._run([], enc=VAAPI)
        assert "-hwaccel" not in popen.call_args[0][0]

    def test_command_shape(self):
        _, popen, *_ = self._run([])
        cmd = popen.call_args[0][0]
        assert cmd[:2] == ["ffmpeg", "-y"]
        assert cmd[cmd.index("-i") + 1] == str(self.meta.path)
        assert cmd[-1].endswith(".mediacrush.temp.mkv")

    def test_finalize_receives_flags(self):
        _, _, fin, _ = self._run([], in_place=False, keep_backup=True)
        assert fin.call_args[0][2:] == (False, True)

    def test_process_cleared_after_run(self):
        engine = TranscodeEngine()
        with patch("mediacrush.core.transcoder.subprocess.Popen", return_value=fake_popen([])), \
             patch("mediacrush.core.transcoder.SafetyManager.verify_transcode", return_value=(True, "")), \
             patch("mediacrush.core.transcoder.SafetyManager.finalize_transcode"), \
             patch("mediacrush.core.transcoder.SafetyManager.cleanup_staging"):
            engine.transcode(self.meta, CPU)
        assert engine._current_process is None


class TestCancel:
    def test_cancel_terminates_process(self):
        e = TranscodeEngine()
        e._current_process = MagicMock()
        e.cancel()
        e._current_process.terminate.assert_called_once()
        assert e._is_cancelled

    def test_cancel_without_process_is_safe(self):
        TranscodeEngine().cancel()

    def test_cancel_mid_stream_returns_false(self):
        engine = TranscodeEngine()
        meta = make_meta(duration=100)

        def lines():
            yield "time=00:00:01.00\n"
            engine.cancel()
            yield "time=00:00:02.00\n"

        proc = MagicMock(stdout=lines(), returncode=0)
        with patch("mediacrush.core.transcoder.subprocess.Popen", return_value=proc), \
             patch("mediacrush.core.transcoder.SafetyManager.verify_transcode") as ver, \
             patch("mediacrush.core.transcoder.SafetyManager.finalize_transcode") as fin, \
             patch("mediacrush.core.transcoder.SafetyManager.cleanup_staging"):
            assert engine.transcode(meta, CPU) is False
        ver.assert_not_called()
        fin.assert_not_called()

    def test_cancel_flag_reset_on_new_run(self):
        engine = TranscodeEngine()
        engine._is_cancelled = True
        with patch("mediacrush.core.transcoder.subprocess.Popen", return_value=fake_popen([])), \
             patch("mediacrush.core.transcoder.SafetyManager.verify_transcode", return_value=(True, "")), \
             patch("mediacrush.core.transcoder.SafetyManager.finalize_transcode"), \
             patch("mediacrush.core.transcoder.SafetyManager.cleanup_staging"):
            assert engine.transcode(make_meta(), CPU) is True
