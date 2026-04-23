"""Custom in-game notification overlay for the Futoshiki GUI.

Replaces all tkinter messagebox calls with an immersive, themed card
rendered directly inside the game board area.  ASCII-art titles are
loaded from gui/fonts/*.txt files.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from typing import Callable

from .theme import (
    BG,
    BORDER,
    BTN_FILL,
    BTN_HOVER,
    BTN_HOVER_TEXT,
    BTN_TEXT,
    ERROR_COLOR,
    GRID_PATTERN_COLOR,
    HINT_COLOR,
    make_button,
    mono_font,
)

# ── Severity colour accents ──────────────────────────────────────────
_ACCENT = {
    "info":    BTN_FILL,
    "warning": HINT_COLOR,
    "error":   ERROR_COLOR,
    "success": BTN_FILL,
}

_POPUP_BG = BORDER                    # card background (black)

# Border thickness (pixels)
_BORDER_TOP = 3
_BORDER_LEFT = 3
_BORDER_RIGHT = 5                 # thicker on right edge
_BORDER_BOTTOM = 5                # thicker on bottom edge


class GameToast:
    """A toast notification card rendered inside a container widget.

    The toast is placed directly inside the game-board area (or any
    other container) rather than covering the entire application window.

    Usage::

        toast = GameToast(root_window, container=grid_area_frame)
        toast.show(
            body="Please load a puzzle first.",
            severity="warning",
            art_text=ascii_art_string,     # optional
            auto_dismiss_ms=4000,          # 0 = manual dismiss only
        )
    """

    # Class-level tracking so only one toast is visible at a time.
    _active: GameToast | None = None

    def __init__(
        self,
        parent: tk.Tk | tk.Toplevel,
        container: tk.Widget | None = None,
    ) -> None:
        self._parent = parent
        # If no container is given, fall back to the parent (whole window).
        self._container: tk.Widget = container if container is not None else parent
        self._card_outer: tk.Frame | None = None
        self._dismiss_job: str | None = None
        self._on_dismiss_callback: Callable[[], None] | None = None

    # ── public API ────────────────────────────────────────────────────

    def set_container(self, container: tk.Widget) -> None:
        """Change the target container for future toasts."""
        self._container = container

    def show(
        self,
        body: str,
        severity: str = "info",
        art_text: str | None = None,
        auto_dismiss_ms: int = 4000,
        on_dismiss: Callable[[], None] | None = None,
    ) -> None:
        """Display the toast card centred inside the container."""
        # Dismiss any existing toast first.
        if GameToast._active is not None and GameToast._active is not self:
            GameToast._active.dismiss()
        if self._card_outer is not None:
            self.dismiss()

        GameToast._active = self
        self._on_dismiss_callback = on_dismiss
        accent = _ACCENT.get(severity, BORDER)

        # ── Asymmetric border frame (thicker on right + bottom) ──────
        # Outer frame acts as the coloured border via its background.
        self._card_outer = tk.Frame(
            self._container, bg=accent, bd=0, relief=tk.FLAT,
        )

        # Inner card with asymmetric padding to create uneven border
        card = tk.Frame(self._card_outer, bg=_POPUP_BG, bd=0, relief=tk.FLAT)
        card.pack(
            fill="both",
            expand=True,
            padx=(_BORDER_LEFT, _BORDER_RIGHT),
            pady=(_BORDER_TOP, _BORDER_BOTTOM),
        )

        # Prevent clicks on the card from propagating
        card.bind("<Button-1>", lambda _e: "break")
        self._card_outer.bind("<Button-1>", lambda _e: "break")

        # ── ASCII art title ──────────────────────────────────────────
        if art_text and art_text.strip():
            art_label = tk.Label(
                card,
                text=art_text,
                font=mono_font(self._parent, 7, "bold"),
                fg=accent,
                bg=_POPUP_BG,
                justify=tk.LEFT,
            )
            art_label.pack(padx=20, pady=(20, 8))

        # ── Body text (bold + upscaled) ──────────────────────────────
        if body and body.strip():
            body_label = tk.Label(
                card,
                text=body,
                font=mono_font(self._parent, 11, "bold"),
                fg=BTN_FILL,
                bg=_POPUP_BG,
                justify=tk.CENTER,
                wraplength=600,
            )
            body_label.pack(padx=20, pady=(8, 12))

        # ── Accent divider ───────────────────────────────────────────
        tk.Frame(card, bg=accent, height=2, bd=0).pack(
            fill="x", padx=30, pady=(0, 12),
        )

        # ── Dismiss button ───────────────────────────────────────────
        btn_frame = tk.Frame(card, bg=_POPUP_BG, bd=0)
        btn_frame.pack(pady=(0, 18))

        dismiss_btn = make_button(btn_frame, "OK", self.dismiss)
        dismiss_btn.configure(padx=24, pady=6)
        dismiss_btn.pack()

        # ── Centre inside container using place ──────────────────────
        self._card_outer.place(relx=0.5, rely=0.5, anchor="center")
        self._card_outer.lift()

        # Auto-dismiss timer
        if auto_dismiss_ms > 0:
            self._dismiss_job = self._parent.after(auto_dismiss_ms, self.dismiss)

    def dismiss(self) -> None:
        """Remove the toast from the screen."""
        if self._dismiss_job is not None:
            self._parent.after_cancel(self._dismiss_job)
            self._dismiss_job = None

        if self._card_outer is not None:
            try:
                self._card_outer.destroy()
            except tk.TclError:
                pass
            self._card_outer = None

        if GameToast._active is self:
            GameToast._active = None

        if self._on_dismiss_callback is not None:
            cb = self._on_dismiss_callback
            self._on_dismiss_callback = None
            cb()

    @property
    def is_visible(self) -> bool:
        return self._card_outer is not None


# ── Module-level convenience helpers ─────────────────────────────────

def load_art_text(project_root: Path, filename: str, fallback: str = "") -> str:
    """Load an ASCII-art file from gui/fonts/."""
    candidates = (
        project_root / "gui" / "fonts" / filename,
        project_root / filename,
    )
    for candidate in candidates:
        if not (candidate.exists() and candidate.is_file()):
            continue
        try:
            text = candidate.read_text(encoding="utf-8-sig").replace("\r\n", "\n").rstrip()
        except OSError:
            continue
        if text.strip():
            return text
    return fallback


# Maps algorithm display names → ASCII-art filenames
ALGO_ART_FILES: dict[str, str] = {
    "Brute Force":      "BRUTE_FORCE_FINISHED.txt",
    "Backtracking":     "BACKTRACKING_FINISHED.txt",
    "Forward Chaining": "FORWARD_CHAINING_FINISHED.txt",
    "A*":               "ASTAR_FINISHED.txt",
}
