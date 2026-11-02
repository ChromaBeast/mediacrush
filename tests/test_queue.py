"""Unit tests for JobQueue persistence and state transitions."""

import tempfile
import unittest
from pathlib import Path
from mediacrush.core.queue import JobQueue, QueueEntry


class TestJobQueue(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False)
        self.tmp.close()
        self.queue_file = Path(self.tmp.name)
        self.queue = JobQueue(self.queue_file)

    def tearDown(self):
        if self.queue_file.exists():
            self.queue_file.unlink()

    def test_empty_load(self):
        """Empty queue file should return empty list."""
        entries = self.queue.load()
        self.assertEqual(entries, [])

    def test_push_and_pending(self):
        """Pushed items should appear in pending list."""
        entry = QueueEntry(path="/path/test.mkv", preset="anime", in_place=True, status="pending")
        self.queue.push(entry)
        pending = self.queue.pending()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].path, "/path/test.mkv")

    def test_mark_done_and_failed(self):
        """mark_done updates status to done and removes from pending."""
        self.queue.push(QueueEntry(path="/path/1.mkv", preset="anime", in_place=True, status="pending"))
        self.queue.push(QueueEntry(path="/path/2.mkv", preset="film", in_place=False, status="pending"))

        self.queue.mark_done("/path/1.mkv")
        self.queue.mark_failed("/path/2.mkv")

        pending = self.queue.pending()
        self.assertEqual(len(pending), 0)

        # Reload from disk
        reloaded = JobQueue(self.queue_file).load()
        self.assertEqual(reloaded[0].status, "done")
        self.assertEqual(reloaded[1].status, "failed")

    def test_clear_done(self):
        """clear_done removes completed entries from disk."""
        self.queue.push(QueueEntry(path="/path/done.mkv", preset="anime", in_place=True, status="done"))
        self.queue.push(QueueEntry(path="/path/pending.mkv", preset="anime", in_place=True, status="pending"))
        self.queue.clear_done()

        remaining = self.queue.load()
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0].path, "/path/pending.mkv")


if __name__ == "__main__":
    unittest.main()
