"""Unit tests for ContentClassifier PPM analysis and detect() control flow."""

import random
from unittest.mock import patch

import pytest

from mediacrush.core.content_classifier import ContentClassifier, ContentType


def write_ppm(path, w, h, pixel_fn, maxval=255, magic=b"P6", comment=False):
    body = bytearray()
    for i in range(w * h):
        body += bytes(pixel_fn(i))
    hdr = magic + b"\n" + (b"# c\n" if comment else b"") + f"{w} {h}\n{maxval}\n".encode()
    path.write_bytes(hdr + bytes(body))
    return path


class TestAnalyzePpm:
    def test_flat_color_is_one_color(self, tmp_path):
        p = write_ppm(tmp_path / "a.ppm", 64, 64, lambda i: (10, 20, 30))
        assert ContentClassifier._analyze_frame_ppm(p) == pytest.approx(1 / 4096)

    def test_noise_has_high_ratio(self, tmp_path):
        rnd = random.Random(1)
        p = write_ppm(tmp_path / "n.ppm", 320, 180, lambda i: (rnd.randrange(256),) * 3 if False else (rnd.randrange(256), rnd.randrange(256), rnd.randrange(256)))
        assert ContentClassifier._analyze_frame_ppm(p) > 0.5

    def test_quantization_merges_close_colors(self, tmp_path):
        p = write_ppm(tmp_path / "q.ppm", 4, 4, lambda i: (16 + (i % 15), 0, 0))  # all share top nibble 1
        assert ContentClassifier._analyze_frame_ppm(p) == pytest.approx(1 / 4096)

    def test_comment_line_skipped(self, tmp_path):
        p = write_ppm(tmp_path / "c.ppm", 2, 2, lambda i: (0, 0, 0), comment=True)
        assert ContentClassifier._analyze_frame_ppm(p) is not None

    def test_wrong_magic(self, tmp_path):
        p = write_ppm(tmp_path / "b.ppm", 2, 2, lambda i: (0, 0, 0), magic=b"P3")
        assert ContentClassifier._analyze_frame_ppm(p) is None

    def test_wrong_maxval(self, tmp_path):
        p = write_ppm(tmp_path / "m.ppm", 2, 2, lambda i: (0, 0, 0), maxval=65535)
        assert ContentClassifier._analyze_frame_ppm(p) is None

    def test_truncated_data(self, tmp_path):
        p = tmp_path / "t.ppm"
        p.write_bytes(b"P6\n10 10\n255\n" + b"\0" * 5)
        assert ContentClassifier._analyze_frame_ppm(p) is None

    def test_missing_file(self, tmp_path):
        assert ContentClassifier._analyze_frame_ppm(tmp_path / "none.ppm") is None

    def test_garbage_header(self, tmp_path):
        p = tmp_path / "g.ppm"
        p.write_bytes(b"P6\nabc def\n255\n")
        assert ContentClassifier._analyze_frame_ppm(p) is None


class TestDetect:
    def test_missing_file_unknown(self, tmp_path):
        assert ContentClassifier.detect(tmp_path / "x.mkv") == ContentType.UNKNOWN

    def test_exception_returns_unknown(self, tmp_path):
        f = tmp_path / "x.mkv"
        f.write_bytes(b"1")
        with patch("mediacrush.core.content_classifier.subprocess.run", side_effect=OSError):
            assert ContentClassifier.detect(f) == ContentType.UNKNOWN

    def test_no_frames_unknown(self, tmp_path):
        f = tmp_path / "x.mkv"
        f.write_bytes(b"1")
        with patch("mediacrush.core.content_classifier.subprocess.run"):
            assert ContentClassifier.detect(f) == ContentType.UNKNOWN

    @pytest.mark.parametrize("ratio,expected", [(0.05, ContentType.ANIME), (0.17, ContentType.ANIME),
                                                (0.18, ContentType.LIVE_ACTION), (0.6, ContentType.LIVE_ACTION)])
    def test_threshold(self, tmp_path, ratio, expected):
        f = tmp_path / "x.mkv"
        f.write_bytes(b"1")

        def fake_run(cmd, **kw):
            from pathlib import Path
            Path(cmd[-1].replace("%02d", "01")).write_bytes(b"")

        with patch("mediacrush.core.content_classifier.subprocess.run", side_effect=fake_run), \
             patch.object(ContentClassifier, "_analyze_frame_ppm", return_value=ratio):
            assert ContentClassifier.detect(f) == expected

    def test_all_frames_unparsable_unknown(self, tmp_path):
        f = tmp_path / "x.mkv"
        f.write_bytes(b"1")

        def fake_run(cmd, **kw):
            from pathlib import Path
            Path(cmd[-1].replace("%02d", "01")).write_bytes(b"")

        with patch("mediacrush.core.content_classifier.subprocess.run", side_effect=fake_run), \
             patch.object(ContentClassifier, "_analyze_frame_ppm", return_value=None):
            assert ContentClassifier.detect(f) == ContentType.UNKNOWN


class TestContentTypeEnum:
    def test_values_are_valid_preset_keys(self):
        from mediacrush.core.presets import PresetManager
        for t in ContentType:
            assert t.preset_key in PresetManager.PRESETS

    def test_unknown_maps_to_film_preset(self):
        assert ContentType.UNKNOWN.preset_key == "film"
        assert ContentType.LIVE_ACTION.preset_key == "film"
        assert ContentType.ANIME.preset_key == "anime"

    def test_unknown_is_distinct_member(self):
        assert ContentType.UNKNOWN is not ContentType.LIVE_ACTION
