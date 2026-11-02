"""Desktop GUI Application Window for MediaCrush."""

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from mediacrush.cli.formatters import format_bytes
from mediacrush.core.hardware import HardwareDetector
from mediacrush.core.presets import PresetManager
from mediacrush.core.scanner import ScanReport
from mediacrush.gui.components import DarkTheme, StatCard, setup_theme
from mediacrush.gui.worker import BackgroundWorker


class MediaCrushGUI:
    """Main Application Controller for the MediaCrush Desktop UI."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("MediaCrush - Universal Media Optimizer")
        self.root.geometry("960x650")
        self.root.minsize(800, 500)

        setup_theme(self.root)
        self.worker = BackgroundWorker()
        self.active_encoder = HardwareDetector.get_best_encoder()
        self.current_report: ScanReport = None

        self._build_header()
        self._build_stats_row()
        self._build_table()
        self._build_footer()

    def _build_header(self):
        header = ttk.Frame(self.root, padding=15)
        header.pack(fill="x")

        ttk.Label(header, text="MediaCrush", style="Title.TLabel").pack(side="left")
        badge_text = f"Hardware: {self.active_encoder.description}"
        ttk.Label(header, text=badge_text, foreground=DarkTheme.SUCCESS).pack(side="right")

        controls = ttk.Frame(self.root, padding=(15, 0, 15, 10))
        controls.pack(fill="x")

        ttk.Button(controls, text="Select Folder & Subfolders", command=self._pick_folder).pack(side="left", padx=(0, 10))

        ttk.Label(controls, text="Preset:").pack(side="left", padx=(10, 5))
        self.preset_var = tk.StringVar(value="anime")
        p_combo = ttk.Combobox(controls, textvariable=self.preset_var, values=list(PresetManager.PRESETS.keys()), state="readonly", width=10)
        p_combo.pack(side="left", padx=(0, 10))

        self.in_place_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(controls, text="In-place Replacement", variable=self.in_place_var).pack(side="left", padx=10)

    def _build_stats_row(self):
        row = ttk.Frame(self.root, padding=(15, 0, 15, 10))
        row.pack(fill="x")
        self.card_files = StatCard(row, "Candidates", "0")
        self.card_files.pack(side="left", expand=True, fill="x", padx=5)
        self.card_curr = StatCard(row, "Current Size", "0 MB")
        self.card_curr.pack(side="left", expand=True, fill="x", padx=5)
        self.card_est = StatCard(row, "Estimated Size", "0 MB")
        self.card_est.pack(side="left", expand=True, fill="x", padx=5)
        self.card_save = StatCard(row, "Projected Savings", "0 MB")
        self.card_save.pack(side="left", expand=True, fill="x", padx=5)

    def _build_table(self):
        table_frame = ttk.Frame(self.root, padding=(15, 0))
        table_frame.pack(fill="both", expand=True)

        cols = ("file", "codec", "res", "curr", "est", "status")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")
        for col, title, w in [("file", "File Name", 300), ("codec", "Codec", 70), ("res", "Res", 70),
                              ("curr", "Current", 90), ("est", "Est. New", 90), ("status", "Status", 120)]:
            self.tree.heading(col, text=title)
            self.tree.column(col, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True)

    def _build_footer(self):
        footer = ttk.Frame(self.root, padding=15)
        footer.pack(fill="x", side="bottom")

        self.status_label = ttk.Label(footer, text="Select a movie/TV folder to scan...")
        self.status_label.pack(side="left", pady=5)

        self.start_btn = ttk.Button(footer, text="Start Optimization", style="Accent.TButton", command=self._start_batch)
        self.start_btn.pack(side="right", padx=5)

        self.prog_bar = ttk.Progressbar(footer, mode="determinate")
        self.prog_bar.pack(fill="x", padx=(0, 15), pady=5)

    def _pick_folder(self):
        path = filedialog.askdirectory(title="Select Folder to Optimize")
        if not path:
            return
        self.status_label.config(text=f"Scanning {path} and all subfolders...")
        self.tree.delete(*self.tree.get_children())
        self.worker.start_scan(Path(path), self._on_scan_done)

    def _on_scan_done(self, report: ScanReport):
        self.current_report = report
        self.root.after(0, self._render_scan_results, report)

    def _render_scan_results(self, report: ScanReport):
        self.card_files.update_value(str(len(report.candidates)))
        self.card_curr.update_value(format_bytes(report.total_current_bytes))
        self.card_est.update_value(format_bytes(report.total_estimated_bytes))
        self.card_save.update_value(format_bytes(report.total_savings_bytes))

        for cand in report.candidates:
            self.tree.insert("", "end", values=(
                cand.metadata.path.name, cand.metadata.video_codec.upper(),
                cand.metadata.resolution_label, format_bytes(cand.metadata.file_size_bytes),
                format_bytes(cand.estimated_size_bytes), "Ready"
            ))
        self.status_label.config(text=f"Scan complete: {len(report.candidates)} candidate(s) found.")

    def _start_batch(self):
        if not self.current_report or not self.current_report.candidates:
            messagebox.showinfo("No Files", "No candidate files found to optimize.")
            return

        self.start_btn.config(state="disabled")
        self.worker.start_batch(
            candidates=self.current_report.candidates,
            encoder=self.active_encoder,
            preset_key=self.preset_var.get(),
            in_place=self.in_place_var.get(),
            on_file_start=lambda i, tot, name: self.root.after(0, lambda: self.status_label.config(text=f"[{i}/{tot}] Optimizing: {name}")),
            on_progress=lambda p: self.root.after(0, lambda: self.prog_bar.config(value=p.percent)),
            on_file_complete=lambda i, name, ok: None,
            on_all_complete=lambda saved: self.root.after(0, lambda: self._on_batch_complete(saved))
        )

    def _on_batch_complete(self, total_saved: int):
        self.start_btn.config(state="normal")
        self.status_label.config(text=f"Complete! Reclaimed {format_bytes(total_saved)}.")
        messagebox.showinfo("Optimization Complete", f"All files optimized!\nTotal space reclaimed: {format_bytes(total_saved)}")


def launch_gui():
    """Initializes and runs the GUI mainloop."""
    root = tk.Tk()
    app = MediaCrushGUI(root)
    root.mainloop()
