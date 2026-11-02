"""Post-batch compression report generator (HTML + JSON)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List


@dataclass
class ReportEntry:
    """Result of a single file compression."""
    file: str
    original_bytes: int
    final_bytes: int
    encoder: str
    duration_s: float
    success: bool

    @property
    def savings_pct(self) -> float:
        if self.original_bytes == 0:
            return 0.0
        return max(0.0, (1 - self.final_bytes / self.original_bytes) * 100)


class CompressionReporter:
    """Accumulates per-file results and renders HTML/JSON reports."""

    def __init__(self) -> None:
        self._entries: List[ReportEntry] = []

    def add_result(
        self,
        file: str,
        original_bytes: int,
        final_bytes: int,
        encoder: str,
        duration_s: float,
        success: bool,
    ) -> None:
        """Appends a single file result."""
        self._entries.append(ReportEntry(file, original_bytes, final_bytes, encoder, duration_s, success))

    def write_json(self, output_path: Path) -> None:
        """Writes results to a JSON file."""
        output_path.write_text(
            json.dumps([asdict(e) for e in self._entries], indent=2),
            encoding="utf-8"
        )

    def write_html(self, output_path: Path) -> None:
        """Writes a self-contained HTML report with savings table."""
        rows = "".join(self._build_row(e) for e in self._entries)
        total_orig = sum(e.original_bytes for e in self._entries)
        total_final = sum(e.final_bytes for e in self._entries)
        total_saved = max(0, total_orig - total_final)
        overall_pct = (total_saved / total_orig * 100) if total_orig else 0.0

        html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>MediaCrush Report</title>
<style>
  body{{font-family:system-ui,sans-serif;margin:2rem;background:#111;color:#eee}}
  h1{{color:#7cf}}
  table{{border-collapse:collapse;width:100%;margin-top:1rem}}
  th,td{{padding:.5rem 1rem;border:1px solid #333;text-align:left}}
  th{{background:#222}} tr:nth-child(even){{background:#1a1a1a}}
  .ok{{color:#4f4}} .fail{{color:#f44}} .summary{{margin-top:1rem;color:#7cf}}
</style></head><body>
<h1>MediaCrush Compression Report</h1>
<table>
<tr><th>File</th><th>Original</th><th>Final</th><th>Saved %</th><th>Encoder</th><th>Time (s)</th><th>Status</th></tr>
{rows}
</table>
<p class="summary">Total saved: {self._fmt(total_saved)} / {self._fmt(total_orig)} ({overall_pct:.1f}%)</p>
</body></html>"""
        output_path.write_text(html, encoding="utf-8")

    @staticmethod
    def _fmt(b: int) -> str:
        for unit in ("B", "KB", "MB", "GB"):
            if b < 1024:
                return f"{b:.1f} {unit}"
            b //= 1024
        return f"{b:.1f} TB"

    @staticmethod
    def _build_row(e: ReportEntry) -> str:
        status = '<span class="ok">✓</span>' if e.success else '<span class="fail">✗</span>'
        orig = CompressionReporter._fmt(e.original_bytes)
        final = CompressionReporter._fmt(e.final_bytes)
        return (
            f"<tr><td>{e.file}</td><td>{orig}</td><td>{final}</td>"
            f"<td>{e.savings_pct:.1f}%</td><td>{e.encoder}</td>"
            f"<td>{e.duration_s:.1f}</td><td>{status}</td></tr>\n"
        )
