"""Additional JobQueue tests: persistence across instances and corrupt-file recovery."""

import json

import pytest

from mediacrush.core.queue import JobQueue, QueueEntry


def e(path, status="pending"):
    return QueueEntry(path, "anime", True, status)


@pytest.fixture
def qfile(tmp_path):
    return tmp_path / "nested" / "queue.json"


def test_missing_file_loads_empty(qfile):
    assert JobQueue(qfile).load() == []


def test_push_creates_parent_dirs(qfile):
    JobQueue(qfile).push(e("/a"))
    assert qfile.exists()


def test_persists_across_instances(qfile):
    JobQueue(qfile).push(e("/a"))
    q2 = JobQueue(qfile)
    assert [x.path for x in q2.load()] == ["/a"]


def test_corrupt_json_recovers_empty(qfile):
    qfile.parent.mkdir(parents=True)
    qfile.write_text("{{{")
    assert JobQueue(qfile).load() == []


def test_unexpected_schema_recovers_empty(qfile):
    qfile.parent.mkdir(parents=True)
    qfile.write_text(json.dumps([{"unknown": 1}]))
    assert JobQueue(qfile).load() == []


def test_status_transitions_persist(qfile):
    q = JobQueue(qfile)
    for p in ("/a", "/b", "/c"):
        q.push(e(p))
    q.mark_done("/a")
    q.mark_failed("/b")
    q2 = JobQueue(qfile)
    q2.load()
    assert [x.path for x in q2.pending()] == ["/c"]
    assert {x.path: x.status for x in q2.load()} == {"/a": "done", "/b": "failed", "/c": "pending"}


def test_mark_unknown_path_is_noop(qfile):
    q = JobQueue(qfile)
    q.push(e("/a"))
    q.mark_done("/zzz")
    assert q.pending()[0].path == "/a"


def test_clear_done_keeps_failed_and_pending(qfile):
    q = JobQueue(qfile)
    q.push(e("/a", "done"))
    q.push(e("/b", "failed"))
    q.push(e("/c"))
    q.clear_done()
    q2 = JobQueue(qfile)
    assert sorted(x.path for x in q2.load()) == ["/b", "/c"]


def test_default_queue_file_under_home():
    from mediacrush.core import queue as qm
    assert qm._QUEUE_FILE.name == "queue.json" and qm._QUEUE_FILE.parent.name == ".mediacrush"
