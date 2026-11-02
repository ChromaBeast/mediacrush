"""Terminal formatting and Rich console components for MediaCrush."""

from typing import List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from mediacrush.core.hardware import EncoderInfo
from mediacrush.core.scanner import CandidateFile, ScanReport

console = Console()


def format_bytes(size: int) -> str:
    """Converts bytes to human readable format (MB/GB)."""
    if size >= 1024 * 1024 * 1024:
        return f"{size / (1024**3):.2f} GB"
    return f"{size / (1024**2):.1f} MB"


def print_banner() -> None:
    """Prints the application banner."""
    console.print(
        Panel.fit(
            "[bold cyan]MediaCrush[/bold cyan] - [bold white]Universal Media Optimizer[/bold white]\n"
            "[dim]Hardware Accelerated: NVIDIA | AMD | Intel | Qualcomm Snapdragon X | CPU[/dim]",
            border_style="cyan"
        )
    )


def print_encoders_table(encoders: List[EncoderInfo], active: EncoderInfo) -> None:
    """Displays table of available hardware encoders."""
    table = Table(title="Detected Hardware Encoders", border_style="blue")
    table.add_column("Vendor", style="cyan", justify="left")
    table.add_column("Encoder", style="magenta")
    table.add_column("Codec", style="green")
    table.add_column("Status", style="bold")

    for enc in encoders:
        is_active = enc.encoder_name == active.encoder_name
        status = "[bold green]Active (Preferred)[/bold green]" if is_active else "[dim green]Available[/dim green]"
        table.add_row(enc.vendor, enc.encoder_name, enc.codec.upper(), status)

    console.print(table)


def print_scan_report(report: ScanReport) -> None:
    """Displays scan summary and candidate breakdown table."""
    table = Table(title=f"Scan Results for: {report.root_path.name}", border_style="cyan")
    table.add_column("File / Relative Path", style="white")
    table.add_column("Codec", style="magenta")
    table.add_column("Res", style="yellow")
    table.add_column("Current", style="red")
    table.add_column("Estimated", style="green")
    table.add_column("Savings", style="bold green")

    for c in report.candidates:
        rel_path = c.metadata.path.name
        table.add_row(
            rel_path,
            c.metadata.video_codec.upper(),
            c.metadata.resolution_label,
            format_bytes(c.metadata.file_size_bytes),
            format_bytes(c.estimated_size_bytes),
            f"-{c.savings_percent:.1f}% ({format_bytes(c.potential_savings_bytes)})"
        )

    console.print(table)
    console.print(
        f"\n[bold]Found:[/bold] [yellow]{len(report.candidates)}[/yellow] candidate(s) to optimize | "
        f"[dim]Skipped {report.skipped_count} already-efficient files[/dim]\n"
        f"[bold]Total Current Size:[/bold] [red]{format_bytes(report.total_current_bytes)}[/red] -> "
        f"[bold]Estimated New Size:[/bold] [green]{format_bytes(report.total_estimated_bytes)}[/green] "
        f"([bold green]Savings: {format_bytes(report.total_savings_bytes)}[/bold green])"
    )
