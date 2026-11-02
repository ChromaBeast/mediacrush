"""CLI entrypoint and argument parser for MediaCrush."""

import argparse
from mediacrush.cli.commands import (
    cmd_compress,
    cmd_detect,
    cmd_find_dupes,
    cmd_gui,
    cmd_resume,
    cmd_scan,
    cmd_watch,
)


def build_parser() -> argparse.ArgumentParser:
    """Configures the top-level argument parser and subcommands."""
    parser = argparse.ArgumentParser(prog="mediacrush", description="Universal Media Optimizer")
    subs = parser.add_subparsers(dest="command", required=True)

    subs.add_parser("detect", help="Detect functional hardware encoders")

    scan_p = subs.add_parser("scan", help="Scan a directory and all subfolders")
    scan_p.add_argument("path", type=str, help="Path to video file or folder")

    comp_p = subs.add_parser("compress", help="Compress video files across folder tree")
    comp_p.add_argument("path", type=str, help="Path to video file or folder")
    comp_p.add_argument(
        "--preset",
        choices=["auto", "anime", "film", "saver"],
        default="auto",
        help="Optimization preset (default: auto)",
    )
    comp_p.add_argument("--side-by-side", action="store_true", help="Save output as .crushed.mkv")
    comp_p.add_argument("--keep-backup", action="store_true", help="Keep .bak backup copy of original")
    comp_p.add_argument("--dry-run", action="store_true", help="Simulate scan without modifying files")
    comp_p.add_argument("--report", type=str, default=None, help="Generate HTML or JSON report file")
    comp_p.add_argument("--pause", action="store_true", help="Pause batch and push remaining to queue")
    comp_p.add_argument("--quality-check", action="store_true", help="Verify output fidelity via VMAF & SSIM")

    watch_p = subs.add_parser("watch", help="Monitor folder and compress incoming media")
    watch_p.add_argument("path", type=str, help="Folder to monitor")
    watch_p.add_argument("--preset", choices=["anime", "film", "saver"], default="anime", help="Preset to use")

    subs.add_parser("resume", help="Resume interrupted compression queue")

    dupe_p = subs.add_parser("find-dupes", help="Detect duplicate video files across library")
    dupe_p.add_argument("path", type=str, help="Path to library directory")
    dupe_p.add_argument("--report", type=str, default=None, help="Export cleanup report to file")

    subs.add_parser("gui", help="Launch the Desktop GUI application")
    return parser


def main() -> None:
    """Parser routing for all CLI subcommands."""
    parser = build_parser()
    args = parser.parse_args()

    commands = {
        "detect": cmd_detect,
        "scan": cmd_scan,
        "compress": cmd_compress,
        "watch": cmd_watch,
        "resume": cmd_resume,
        "find-dupes": cmd_find_dupes,
        "gui": cmd_gui,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
