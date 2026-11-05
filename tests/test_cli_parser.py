"""Unit tests for the argparse CLI surface and main() routing."""

import pytest

from mediacrush.cli import main as cli_main
from mediacrush.cli.main import build_parser


@pytest.fixture
def parser():
    return build_parser()


class TestParser:
    def test_command_required(self, parser):
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_unknown_command(self, parser):
        with pytest.raises(SystemExit):
            parser.parse_args(["explode"])

    def test_compress_defaults(self, parser):
        a = parser.parse_args(["compress", "/x"])
        assert (a.preset, a.side_by_side, a.keep_backup, a.dry_run, a.report, a.pause, a.quality_check) == \
               ("auto", False, False, False, None, False, False)

    def test_compress_all_flags(self, parser):
        a = parser.parse_args(["compress", "/x", "--preset", "saver", "--side-by-side", "--keep-backup",
                               "--dry-run", "--report", "r.json", "--pause", "--quality-check"])
        assert a.preset == "saver" and a.side_by_side and a.keep_backup and a.dry_run
        assert a.report == "r.json" and a.pause and a.quality_check

    def test_compress_rejects_bad_preset(self, parser):
        with pytest.raises(SystemExit):
            parser.parse_args(["compress", "/x", "--preset", "ultra"])

    def test_compress_requires_path(self, parser):
        with pytest.raises(SystemExit):
            parser.parse_args(["compress"])

    def test_watch_default_and_no_auto(self, parser):
        assert parser.parse_args(["watch", "/x"]).preset == "anime"
        with pytest.raises(SystemExit):
            parser.parse_args(["watch", "/x", "--preset", "auto"])

    @pytest.mark.parametrize("cmd", ["detect", "resume", "gui"])
    def test_no_arg_commands(self, parser, cmd):
        assert parser.parse_args([cmd]).command == cmd

    def test_find_dupes(self, parser):
        a = parser.parse_args(["find-dupes", "/lib", "--report", "o.html"])
        assert a.path == "/lib" and a.report == "o.html"


class TestMainRouting:
    @pytest.mark.parametrize("argv,name", [
        (["detect"], "cmd_detect"), (["scan", "/x"], "cmd_scan"), (["compress", "/x"], "cmd_compress"),
        (["watch", "/x"], "cmd_watch"), (["resume"], "cmd_resume"),
        (["find-dupes", "/x"], "cmd_find_dupes"), (["gui"], "cmd_gui"),
    ])
    def test_dispatch(self, monkeypatch, argv, name):
        called = []
        monkeypatch.setattr(cli_main, name, lambda args: called.append(args.command))
        monkeypatch.setattr("sys.argv", ["mediacrush"] + argv)
        cli_main.main()
        assert called == [argv[0]]
