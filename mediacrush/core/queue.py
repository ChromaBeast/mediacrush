"""Persistent job queue stored in ~/.mediacrush/queue.json."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List

_QUEUE_FILE = Path.home() / ".mediacrush" / "queue.json"


@dataclass
class QueueEntry:
    """A single queued compression job."""
    path: str
    preset: str
    in_place: bool
    status: str  # "pending" | "done" | "failed"


class JobQueue:
    """Persistent job queue backed by ~/.mediacrush/queue.json."""

    def __init__(self, queue_file: Path = _QUEUE_FILE) -> None:
        self._file = queue_file
        self._entries: List[QueueEntry] = []

    def load(self) -> List[QueueEntry]:
        """Loads entries from disk. Returns empty list if file missing."""
        if not self._file.exists():
            self._entries = []
            return self._entries
        try:
            raw = json.loads(self._file.read_text(encoding="utf-8"))
            self._entries = [QueueEntry(**item) for item in raw]
        except Exception:
            self._entries = []
        return self._entries

    def save(self) -> None:
        """Persists current entries to disk."""
        self._file.parent.mkdir(parents=True, exist_ok=True)
        self._file.write_text(
            json.dumps([asdict(e) for e in self._entries], indent=2),
            encoding="utf-8"
        )

    def push(self, entry: QueueEntry) -> None:
        """Appends a new entry and saves immediately."""
        self._entries.append(entry)
        self.save()

    def _update_status(self, path: str, status: str) -> None:
        for e in self._entries:
            if e.path == path:
                e.status = status
        self.save()

    def mark_done(self, path: str) -> None:
        """Marks a job as done and persists."""
        self._update_status(path, "done")

    def mark_failed(self, path: str) -> None:
        """Marks a job as failed and persists."""
        self._update_status(path, "failed")

    def pending(self) -> List[QueueEntry]:
        """Returns all entries with status 'pending'."""
        return [e for e in self._entries if e.status == "pending"]

    def clear_done(self) -> None:
        """Removes all completed entries and saves."""
        self._entries = [e for e in self._entries if e.status != "done"]
        self.save()
