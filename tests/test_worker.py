"""Unit tests for the GUI BackgroundWorker (tkinter-free)."""

import threading
from unittest.mock import MagicMock, patch

from conftest import make_meta
from mediacrush.core.hardware import EncoderInfo
from mediacrush.core.scanner import CandidateFile, ScanReport
from mediacrush.gui.worker import BackgroundWorker

ENC = EncoderInfo("hevc", "libx265", "CPU", None, "")


def cand(name, saved=100):
    return CandidateFile(make_meta(f"/v/{name}"), "r", 1, saved)


def run_batch(worker, cands, results):
    ev = threading.Event()
    log = {"start": [], "done": [], "total": None}
    worker._engine.transcode = MagicMock(side_effect=results)
    worker.start_batch(
        cands, ENC, "film", True,
        on_file_start=lambda i, n, f: log["start"].append((i, n, f)),
        on_progress=lambda p: None,
        on_file_complete=lambda i, f, ok: log["done"].append((i, f, ok)),
        on_all_complete=lambda s: (log.__setitem__("total", s), ev.set()),
    )
    assert ev.wait(5)
    return log


def test_batch_reports_each_file_and_total():
    log = run_batch(BackgroundWorker(), [cand("a.mkv", 100), cand("b.mkv", 50)], [True, False])
    assert log["start"] == [(1, 2, "a.mkv"), (2, 2, "b.mkv")]
    assert log["done"] == [(1, "a.mkv", True), (2, "b.mkv", False)]
    assert log["total"] == 100  # failed file contributes no savings


def test_not_running_after_completion():
    w = BackgroundWorker()
    run_batch(w, [cand("a.mkv")], [True])
    w._thread.join(2)
    assert w.is_running is False


def test_cancel_stops_batch_and_engine():
    w = BackgroundWorker()
    ev = threading.Event()
    done = []
    first = threading.Event()

    def slow(*a, **k):
        first.set()
        ev.wait(2)
        return True

    w._engine.transcode = MagicMock(side_effect=slow)
    w._engine.cancel = MagicMock()
    fin = threading.Event()
    w.start_batch([cand("a.mkv"), cand("b.mkv")], ENC, "film", True, lambda *a: None, lambda p: None,
                  lambda i, f, ok: done.append(f), lambda s: fin.set())
    first.wait(2)
    w.cancel()
    ev.set()
    assert fin.wait(5)
    assert done == ["a.mkv"]  # second file never started
    w._engine.cancel.assert_called_once()


def test_start_scan_invokes_callback_with_report(tmp_path):
    got = threading.Event()
    box = []
    rep = ScanReport(tmp_path, [], 0, 0, 0)
    with patch("mediacrush.gui.worker.LibraryScanner.scan_path", return_value=rep):
        BackgroundWorker().start_scan(tmp_path, lambda r: (box.append(r), got.set()))
        assert got.wait(5)
    assert box == [rep]
