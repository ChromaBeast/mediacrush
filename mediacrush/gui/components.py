"""Custom dark-themed GUI widgets and styling for MediaCrush."""

import tkinter as tk
from tkinter import ttk


class DarkTheme:
    """Modern dark theme color palette."""
    BG = "#121214"
    CARD_BG = "#1c1c1f"
    ACCENT = "#0ea5e9"
    SUCCESS = "#10b981"
    TEXT = "#f8fafc"
    MUTED = "#94a3b8"
    BORDER = "#27272a"


def setup_theme(root: tk.Tk) -> ttk.Style:
    """Configures modern dark ttk styles for treeviews, buttons, and frames."""
    root.configure(bg=DarkTheme.BG)
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure("TFrame", background=DarkTheme.BG)
    style.configure("Card.TFrame", background=DarkTheme.CARD_BG, relief="flat")

    style.configure("TLabel", background=DarkTheme.BG, foreground=DarkTheme.TEXT, font=("Segoe UI", 10))
    style.configure("Card.TLabel", background=DarkTheme.CARD_BG, foreground=DarkTheme.TEXT, font=("Segoe UI", 10))
    style.configure("Muted.TLabel", background=DarkTheme.CARD_BG, foreground=DarkTheme.MUTED, font=("Segoe UI", 9))
    style.configure("Title.TLabel", background=DarkTheme.BG, foreground=DarkTheme.TEXT, font=("Segoe UI", 14, "bold"))

    style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), background=DarkTheme.ACCENT, foreground="#ffffff")
    style.map("Accent.TButton", background=[("active", "#0284c7"), ("disabled", "#334155")])

    # Treeview (table)
    style.configure(
        "Treeview",
        background=DarkTheme.CARD_BG,
        foreground=DarkTheme.TEXT,
        fieldbackground=DarkTheme.CARD_BG,
        rowheight=26,
        font=("Segoe UI", 9)
    )
    style.configure(
        "Treeview.Heading",
        background="#27272a",
        foreground=DarkTheme.TEXT,
        font=("Segoe UI", 9, "bold"),
        relief="flat"
    )
    style.map("Treeview", background=[("selected", "#0369a1")])

    # Progress bar
    style.configure("TProgressbar", thickness=10, background=DarkTheme.ACCENT, troughcolor=DarkTheme.CARD_BG)
    return style


class StatCard(ttk.Frame):
    """Reusable dashboard metric display card."""

    def __init__(self, parent, title: str, initial_value: str = "0", *args, **kwargs):
        super().__init__(parent, style="Card.TFrame", padding=10, *args, **kwargs)
        self.val_label = ttk.Label(self, text=initial_value, font=("Segoe UI", 16, "bold"), style="Card.TLabel")
        self.val_label.pack(anchor="w")

        self.title_label = ttk.Label(self, text=title.upper(), style="Muted.TLabel")
        self.title_label.pack(anchor="w")

    def update_value(self, new_value: str):
        self.val_label.config(text=new_value)
