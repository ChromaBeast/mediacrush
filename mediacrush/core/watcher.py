"""Folder watcher for automatic background compression of new files."""

from __future__ import annotations

from pathlib import Path
import time
from typing import Optional

from mediacrush.cli.formatters import console, format_bytes
from mediacrush.core.hardware import EncoderInfo
from mediacrush.core.scanner import LibraryScanner
from mediacrush.core.transcoder import TranscodeEngine

try:
    from watchdog.events import FileSystemEvent, FileSystemEventHandler
    from watchdog.observers import Observer
    _WATCHDOG_AVAILABLE = True
except ImportError:
    _WATCHDOG_AVAILABLE = False
    FileSystemEventHandler = object  # type: ignore
    Observer = None  # type: ignore


class VideoFileHandler(FileSystemEventHandler):
    """Handles file system events and triggers compression on new video files."""

    def __init__(self, watcher: "FolderWatcher") -> None:
        super().__init__()
        self.watcher = watcher
        self._processed = set()

    def on_created(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        self._handle_file(Path(str(event.src_path)))

    def on_moved(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        dest = getattr(event, "dest_path", None)
        if dest:
            self._handle_file(Path(str(dest)))

    def _handle_file(self, path: Path) -> None:
        if path.suffix.lower() not in LibraryScanner.SUPPORTED_EXTS:
            return
        if str(path) in self._processed or ".mediacrush.temp" in path.name:
            return

        # Brief wait to ensure file write is finished
        time.sleep(2.0)
        self._processed.add(str(path))
        self.watcher.process_file(path)


class FolderWatcher:
    """Monitors a directory tree and automatically compresses incoming media."""

    def __init__(self, path: Path, preset: str, encoder: EncoderInfo) -> None:
        if not _WATCHDOG_AVAILABLE:
            raise RuntimeError("watchdog is required for watch mode. Run: pip install watchdog")
        self.path = path.resolve()
        self.preset = preset
        self.encoder = encoder
        self.engine = TranscodeEngine()
        self.observer: Optional[Observer] = None
        self._running = False

    def process_file(self, file_path: Path) -> None:
        """Evaluates and compresses a newly detected file."""
        console.print(f"\n[bold yellow]New file detected:[/bold yellow] {file_path.name}")
        report = LibraryScanner.scan_path(file_path)
        if not report.candidates:
            console.print("[green]File is already optimized. Skipping.[/green]")
            return

        cand = report.candidates[0]
        console.print(f"[cyan]Compressing:[/cyan] {file_path.name} (Preset: {self.preset})")
        ok = self.engine.transcode(
            meta=cand.metadata,
            encoder=self.encoder,
            preset_key=self.preset,
            in_place=True
        )
        if ok:
            console.print(f"[bold green]Optimized:[/bold green] Saved ~{format_bytes(cand.potential_savings_bytes)}")
        else:
            console.print(f"[bold red]Failed to optimize:[/bold red] {file_path.name}")

    def start(self) -> None:
        """Starts monitoring the target folder (blocking loop)."""
        self.observer = Observer()
        handler = VideoFileHandler(self)
        self.observer.schedule(handler, str(self.path), recursive=True)
        self.observer.start()
        self._running = True
        console.print(f"[bold green]Watching directory:[/bold green] {self.path} (Ctrl+C to stop)")
        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self) -> None:
        """Stops the directory watcher."""
        self._running = False
        if self.observer:
            self.observer.stop()
            self.observer.join()
            console.print("\n[yellow]Watch mode stopped.[/yellow]")
