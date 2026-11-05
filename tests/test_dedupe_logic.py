"""Unit tests for DuplicateDetector name normalization and clustering (probe mocked)."""

from unittest.mock import patch

import pytest

from conftest import make_meta
from mediacrush.core.deduplicator import DuplicateDetector


def run_find(tmp_path, metas):
    """Creates empty files named after metas and maps probe results by name."""
    by_name = {}
    for m in metas:
        (tmp_path / m.path.name).write_bytes(b"x")
        by_name[m.path.name] = m
    with patch("mediacrush.core.deduplicator.MediaProbe.inspect", side_effect=lambda p: by_name.get(p.name)):
        return DuplicateDetector.find(tmp_path)


class TestNormalize:
    @pytest.mark.parametrize("a,b", [
        ("Movie.1080p.x265.mkv", "movie 720p x264.mkv"),
        ("My_Show-WEB-DL.AAC", "my show"),
    ])
    def test_tags_stripped(self, a, b):
        assert DuplicateDetector._normalize_name(a).split() [:2] == DuplicateDetector._normalize_name(b).split()[:2]

    def test_separators_collapsed(self):
        assert DuplicateDetector._normalize_name("A._-B") == "a b"


class TestFind:
    def test_empty_dir(self, tmp_path):
        assert DuplicateDetector.find(tmp_path) == []

    def test_nonexistent_path(self, tmp_path):
        assert DuplicateDetector.find(tmp_path / "nope") == []

    def test_pair_detected_best_kept(self, tmp_path):
        hi = make_meta("/a/hi.mkv", duration=1400, size_mb=900, width=1920, height=1080)
        lo = make_meta("/a/lo.mkv", duration=1401, size_mb=300, width=1280, height=720)
        groups = run_find(tmp_path, [hi, lo])
        assert len(groups) == 1
        assert groups[0].recommended_keep.path.name == "hi.mkv"
        assert groups[0].removable_size_bytes == lo.file_size_bytes

    def test_same_resolution_largest_kept(self, tmp_path):
        a = make_meta("/a/a.mkv", duration=1400, size_mb=100)
        b = make_meta("/a/b.mkv", duration=1400, size_mb=500)
        g = run_find(tmp_path, [a, b])[0]
        assert g.recommended_keep.path.name == "b.mkv"

    def test_different_durations_not_duplicates(self, tmp_path):
        a = make_meta("/a/a.mkv", duration=1400)
        b = make_meta("/a/b.mkv", duration=2400)
        assert run_find(tmp_path, [a, b]) == []

    def test_short_clips_ignored(self, tmp_path):
        a = make_meta("/a/a.mkv", duration=8)
        b = make_meta("/a/b.mkv", duration=8)
        assert run_find(tmp_path, [a, b]) == []

    def test_unprobeable_files_ignored(self, tmp_path):
        (tmp_path / "bad.mkv").write_bytes(b"x")
        with patch("mediacrush.core.deduplicator.MediaProbe.inspect", return_value=None):
            assert DuplicateDetector.find(tmp_path) == []

    def test_non_video_ignored(self, tmp_path):
        (tmp_path / "notes.txt").write_text("x")
        with patch("mediacrush.core.deduplicator.MediaProbe.inspect") as probe:
            DuplicateDetector.find(tmp_path)
        probe.assert_not_called()

    def test_recurses_into_subfolders(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        a, b = make_meta("/a/a.mkv", duration=1400), make_meta("/a/b.mkv", duration=1400)
        (tmp_path / "a.mkv").write_bytes(b"x")
        (sub / "b.mkv").write_bytes(b"x")
        with patch("mediacrush.core.deduplicator.MediaProbe.inspect",
                   side_effect=lambda p: {"a.mkv": a, "b.mkv": b}[p.name]):
            assert len(DuplicateDetector.find(tmp_path)) == 1

    def test_single_file_target(self, tmp_path):
        f = tmp_path / "a.mkv"
        f.write_bytes(b"x")
        with patch("mediacrush.core.deduplicator.MediaProbe.inspect", return_value=make_meta("/a/a.mkv")):
            assert DuplicateDetector.find(f) == []  # one file cannot duplicate itself

    def test_near_duplicates_across_bucket_boundary(self, tmp_path):
        a = make_meta("/a/a.mkv", duration=1401.9)
        b = make_meta("/a/b.mkv", duration=1402.1)
        assert len(run_find(tmp_path, [a, b])) == 1
