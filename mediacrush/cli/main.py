"""CLI entrypoint for MediaCrush."""

import argparse
from pathlib import Path
import sys
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from mediacrush.cli.formatters import console, format_bytes, print_banner, print_encoders_table, print_scan_report
from mediacrush.core.hardware import HardwareDetector
from mediacrush.core.scanner import LibraryScanner
from mediacrush.core.transcoder import TranscodeEngine


def cmd_detect(args: argparse.Namespace) -> None:
    """Detects and reports working hardware encoders."""
    print_banner()
    encoders = HardwareDetector.discover_encoders()
    active = HardwareDetector.get_best_encoder()
    print_encoders_table(encoders, active)


def cmd_scan(args: argparse.Namespace) -> None:
    """Scans directory and subfolders, reporting bloat and savings."""
    print_banner()
    target = Path(args.path)
    if not target.exists():
        console.print(f"[bold red]Error:[/bold red] Path not found: {target}")
        sys.exit(1)

    console.print(f"[cyan]Scanning folder & all subfolders:[/cyan] {target} ...")
    report = LibraryScanner.scan_path(target)
    print_scan_report(report)


def cmd_compress(args: argparse.Namespace) -> None:
    """Compresses candidates across folder and all subfolders."""
    print_banner()
    target = Path(args.path)
    if not target.exists():
        console.print(f"[bold red]Error:[/bold red] Path not found: {target}")
        sys.exit(1)

    active_enc = HardwareDetector.get_best_encoder()
    console.print(f"[bold green]Selected Encoder:[/bold green] {active_enc.description}")
    console.print(f"[bold cyan]Scanning:[/bold cyan] {target} (recursive)")

    report = LibraryScanner.scan_path(target)
    if not report.candidates:
        console.print("[green]All files are already optimized! No compression needed.[/green]")
        return

    print_scan_report(report)

    if args.dry_run:
        console.print("\n[yellow]Dry run mode active. No files were modified.[/yellow]")
        return

    in_place = not args.side_by_side
    engine = TranscodeEngine()
    total_saved = 0

    for idx, cand in enumerate(report.candidates, 1):
        f_name = cand.metadata.path.name
        console.print(f"\n[bold cyan][{idx}/{len(report.candidates)}][/bold cyan] Compressing: [white]{f_name}[/white]")

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("• {task.fields[fps]:.0f} fps ({task.fields[speed]:.1f}x)"),
            TimeRemainingColumn(),
            console=console
        ) as prog:
            task = prog.add_task("Optimizing...", total=100, fps=0.0, speed=1.0)

            def on_progress(p):
                prog.update(task, completed=p.percent, fps=p.fps, speed=p.speed_multiplier)

            success = engine.transcode(
                meta=cand.metadata,
                encoder=active_enc,
                preset_key=args.preset,
                in_place=in_place,
                keep_backup=args.keep_backup,
                progress_callback=on_progress
            )

        if success:
            saved = cand.potential_savings_bytes
            total_saved += saved
            console.print(f"[bold green][OK] Completed![/bold green] Saved ~{format_bytes(saved)}")
        else:
            console.print(f"[bold red][FAIL] Failed to optimize {f_name}[/bold red]")

    console.print(f"\n[bold green]Batch complete![/bold green] Total reclaimed space: [bold green]{format_bytes(total_saved)}[/bold green]")


def cmd_gui(args: argparse.Namespace) -> None:
    """Launches the desktop GUI application."""
    from mediacrush.gui.app import launch_gui
    launch_gui()


def main() -> None:
    """Parser routing for all CLI subcommands."""
    parser = argparse.ArgumentParser(prog="mediacrush", description="Universal Media Optimizer")
    subs = parser.add_subparsers(dest="command", required=True)

    subs.add_parser("detect", help="Detect functional hardware encoders")

    scan_p = subs.add_parser("scan", help="Scan a directory and all subfolders")
    scan_p.add_argument("path", type=str, help="Path to video file or folder")

    comp_p = subs.add_parser("compress", help="Compress video files across folder tree")
    comp_p.add_argument("path", type=str, help="Path to video file or folder")
    comp_p.add_argument("--preset", choices=["anime", "film", "saver"], default="anime", help="Optimization preset")
    comp_p.add_argument("--side-by-side", action="store_true", help="Save output as .crushed.mkv rather than replacing")
    comp_p.add_argument("--keep-backup", action="store_true", help="Keep .bak backup copy of original")
    comp_p.add_argument("--dry-run", action="store_true", help="Simulate scan and calculations without writing files")

    subs.add_parser("gui", help="Launch the Desktop GUI application")

    args = parser.parse_args()
    commands = {"detect": cmd_detect, "scan": cmd_scan, "compress": cmd_compress, "gui": cmd_gui}
    commands[args.command](args)


if __name__ == "__main__":
    main()
