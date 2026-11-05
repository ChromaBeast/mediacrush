"""Unit tests for FolderWatcher and its event handler (watchdog events faked)."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

import mediacrush.core.watcher as w
from conftest import make_meta
from mediacrush.core.hardware import EncoderInfo
from mediacrush.core.scanner import CandidateFile, ScanReport

pytest.importorskip("watchdog")

ENC = EncoderInfo("hevc", "libx265", "CPU", None, "")


@pytest.fixture(autouse=True)
def no_sleep_and_quiet(monkeypatch):
    monkeypatch.setattr(w.time, "sleep", lambda s: None)
    monkeypatch.setattr(w, "console", Console(record=True))


@pytest.fixture
def watcher(tmp_path):
    return w.FolderWatcher(tmp_path, "film", ENC)


def ev(path, directory=False, dest=None):
    return SimpleNamespace(src_path=str(path), is_directory=directory, dest_path=dest)


class TestHandler:
    def test_new_video_processed_once(self, watcher):
        watcher.process_file = MagicMock()
        h = w.VideoFileHandler(watcher)
        h.on_created(ev("/x/a.mkv"))
        h.on_created(ev("/x/a.mkv"))
        watcher.process_file.assert_called_once_with(Path("/x/a.mkv"))

    @pytest.mark.parametrize("name", ["note.txt", "a.mediacrush.temp.mkv", "img.jpg"])
    def test_ignored_files(self, watcher, name):
        watcher.process_file = MagicMock()
        w.VideoFileHandler(watcher).on_created(ev(f"/x/{name}"))
        watcher.process_file.assert_not_called()

    def test_directories_ignored(self, watcher):
        watcher.process_file = MagicMock()
        w.VideoFileHandler(watcher).on_created(ev("/x/dir.mkv", directory=True))
        watcher.process_file.assert_not_called()

    def test_moved_in_uses_dest(self, watcher):
        watcher.process_file = MagicMock()
        w.VideoFileHandler(watcher).on_moved(ev("/tmp/x.part", dest="/x/final.mp4"))
        watcher.process_file.assert_called_once_with(Path("/x/final.mp4"))

    def test_moved_without_dest(self, watcher):
        watcher.process_file = MagicMock()
        w.VideoFileHandler(watcher).on_moved(ev("/tmp/x.part", dest=None))
        watcher.process_file.assert_not_called()

    def test_uppercase_extension(self, watcher):
        watcher.process_file = MagicMock()
        w.VideoFileHandler(watcher).on_created(ev("/x/A.MKV"))
        watcher.process_file.assert_called_once()


class TestProcessFile:
    def _report(self, tmp_path, cands):
        return ScanReport(tmp_path, cands, 0, 0, 0)

    def test_skips_when_no_candidates(self, watcher, tmp_path):
        watcher.engine = MagicMock()
        with patch.object(w.LibraryScanner, "scan_path", return_value=self._report(tmp_path, [])):
            watcher.process_file(tmp_path / "a.mkv")
        watcher.engine.transcode.assert_not_called()

    def test_transcodes_candidate_in_place(self, watcher, tmp_path):
        c = CandidateFile(make_meta(str(tmp_path / "a.mkv")), "r", 1, 10)
        watcher.engine = MagicMock(transcode=MagicMock(return_value=True))
        with patch.object(w.LibraryScanner, "scan_path", return_value=self._report(tmp_path, [c])):
            watcher.process_file(tmp_path / "a.mkv")
        kw = watcher.engine.transcode.call_args.kwargs
        assert kw["preset_key"] == "film" and kw["in_place"] is True and kw["encoder"] is ENC

    def test_failure_does_not_raise(self, watcher, tmp_path):
        c = CandidateFile(make_meta(str(tmp_path / "a.mkv")), "r", 1, 10)
        watcher.engine = MagicMock(transcode=MagicMock(return_value=False))
        with patch.object(w.LibraryScanner, "scan_path", return_value=self._report(tmp_path, [c])):
            watcher.process_file(tmp_path / "a.mkv")


class TestLifecycle:
    def test_requires_watchdog(self, monkeypatch, tmp_path):
        monkeypatch.setattr(w, "_WATCHDOG_AVAILABLE", False)
        with pytest.raises(RuntimeError, match="watchdog"):
            w.FolderWatcher(tmp_path, "film", ENC)

    def test_start_schedules_recursive_and_stop(self, watcher, monkeypatch):
        obs = MagicMock()
        monkeypatch.setattr(w, "Observer", lambda: obs)
        calls = {"n": 0}

        def sleeper(s):
            calls["n"] += 1
            if calls["n"] >= 2:
                watcher.stop()
        monkeypatch.setattr(w.time, "sleep", sleeper)
        watcher.start()
        assert obs.schedule.call_args.kwargs.get("recursive") is True
        obs.start.assert_called_once()
        obs.stop.assert_called_once()

    def test_stop_without_start(self, watcher):
        watcher.stop()  # no observer yet; must not raise
