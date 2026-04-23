"""
Shared GUI styling helpers.
"""

import customtkinter as ctk


APP_BG = ("#f4f6f8", "#111827")
SURFACE = ("#ffffff", "#1f2937")
SURFACE_ALT = ("#eef2f7", "#16202f")
SIDEBAR = ("#e7edf3", "#0b1220")
BORDER = ("#d7dee8", "#334155")
TEXT = ("#172033", "#f8fafc")
MUTED = ("#667085", "#a9b4c4")
ACCENT = ("#2563eb", "#3b82f6")
ACCENT_HOVER = ("#1d4ed8", "#60a5fa")
ACCENT_ACTIVE_HOVER = ("#1e40af", "#1d4ed8")
SUCCESS = ("#0f766e", "#2dd4bf")
SUCCESS_HOVER = ("#115e59", "#5eead4")
DANGER = ("#b42318", "#f97066")

FONT_TITLE = ("TkDefaultFont", 24, "bold")
FONT_SECTION = ("TkDefaultFont", 14, "bold")
FONT_BODY = ("TkDefaultFont", 12)
FONT_MONO = ("Courier", 11)


def apply_window(root):
    """Apply top-level window sizing and background."""
    root.title("sb3topy")
    root.geometry("1040x700")
    root.minsize(860, 560)
    root.configure(fg_color=APP_BG)


def page_header(parent, title, subtitle=None):
    """Create a compact page header."""
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    label = ctk.CTkLabel(
        frame, text=title, font=FONT_TITLE, text_color=TEXT, anchor="w")
    label.grid(row=0, column=0, sticky="ew")

    if subtitle:
        sub = ctk.CTkLabel(
            frame, text=subtitle, font=FONT_BODY, text_color=MUTED,
            anchor="w", justify="left")
        sub.grid(row=1, column=0, sticky="ew", pady=(2, 0))

    frame.columnconfigure(0, weight=1)
    return frame


def section(parent, title=None):
    """Create a styled section frame."""
    frame = ctk.CTkFrame(
        parent, fg_color=SURFACE, border_color=BORDER,
        border_width=1, corner_radius=8)
    if title:
        label = ctk.CTkLabel(
            frame, text=title, font=FONT_SECTION, text_color=TEXT,
            anchor="w")
        label.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))
    return frame


def primary_button(parent, **kwargs):
    """Create a primary action button."""
    return ctk.CTkButton(
        parent, fg_color=ACCENT, hover_color=ACCENT_HOVER,
        text_color="#ffffff", corner_radius=8, height=36, **kwargs)


def success_button(parent, **kwargs):
    """Create a positive action button."""
    return ctk.CTkButton(
        parent, fg_color=SUCCESS, hover_color=SUCCESS_HOVER,
        text_color="#ffffff", corner_radius=8, height=36, **kwargs)


def secondary_button(parent, **kwargs):
    """Create a secondary action button."""
    return ctk.CTkButton(
        parent, fg_color=SURFACE_ALT, hover_color=BORDER,
        text_color=TEXT, corner_radius=8, height=36, **kwargs)


def entry(parent, **kwargs):
    """Create a consistently styled entry."""
    return ctk.CTkEntry(
        parent, border_color=BORDER, corner_radius=8, height=36, **kwargs)


def checkbox(parent, **kwargs):
    """Create a consistently styled checkbox."""
    return ctk.CTkCheckBox(
        parent, fg_color=ACCENT, hover_color=ACCENT_HOVER,
        border_color=BORDER, text_color=TEXT, **kwargs)
