"""Theme definitions for the Futoshiki Tkinter GUI."""

import tkinter as tk
from tkinter import font as tkfont


BG                 = "#f2f0e3"
GRID_PATTERN_COLOR = "#e2e0d3"
BTN_FILL           = "#fafafa"
BTN_TEXT           = "#090909"
BTN_HOVER          = "#090909"
BTN_HOVER_TEXT     = "#fafafa"
PANEL_BG           = BG
BORDER             = "#090909"
GRID_LINE          = "#d4d1c4"
SELECTED_RING      = "#090909"
GIVEN_COLOR        = "#090909"
PLAYER_COLOR       = "#3a3a3a"
ALGO_COLOR         = "#2f2f2f"
ERROR_COLOR        = "#cc0000"
HINT_COLOR         = "#ff9900"
DISABLED           = "#8f8f8f"
# Tkinter colors do not support alpha; use a lighter blended tone as a softer shadow.
SHADOW             = "#9a9a96"

def bind_continuous_grid(canvas: tk.Canvas) -> None:
    """Binds a configure event to draw a continuous graph-paper grid across the app."""
    def _draw(event=None):
        if event and event.widget != canvas:
            return
        canvas.delete("bg_grid")
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w <= 1 or h <= 1:
            return
            
        spacing = 15
        root = canvas.winfo_toplevel()
        rx = root.winfo_rootx() if root.winfo_rootx() > 0 else 0
        ry = root.winfo_rooty() if root.winfo_rooty() > 0 else 0
        
        offset_x = canvas.winfo_rootx() - rx
        offset_y = canvas.winfo_rooty() - ry
        
        start_x = (spacing - (offset_x % spacing)) % spacing
        start_y = (spacing - (offset_y % spacing)) % spacing
        
        for x in range(start_x, w, spacing):
            canvas.create_line(x, 0, x, h, fill=GRID_PATTERN_COLOR, tags="bg_grid")
        for y in range(start_y, h, spacing):
            canvas.create_line(0, y, w, y, fill=GRID_PATTERN_COLOR, tags="bg_grid")
        canvas.tag_lower("bg_grid")

    canvas.bind("<Configure>", _draw, add="+")
    # Trigger an initial draw shortly after mapping
    canvas.after(100, _draw)

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


class NeoButton(tk.Frame):
    """Neo-brutalist wrapper replacing standard tk.Button."""
    
    def __init__(self, master: tk.Misc, **kwargs):
        self.command = kwargs.pop("command", None)
        self.default_bg = kwargs.get("bg", BTN_FILL)
        self.default_fg = kwargs.get("fg", BTN_TEXT)
        self._state = kwargs.pop("state", "normal")
        self._is_pressed = False
        # Thick brutalist shadow offset
        self.shadow_offset = 3 if kwargs.pop("style_small", False) else 3
        
        super().__init__(master, bg=SHADOW, padx=0, pady=0)
        
        # Strip out standard Button kwargs not supported by Label
        kwargs.pop("activebackground", None)
        kwargs.pop("activeforeground", None)
        kwargs.pop("disabledforeground", None)
        kwargs.pop("bd", None)
        kwargs.pop("relief", None)
        
        if "cursor" not in kwargs:
            kwargs["cursor"] = "hand2"
            
        self.top_layer = tk.Label(
            self,
            highlightbackground=BORDER,
            highlightcolor=BORDER,
            highlightthickness=2,
            **kwargs
        )
        
        self.top_layer.pack(fill="both", expand=True, padx=(0, self.shadow_offset), pady=(0, self.shadow_offset))
        
        self.top_layer.bind("<ButtonPress-1>", self._on_press)
        self.top_layer.bind("<ButtonRelease-1>", self._on_release)
        # Also bind on the frame in case user clicks the shadow area
        super().bind("<ButtonPress-1>", self._on_press)
        super().bind("<ButtonRelease-1>", self._on_release)

    def _on_press(self, event):
        if self._state != "disabled":
            self.top_layer.pack_configure(padx=(self.shadow_offset, 0), pady=(self.shadow_offset, 0))

    def _on_release(self, event):
        if self._state != "disabled":
            self.top_layer.pack_configure(padx=(0, self.shadow_offset), pady=(0, self.shadow_offset))
            # Only trigger command if released over the widget (simple check)
            if self.command:
                self.command()

    def configure(self, **kwargs):
        self.config(**kwargs)
        
    def config(self, **kwargs):
        if "command" in kwargs:
            self.command = kwargs.pop("command")
        if "state" in kwargs:
            self._state = kwargs.pop("state")
            if self._state == "disabled":
                self.top_layer.config(fg=DISABLED, cursor="arrow")
            else:
                self.top_layer.config(fg=self.default_fg, cursor="hand2")
            if not kwargs:
                return
                
        if "bg" in kwargs:
            self.default_bg = kwargs["bg"]
        if "fg" in kwargs:
            self.default_fg = kwargs["fg"]
            
        kwargs.pop("activebackground", None)
        kwargs.pop("activeforeground", None)
        kwargs.pop("disabledforeground", None)
        kwargs.pop("bd", None)
        kwargs.pop("relief", None)
        
        if kwargs:
            self.top_layer.config(**kwargs)

    def bind(self, sequence=None, func=None, add=None):
        return self.top_layer.bind(sequence, func, add)
        
    def unbind(self, sequence, funcid=None):
        self.top_layer.unbind(sequence, funcid)



def make_button(parent, text, command, style="normal"):
    label_font = _label_font_with_fallback(parent)

    button_kwargs = {
        "text": text,
        "command": command,
        "padx": 8,
        "pady": 4,
        "style_small": style == "small"
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

    button = NeoButton(parent, **button_kwargs)

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
