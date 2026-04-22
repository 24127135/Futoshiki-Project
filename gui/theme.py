"""Theme definitions for the Futoshiki Tkinter GUI."""

import tkinter as tk
from tkinter import font as tkfont


BG = "#f2f0e3"
GRID_PATTERN_COLOR = "#e2e0d3"
BTN_FILL = "#fafafa"
BTN_TEXT = "#090909"
BTN_HOVER = "#090909"
BTN_HOVER_TEXT = "#fafafa"
PANEL_BG = BG
BORDER = "#090909"
GRID_LINE = "#d4d1c4"
SELECTED_RING = "#090909"
GIVEN_COLOR = "#090909"
PLAYER_COLOR = "#3a3a3a"
ALGO_COLOR = "#2f2f2f"
ERROR_COLOR = "#cc0000"
HINT_COLOR = "#ff9900"
DISABLED = "#8f8f8f"

MONO_FONT_CANDIDATES = (
    "JetBrain NerdFont Mono",
    "JetBrains Nerd Font Mono",
    "JetBrainsMono Nerd Font Mono",
    "JetBrainsMono NF",
    "JetBrains Mono",
    "Consolas",
    "Courier New",
    "Courier",
)

FONT_LABEL = (MONO_FONT_CANDIDATES[0], 9)
FONT_LABEL_FB = ("Consolas", 9)
FONT_SMALL = (MONO_FONT_CANDIDATES[0], 8)
FONT_HINT = (MONO_FONT_CANDIDATES[0], 8, "italic")

CELL_SIZES = {4: 100, 5: 85, 6: 75, 7: 65, 9: 55}
FONT_SIZES = {4: 36, 5: 30, 6: 26, 7: 22, 9: 18}
FONT_CELL = (MONO_FONT_CANDIDATES[0], FONT_SIZES)

_MONO_FONT_FAMILY: str | None = None


def get_mono_font_family(parent: tk.Misc | None = None) -> str:
    global _MONO_FONT_FAMILY
    if _MONO_FONT_FAMILY is not None:
        return _MONO_FONT_FAMILY

    try:
        if parent is not None:
            families = set(tkfont.families(parent))
        else:
            families = set(tkfont.families())
    except tk.TclError:
        _MONO_FONT_FAMILY = FONT_LABEL_FB[0]
        return _MONO_FONT_FAMILY

    for candidate in MONO_FONT_CANDIDATES:
        if candidate in families:
            _MONO_FONT_FAMILY = candidate
            return _MONO_FONT_FAMILY

    _MONO_FONT_FAMILY = FONT_LABEL_FB[0]
    return _MONO_FONT_FAMILY


def mono_font(
    parent: tk.Misc | None,
    size: int,
    weight: str | None = None,
    slant: str | None = None,
) -> tuple[str | int, ...]:
    parts: list[str | int] = [get_mono_font_family(parent), size]
    if weight is not None:
        parts.append(weight)
    if slant is not None:
        parts.append(slant)
    return tuple(parts)


def get_cell_font(N: int, parent: tk.Misc | None = None) -> tuple[str | int, ...]:
    return mono_font(parent, FONT_SIZES[N])


def _label_font_with_fallback(parent: tk.Misc) -> tuple:
    return mono_font(parent, FONT_LABEL[1])


def make_button(parent, text, command, style="normal"):
    label_font = _label_font_with_fallback(parent)

    button_kwargs = {
        "text": text,
        "command": command,
        "cursor": "hand2",
        "padx": 8,
        "pady": 4,
        "activebackground": BTN_HOVER,
        "activeforeground": BTN_HOVER_TEXT,
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
                "bg": BTN_FILL,
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
                "font": mono_font(parent, FONT_SMALL[1]),
            }
        )
    else:
        raise ValueError("style must be one of: normal, danger, small")

    button = tk.Button(parent, **button_kwargs)

    original_bg = button_kwargs["bg"]
    original_fg = button_kwargs["fg"]

    button.bind("<Enter>", lambda _event: button.config(bg=BTN_HOVER, fg=BTN_HOVER_TEXT))
    button.bind("<Leave>", lambda _event: button.config(bg=original_bg, fg=original_fg))

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
