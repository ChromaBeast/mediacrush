"""Integration-style tests for CLI command handlers with core services mocked."""

import argparse
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

from conftest import make_meta
from mediacrush.cli import commands, formatters
from mediacrush.core.deduplicator import DuplicateGroup
from mediacrush.core.hardware import EncoderInfo
from mediacrush.core.scanner import CandidateFile, ScanReport

ENC = EncoderInfo("hevc", "libx265", "CPU", None, "CPU x265")


@pytest.fixture(autouse=True)
def quiet_console(monkeypatch):
    c = Console(record=True, width=200)
    monkeypatch.setattr(commands, "console", c)
    monkeypatch.setattr(formatters, "console", c)
    return c


def cand(path, size_mb=1000, preset=None):
    m = make_meta(str(path), size_mb=size_mb)
    return CandidateFile(m, "r", m.file_size_bytes // 3, m.file_size_bytes * 2 // 3, preset)


def report(tmp_path, cands):
    return ScanReport(tmp_path, cands, 0, sum(c.metadata.file_size_bytes for c in cands),
                      sum(c.estimated_size_bytes for c in cands))


class TestDetect:
    def test_prints_table(self, quiet_console):
        with patch.object(commands.HardwareDetector, "discover_encoders", return_value=[ENC]), \
             patch.object(commands.HardwareDetector, "get_best_encoder", return_value=ENC):
            commands.cmd_detect(argparse.Namespace())
        assert "libx265" in quiet_console.export_text()


class TestScan:
    def test_missing_path_exits_1(self, tmp_path):
        with pytest.raises(SystemExit) as e:
            commands.cmd_scan(argparse.Namespace(path=str(tmp_path / "nope")))
        assert e.value.code == 1

    def test_scan_prints_report(self, tmp_path, quiet_console):
        with patch.object(commands.LibraryScanner, "scan_path", return_value=report(tmp_path, [cand(tmp_path / "a.mkv")])):
            commands.cmd_scan(argparse.Namespace(path=str(tmp_path)))
        assert "a.mkv" in quiet_console.export_text()


class TestCompress:
    def _run(self, tmp_path, args, rep, transcode=True):
        with patch.object(commands.HardwareDetector, "get_best_encoder", return_value=ENC), \
             patch.object(commands.LibraryScanner, "scan_path", return_value=rep), \
             patch.object(commands.TranscodeEngine, "transcode", return_value=transcode) as tc, \
             patch.object(commands.ContentClassifier, "detect") as det:
            det.return_value = MagicMock(preset_key="anime")
            commands.cmd_compress(args)
        return tc, det

    def test_missing_path_exits(self, cli_args, tmp_path):
        with pytest.raises(SystemExit):
            commands.cmd_compress(cli_args(path=str(tmp_path / "nope")))

    def test_nothing_to_do(self, cli_args, tmp_path, quiet_console):
        tc, _ = self._run(tmp_path, cli_args(path=str(tmp_path)), report(tmp_path, []))
        tc.assert_not_called()
        assert "already optimized" in quiet_console.export_text()

    def test_dry_run_never_transcodes(self, cli_args, tmp_path):
        tc, _ = self._run(tmp_path, cli_args(path=str(tmp_path), dry_run=True), report(tmp_path, [cand(tmp_path / "a.mkv")]))
        tc.assert_not_called()

    def test_auto_preset_uses_classifier(self, cli_args, tmp_path):
        tc, det = self._run(tmp_path, cli_args(path=str(tmp_path)), report(tmp_path, [cand(tmp_path / "a.mkv")]))
        det.assert_called_once()
        assert tc.call_args.kwargs["preset_key"] == "anime"

    def test_explicit_preset_skips_classifier(self, cli_args, tmp_path):
        tc, det = self._run(tmp_path, cli_args(path=str(tmp_path), preset="saver"), report(tmp_path, [cand(tmp_path / "a.mkv")]))
        det.assert_not_called()
        assert tc.call_args.kwargs["preset_key"] == "saver"

    def test_folder_override_wins(self, cli_args, tmp_path):
        tc, det = self._run(tmp_path, cli_args(path=str(tmp_path), preset="saver"),
                            report(tmp_path, [cand(tmp_path / "a.mkv", preset="film")]))
        assert tc.call_args.kwargs["preset_key"] == "film"
        det.assert_not_called()

    def test_side_by_side_flag(self, cli_args, tmp_path):
        tc, _ = self._run(tmp_path, cli_args(path=str(tmp_path), preset="film", side_by_side=True),
                          report(tmp_path, [cand(tmp_path / "a.mkv")]))
        assert tc.call_args.kwargs["in_place"] is False

    def test_failure_is_reported_not_raised(self, cli_args, tmp_path, quiet_console):
        self._run(tmp_path, cli_args(path=str(tmp_path), preset="film"), report(tmp_path, [cand(tmp_path / "a.mkv")]), transcode=False)
        assert "Failed" in quiet_console.export_text()

    def test_processes_every_candidate(self, cli_args, tmp_path):
        cs = [cand(tmp_path / f"{i}.mkv") for i in range(3)]
        tc, _ = self._run(tmp_path, cli_args(path=str(tmp_path), preset="film"), report(tmp_path, cs))
        assert tc.call_count == 3


class TestPauseQueue:
    def test_pause_queues_remaining(self, cli_args, tmp_path):
        qfile = tmp_path / "q.json"
        cs = [cand(tmp_path / f"{i}.mkv") for i in range(3)]
        from mediacrush.core.queue import JobQueue
        with patch.object(commands, "JobQueue", side_effect=lambda: JobQueue(qfile)), \
             patch.object(commands.TranscodeEngine, "transcode", return_value=True) as tc:
            commands._execute_compression_batch(cs, ENC, cli_args(preset="film", pause=True))
        assert tc.call_count == 1
        saved = json.loads(qfile.read_text())
        assert [Path(e["path"]).name for e in saved] == ["1.mkv", "2.mkv"]
        assert all(e["status"] == "pending" and e["preset"] == "film" for e in saved)


class TestReports:
    def _batch(self, tmp_path, cli_args, name):
        rp = tmp_path / name
        with patch.object(commands.TranscodeEngine, "transcode", return_value=True):
            commands._execute_compression_batch([cand(tmp_path / "a.mkv")], ENC, cli_args(preset="film", report=str(rp)))
        return rp

    def test_html_report(self, tmp_path, cli_args):
        rp = self._batch(tmp_path, cli_args, "r.html")
        assert "<html" in rp.read_text(encoding="utf-8")

    def test_json_report_is_json(self, tmp_path, cli_args):
        rp = self._batch(tmp_path, cli_args, "r.json")
        json.loads(rp.read_text(encoding="utf-8"))


class TestQualityCheck:
    def _run(self, tmp_path, cli_args, **flags):
        f = tmp_path / "a.mkv"
        f.write_bytes(b"x")
        with patch.object(commands.TranscodeEngine, "transcode", return_value=True), \
             patch.object(commands.QualityChecker, "score", return_value=None) as sc:
            commands._execute_compression_batch([cand(f)], ENC, cli_args(preset="film", quality_check=True, **flags))
        return f, sc

    def test_side_by_side_compares_source_to_crushed(self, tmp_path, cli_args):
        f, sc = self._run(tmp_path, cli_args, side_by_side=True)
        sc.assert_called_once_with(f, f.with_name("a.crushed.mkv"))

    def test_in_place_with_backup_compares_backup_to_output(self, tmp_path, cli_args):
        f, sc = self._run(tmp_path, cli_args, keep_backup=True)
        sc.assert_called_once_with(f.with_name("a.mkv.bak"), f)

    def test_in_place_without_backup_skips_check(self, tmp_path, cli_args, quiet_console):
        _, sc = self._run(tmp_path, cli_args)
        sc.assert_not_called()
        assert "Quality check skipped" in quiet_console.export_text()


class TestResume:
    def test_empty_queue(self, quiet_console, tmp_path):
        with patch.object(commands, "JobQueue") as JQ:
            JQ.return_value.load.return_value = []
            commands.cmd_resume(argparse.Namespace())
        assert "No pending jobs" in quiet_console.export_text()

    def test_marks_done_and_failed(self, tmp_path):
        from mediacrush.core.queue import QueueEntry
        entries = [QueueEntry(str(tmp_path / "ok.mkv"), "film", True, "pending"),
                   QueueEntry(str(tmp_path / "bad.mkv"), "film", True, "pending"),
                   QueueEntry(str(tmp_path / "old.mkv"), "film", True, "done")]
        rep = lambda p: report(tmp_path, [cand(p)])
        with patch.object(commands, "JobQueue") as JQ, \
             patch.object(commands.HardwareDetector, "get_best_encoder", return_value=ENC), \
             patch.object(commands.LibraryScanner, "scan_path", side_effect=rep), \
             patch.object(commands.TranscodeEngine, "transcode", side_effect=[True, False]):
            JQ.return_value.load.return_value = entries
            commands.cmd_resume(argparse.Namespace())
            q = JQ.return_value
        q.mark_done.assert_called_once_with(str(tmp_path / "ok.mkv"))
        q.mark_failed.assert_called_once_with(str(tmp_path / "bad.mkv"))


class TestFindDupes:
    def test_none_found(self, quiet_console, tmp_path):
        with patch.object(commands.DuplicateDetector, "find", return_value=[]):
            commands.cmd_find_dupes(argparse.Namespace(path=str(tmp_path)))
        assert "No duplicate" in quiet_console.export_text()

    def test_prints_clusters(self, quiet_console, tmp_path):
        keep, dup = make_meta("/l/keep.mkv", size_mb=900), make_meta("/l/dup.mkv", size_mb=300)
        g = DuplicateGroup([keep, dup], keep, dup.file_size_bytes)
        with patch.object(commands.DuplicateDetector, "find", return_value=[g]):
            commands.cmd_find_dupes(argparse.Namespace(path=str(tmp_path)))
        t = quiet_console.export_text()
        assert "keep.mkv" in t and "dup.mkv" in t and "Total reclaimable" in t


class TestWatchAndGui:
    def test_watch_starts_watcher(self, tmp_path):
        with patch.object(commands.HardwareDetector, "get_best_encoder", return_value=ENC), \
             patch.object(commands, "FolderWatcher") as FW:
            commands.cmd_watch(argparse.Namespace(path=str(tmp_path), preset="film"))
        FW.assert_called_once_with(Path(tmp_path), "film", ENC)
        FW.return_value.start.assert_called_once()
