"""Theme definitions for the Futoshiki Tkinter GUI."""

import tkinter as tk
from tkinter import font as tkfont


BG = "#ffffff"
BTN_FILL = "#000000"
BTN_TEXT = "#ffffff"
BTN_HOVER = "#333333"
PANEL_BG = "#f5f5f5"
BORDER = "#000000"
GRID_LINE = "#e0e0e0"
SELECTED_RING = "#000000"
GIVEN_COLOR = "#000000"
PLAYER_COLOR = "#333333"
ALGO_COLOR = "#555555"
ERROR_COLOR = "#cc0000"
HINT_COLOR = "#ff9900"
DISABLED = "#aaaaaa"

FONT_LABEL = ("Press Start 2P", 9)
FONT_LABEL_FB = ("Courier", 9)
FONT_SMALL = ("Consolas", 8)
FONT_HINT = ("Consolas", 8, "italic")

CELL_SIZES = {4: 100, 5: 85, 6: 75, 7: 65, 9: 55}
FONT_SIZES = {4: 36, 5: 30, 6: 26, 7: 22, 9: 18}
FONT_CELL = ("Consolas", FONT_SIZES)


def get_cell_font(N: int) -> tuple:
    return ("Consolas", FONT_SIZES[N])


def _label_font_with_fallback(parent: tk.Misc) -> tuple:
    try:
        families = set(tkfont.families(parent))
    except tk.TclError:
        return FONT_LABEL_FB
    if FONT_LABEL[0] in families:
        return FONT_LABEL
    return FONT_LABEL_FB


def make_button(parent, text, command, style="normal"):
    label_font = _label_font_with_fallback(parent)

    button_kwargs = {
        "text": text,
        "command": command,
        "cursor": "hand2",
        "padx": 8,
        "pady": 4,
        "activebackground": BTN_HOVER,
        "relief": tk.FLAT,
        "bd": 0,
    }

    if style == "normal":
        button_kwargs.update(
            {
                "bg": BTN_FILL,
                "fg": BTN_TEXT,
                "font": label_font,
            }
        )
    elif style == "danger":
        button_kwargs.update(
            {
                "bg": BG,
                "fg": ERROR_COLOR,
                "font": label_font,
                "relief": tk.SOLID,
                "bd": 1,
            }
        )
    elif style == "small":
        button_kwargs.update(
            {
                "bg": BTN_FILL,
                "fg": BTN_TEXT,
                "font": FONT_SMALL,
            }
        )
    else:
        raise ValueError("style must be one of: normal, danger, small")

    button = tk.Button(parent, **button_kwargs)

    original_bg = button_kwargs["bg"]
    original_fg = button_kwargs["fg"]

    if style == "danger":
        button.bind("<Enter>", lambda _event: button.config(bg=ERROR_COLOR, fg=BG))
        button.bind("<Leave>", lambda _event: button.config(bg=original_bg, fg=original_fg))
    else:
        button.bind("<Enter>", lambda _event: button.config(bg=BTN_HOVER))
        button.bind("<Leave>", lambda _event: button.config(bg=original_bg))

    return button


THEME = {
    N: {
        "cell_size": CELL_SIZES[N],
        "font_size": FONT_SIZES[N],
    }
    for N in CELL_SIZES
}


class ThemeConfig:
    """Compatibility wrapper for modules that still import ThemeConfig."""

    def get_cell_size(self, grid_size: int) -> int:
        return CELL_SIZES[grid_size]

    def get_cell_font(self, grid_size: int) -> tuple:
        return get_cell_font(grid_size)
