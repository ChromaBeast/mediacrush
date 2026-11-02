"""Background worker thread for non-blocking GUI execution."""

from pathlib import Path
import threading
from typing import Callable, List, Optional
from mediacrush.core.hardware import EncoderInfo
from mediacrush.core.scanner import CandidateFile, LibraryScanner, ScanReport
from mediacrush.core.transcoder import TranscodeEngine, TranscodeProgress


class BackgroundWorker:
    """Manages asynchronous scans and batch transcoding for the GUI."""

    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._engine = TranscodeEngine()
        self._is_running = False

    @property
    def is_running(self) -> bool:
        return self._is_running

    def cancel(self):
        """Signals active transcode to terminate."""
        self._is_running = False
        self._engine.cancel()

    def start_scan(self, path: Path, on_done: Callable[[ScanReport], None]):
        """Runs library scanning in background."""
        def _target():
            report = LibraryScanner.scan_path(path)
            on_done(report)

        threading.Thread(target=_target, daemon=True).start()

    def start_batch(
        self,
        candidates: List[CandidateFile],
        encoder: EncoderInfo,
        preset_key: str,
        in_place: bool,
        on_file_start: Callable[[int, int, str], None],
        on_progress: Callable[[TranscodeProgress], None],
        on_file_complete: Callable[[int, str, bool], None],
        on_all_complete: Callable[[int], None]
    ):
        """Runs batch compression across candidates in background."""
        self._is_running = True

        def _target():
            total_saved = 0
            for idx, cand in enumerate(candidates, 1):
                if not self._is_running:
                    break

                f_name = cand.metadata.path.name
                on_file_start(idx, len(candidates), f_name)

                success = self._engine.transcode(
                    meta=cand.metadata,
                    encoder=encoder,
                    preset_key=preset_key,
                    in_place=in_place,
                    keep_backup=False,
                    progress_callback=on_progress
                )

                if success:
                    total_saved += cand.potential_savings_bytes

                on_file_complete(idx, f_name, success)

            self._is_running = False
            on_all_complete(total_saved)

        self._thread = threading.Thread(target=_target, daemon=True)
        self._thread.start()
