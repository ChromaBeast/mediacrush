"""CLI Command execution handlers for MediaCrush."""

import argparse
from pathlib import Path
import sys
import time
from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn
from rich.table import Table

from mediacrush.cli.formatters import console, format_bytes, print_banner, print_encoders_table, print_scan_report
from mediacrush.core.content_classifier import ContentClassifier
from mediacrush.core.deduplicator import DuplicateDetector
from mediacrush.core.hardware import HardwareDetector
from mediacrush.core.quality import QualityChecker
from mediacrush.core.queue import JobQueue, QueueEntry
from mediacrush.core.reporter import CompressionReporter
from mediacrush.core.safety import SafetyManager
from mediacrush.core.scanner import LibraryScanner
from mediacrush.core.transcoder import TranscodeEngine
from mediacrush.core.watcher import FolderWatcher


def cmd_detect(args: argparse.Namespace) -> None:
    print_banner()
    encoders = HardwareDetector.discover_encoders()
    active = HardwareDetector.get_best_encoder()
    print_encoders_table(encoders, active)


def cmd_scan(args: argparse.Namespace) -> None:
    print_banner()
    target = Path(args.path)
    if not target.exists():
        console.print(f"[bold red]Error:[/bold red] Path not found: {target}")
        sys.exit(1)
    console.print(f"[cyan]Scanning folder & all subfolders:[/cyan] {target} ...")
    report = LibraryScanner.scan_path(target)
    print_scan_report(report)


def cmd_compress(args: argparse.Namespace) -> None:
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

    _execute_compression_batch(report.candidates, active_enc, args)


def _execute_compression_batch(candidates, active_enc, args) -> None:
    in_place = not args.side_by_side
    engine = TranscodeEngine()
    reporter = CompressionReporter() if args.report else None
    queue = JobQueue() if args.pause else None
    total_saved = 0

    for idx, cand in enumerate(candidates, 1):
        f_path = cand.metadata.path
        preset = cand.local_preset or (
            ContentClassifier.detect(f_path).preset_key if args.preset == "auto" else args.preset
        )
        console.print(f"\n[bold cyan][{idx}/{len(candidates)}][/bold cyan] Compressing: [white]{f_path.name}[/white] [dim]({preset})[/dim]")

        t0 = time.time()
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("• {task.fields[fps]:.0f} fps ({task.fields[speed]:.1f}x)"),
            TimeRemainingColumn(),
            console=console
        ) as prog:
            task = prog.add_task("Optimizing...", total=100, fps=0.0, speed=1.0)
            success = engine.transcode(
                meta=cand.metadata,
                encoder=active_enc,
                preset_key=preset,
                in_place=in_place,
                keep_backup=args.keep_backup,
                progress_callback=lambda p: prog.update(task, completed=p.percent, fps=p.fps, speed=p.speed_multiplier)
            )

        duration = time.time() - t0
        final_size = f_path.stat().st_size if f_path.exists() else cand.estimated_size_bytes
        if reporter:
            reporter.add_result(f_path.name, cand.metadata.file_size_bytes, final_size, active_enc.encoder_name, duration, success)

        if success:
            saved = max(0, cand.metadata.file_size_bytes - final_size)
            total_saved += saved
            console.print(f"[bold green][OK] Completed![/bold green] Saved ~{format_bytes(saved)}")

            if args.quality_check:
                # The source is replaced in place, so compare against the .crushed copy
                # (side-by-side) or the .bak backup; otherwise there is nothing to compare.
                if in_place:
                    original = f_path.with_name(f"{f_path.name}.bak") if args.keep_backup else None
                    encoded = f_path
                else:
                    original = f_path
                    encoded = SafetyManager.get_output_path(f_path, False)
                score = QualityChecker.score(original, encoded) if original else None
                if score:
                    console.print(f"[magenta]Quality:[/magenta] VMAF: {score.vmaf} | SSIM: {score.ssim} ({score.verdict})")
                elif original is None:
                    console.print("[dim]Quality check skipped: use --side-by-side or --keep-backup to keep the original.[/dim]")
        else:
            console.print(f"[bold red][FAIL] Failed to optimize {f_path.name}[/bold red]")

        if args.pause and queue and idx < len(candidates):
            for remaining in candidates[idx:]:
                queue.push(QueueEntry(str(remaining.metadata.path), preset, in_place, "pending"))
            console.print(f"[yellow]Batch paused. Queued {len(candidates) - idx} remaining jobs.[/yellow]")
            break

    if reporter and args.report:
        rep_p = Path(args.report)
        if rep_p.suffix.lower() == ".json":
            reporter.write_json(rep_p)
        else:
            reporter.write_html(rep_p)
        console.print(f"[cyan]Report written to:[/cyan] {rep_p}")
    console.print(f"\n[bold green]Batch complete![/bold green] Total reclaimed space: [bold green]{format_bytes(total_saved)}[/bold green]")


def cmd_watch(args: argparse.Namespace) -> None:
    print_banner()
    active_enc = HardwareDetector.get_best_encoder()
    watcher = FolderWatcher(Path(args.path), args.preset, active_enc)
    watcher.start()


def cmd_resume(args: argparse.Namespace) -> None:
    print_banner()
    queue = JobQueue()
    pending = queue.load()
    pending = [e for e in pending if e.status == "pending"]
    if not pending:
        console.print("[green]No pending jobs in queue.[/green]")
        return
    console.print(f"[bold cyan]Resuming {len(pending)} queued job(s)...[/bold cyan]")
    engine = TranscodeEngine()
    active_enc = HardwareDetector.get_best_encoder()
    for e in pending:
        p = Path(e.path)
        meta = LibraryScanner.scan_path(p)
        if meta.candidates:
            ok = engine.transcode(meta.candidates[0].metadata, active_enc, e.preset, e.in_place)
            queue.mark_done(e.path) if ok else queue.mark_failed(e.path)


def cmd_find_dupes(args: argparse.Namespace) -> None:
    print_banner()
    groups = DuplicateDetector.find(Path(args.path))
    if not groups:
        console.print("[green]No duplicate video files found.[/green]")
        return
    table = Table(title="Duplicate Media Clusters", border_style="cyan")
    table.add_column("Keep (Best)", style="green")
    table.add_column("Duplicate Copies", style="yellow")
    table.add_column("Potential Savings", style="bold green")
    total_reclaimable = 0
    for g in groups:
        dupe_names = "\n".join(f"{f.path.name} ({f.resolution_label})" for f in g.files if f != g.recommended_keep)
        table.add_row(f"{g.recommended_keep.path.name} ({g.recommended_keep.resolution_label})", dupe_names, format_bytes(g.removable_size_bytes))
        total_reclaimable += g.removable_size_bytes
    console.print(table)
    console.print(f"[bold green]Total reclaimable space:[/bold green] {format_bytes(total_reclaimable)}")


def cmd_gui(args: argparse.Namespace) -> None:
    from mediacrush.gui.app import launch_gui
    launch_gui()
