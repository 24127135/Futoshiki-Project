"""Canvas-based puzzle grid widget for Futoshiki."""

from collections.abc import Callable
import tkinter as tk
from typing import Any

from .theme import (
    ALGO_COLOR,
    BG,
    BORDER,
    ERROR_COLOR,
    GIVEN_COLOR,
    GRID_PATTERN_COLOR,
    GRID_LINE,
    HINT_COLOR,
    PANEL_BG,
    PLAYER_COLOR,
    SELECTED_RING,
    THEME,
    make_button,
    mono_font,
    bind_continuous_grid,
    get_cell_font,
    BTN_FILL,
    SHADOW,
)


GAP = 20
PADDING = 20
BACKGROUND_PATTERN_SPACING = 15
TARGET_GRID_N = 9
TARGET_GRID_PIXEL_SIZE = (THEME[TARGET_GRID_N]["cell_size"] * TARGET_GRID_N) + (
    max(TARGET_GRID_N - 1, 0) * GAP
)


def check_cell_valid(
    grid: list[list[int | None]],
    i: int,
    j: int,
    h_constraints: list[list[str]],
    v_constraints: list[list[str]],
    N: int,
) -> bool:
    """Validate one cell against row, column, and local inequality constraints."""

    def to_int(value: int | None) -> int | None:
        if value in (None, 0, ""):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def vertical_holds(top: int, bottom: int, sign: str) -> bool:
        # '^' means top < bottom, and 'v' means top > bottom.
        if sign == "^":
            return top < bottom
        if sign == "v":
            return top > bottom
        return True

    if not (0 <= i < N and 0 <= j < N):
        return False

    value = to_int(grid[i][j])
    if value is None or not (1 <= value <= N):
        return False

    for col in range(N):
        if col == j:
            continue
        other = to_int(grid[i][col])
        if other is not None and other == value:
            return False

    for row in range(N):
        if row == i:
            continue
        other = to_int(grid[row][j])
        if other is not None and other == value:
            return False

    if j > 0 and i < len(h_constraints) and (j - 1) < len(h_constraints[i]):
        sign = h_constraints[i][j - 1]
        left = to_int(grid[i][j - 1])
        if sign in {"<", ">"} and left is not None:
            if sign == "<" and not (left < value):
                return False
            if sign == ">" and not (left > value):
                return False

    if j < (N - 1) and i < len(h_constraints) and j < len(h_constraints[i]):
        sign = h_constraints[i][j]
        right = to_int(grid[i][j + 1])
        if sign in {"<", ">"} and right is not None:
            if sign == "<" and not (value < right):
                return False
            if sign == ">" and not (value > right):
                return False

    if i > 0 and (i - 1) < len(v_constraints) and j < len(v_constraints[i - 1]):
        sign = v_constraints[i - 1][j]
        top = to_int(grid[i - 1][j])
        if sign in {"^", "v"} and top is not None and not vertical_holds(top, value, sign):
            return False

    if i < (N - 1) and i < len(v_constraints) and j < len(v_constraints[i]):
        sign = v_constraints[i][j]
        bottom = to_int(grid[i + 1][j])
        if sign in {"^", "v"} and bottom is not None and not vertical_holds(value, bottom, sign):
            return False

    return True


class FutoshikiGrid(tk.Canvas):
    """Canvas widget that renders a Futoshiki board and supports user selection.

    Responsibilities:
    - Draw cells, fixed clues, and inequality constraints.
    - Track and highlight the currently selected cell.
    - Update displayed values by source mode (player, algo, error).
    """

    def __init__(
        self,
        master: tk.Misc,
        N: int,
        grid: list[list[int | None]] | None,
        h_constraints: list[list[str]] | None,
        v_constraints: list[list[str]] | None,
        get_input_mode: Callable[[], str] | None = None,
        on_solved: Callable[[], None] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the board canvas with size, values, and constraints."""
        self.N = N
        self.theme = THEME.get(N, THEME[9])
        fixed_gap_total = max(self.N - 1, 0) * GAP
        self.cell_size = (TARGET_GRID_PIXEL_SIZE - fixed_gap_total) / self.N
        self.gap = GAP
        self.padding = PADDING
        self.grid_pixel_size = TARGET_GRID_PIXEL_SIZE
        self.base_canvas_size = self.grid_pixel_size + (2 * self.padding)
        self._board_origin_x = self.padding
        self._board_origin_y = self.padding

        super().__init__(
            master,
            width=self.base_canvas_size,
            height=self.base_canvas_size,
            background=BG,
            highlightthickness=0,
            **kwargs,
        )

        self.board = self._normalize_grid(grid)
        self.h_constraints = self._normalize_h_constraints(h_constraints)
        self.v_constraints = self._normalize_v_constraints(v_constraints)
        self.given_cells = {
            (i, j)
            for i in range(self.N)
            for j in range(self.N)
            if self.board[i][j] is not None
        }
        self.value_modes: dict[tuple[int, int], str] = {}
        self.selected_cell: tuple[int, int] | None = None
        self._solved_announced = False
        self.keyboard_input_enabled = False
        self._get_input_mode = get_input_mode or (lambda: "keyboard")
        self._on_solved = on_solved
        self._input_popup: tk.Toplevel | None = None

        self._cell_items: dict[tuple[int, int], int] = {}
        self._value_items: dict[tuple[int, int], int] = {}
        self._flash_jobs: dict[tuple[int, int], str] = {}

        self.bind("<Button-1>", self._on_cell_click)
        self.bind("<Key>", self._on_key_press)
        self.bind("<Configure>", self._on_canvas_resize)
        self.configure(takefocus=1)
        
        bind_continuous_grid(self)
        self.redraw()

    def _canvas_dimensions(self) -> tuple[int, int]:
        width = self.winfo_width()
        height = self.winfo_height()
        if width <= 1:
            width = int(float(self.cget("width")))
        if height <= 1:
            height = int(float(self.cget("height")))
        return width, height

    def _update_board_origin(self) -> None:
        canvas_w, canvas_h = self._canvas_dimensions()
        self._board_origin_x = max(self.padding, (canvas_w - self.grid_pixel_size) // 2)
        self._board_origin_y = max(self.padding, (canvas_h - self.grid_pixel_size) // 2)

    def _cell_top_left(self, i: int, j: int) -> tuple[int, int]:
        x = self._board_origin_x + (j * (self.cell_size + self.gap))
        y = self._board_origin_y + (i * (self.cell_size + self.gap))
        return x, y

    def _cell_center(self, i: int, j: int) -> tuple[float, float]:
        x, y = self._cell_top_left(i, j)
        return x + (self.cell_size / 2), y + (self.cell_size / 2)

    def _point_to_cell(self, x: int, y: int) -> tuple[int, int] | None:
        local_x = x - self._board_origin_x
        local_y = y - self._board_origin_y

        if local_x < 0 or local_y < 0:
            return None
        if local_x >= self.grid_pixel_size or local_y >= self.grid_pixel_size:
            return None

        step = self.cell_size + self.gap
        j = int(local_x // step)
        i = int(local_y // step)

        if not self._in_bounds(i, j):
            return None

        if (local_x % step) >= self.cell_size:
            return None
        if (local_y % step) >= self.cell_size:
            return None

        return i, j

    def _on_canvas_resize(self, _event: tk.Event) -> None:
        self.redraw()

    def _normalize_grid(self, raw_grid: list[list[int | None]] | None) -> list[list[int | None]]:
        normalized: list[list[int | None]] = []
        for i in range(self.N):
            row: list[int | None] = []
            for j in range(self.N):
                value: int | None = None
                if raw_grid and i < len(raw_grid) and j < len(raw_grid[i]):
                    candidate = raw_grid[i][j]
                    if candidate not in (None, 0, ""):
                        try:
                            value = int(candidate)
                        except (TypeError, ValueError):
                            value = None
                row.append(value)
            normalized.append(row)
        return normalized

    def _normalize_h_constraints(
        self, raw_constraints: list[list[str]] | None
    ) -> list[list[str]]:
        normalized: list[list[str]] = []
        for i in range(self.N):
            row: list[str] = []
            for j in range(max(self.N - 1, 0)):
                value = ""
                if raw_constraints and i < len(raw_constraints) and j < len(raw_constraints[i]):
                    candidate = raw_constraints[i][j]
                    if candidate in {"<", ">"}:
                        value = candidate
                row.append(value)
            normalized.append(row)
        return normalized

    def _normalize_v_constraints(
        self, raw_constraints: list[list[str]] | None
    ) -> list[list[str]]:
        normalized: list[list[str]] = []
        for i in range(max(self.N - 1, 0)):
            row: list[str] = []
            for j in range(self.N):
                value = ""
                if raw_constraints and i < len(raw_constraints) and j < len(raw_constraints[i]):
                    candidate = raw_constraints[i][j]
                    if candidate in {"^", "v"}:
                        value = candidate
                row.append(value)
            normalized.append(row)
        return normalized

    def redraw(self) -> None:
        """Render cells, values, and constraints from current widget state."""
        self._update_board_origin()
        
        # Don't delete bg_grid lines drawn by bind_continuous_grid
        for item in self.find_all():
            if "bg_grid" not in self.gettags(item):
                self.delete(item)
                
        self._cell_items.clear()
        self._value_items.clear()

        self._draw_board_background()
        self._draw_cells()
        self._draw_inequalities()
        self._draw_values()
        self._draw_outer_border()

    def _draw_board_background(self) -> None:
        x1 = self._board_origin_x
        y1 = self._board_origin_y
        x2 = x1 + self.grid_pixel_size
        y2 = y1 + self.grid_pixel_size
        
        # Neo-brutalist drop shadow for the entire board
        shadow_offset = 6
        self.create_rectangle(
            x1 + shadow_offset, 
            y1 + shadow_offset, 
            x2 + shadow_offset, 
            y2 + shadow_offset, 
            fill=SHADOW, 
            outline="",
        )
        
        # Solid white background for the board zone
        self.create_rectangle(
            x1, 
            y1, 
            x2, 
            y2, 
            fill=BTN_FILL, 
            outline="",
        )

    def _draw_cells(self) -> None:
        for i in range(self.N):
            for j in range(self.N):
                x1, y1 = self._cell_top_left(i, j)
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                fill, outline, width = self._cell_style(i, j)
                item_id = self.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=fill,
                    outline=outline,
                    width=width,
                )
                self._cell_items[(i, j)] = item_id

    def _cell_style(self, i: int, j: int) -> tuple[str, str, int]:
        fill = BTN_FILL
        outline = GRID_LINE
        width = 1

        if (i, j) in self.given_cells:
            fill = PANEL_BG
            outline = BORDER
            width = 1
        elif self.board[i][j] is not None:
            if not check_cell_valid(self.board, i, j, self.h_constraints, self.v_constraints, self.N):
                fill = BTN_FILL
                outline = ERROR_COLOR
                width = 2

        if self.selected_cell == (i, j):
            outline = SELECTED_RING
            width = 3

        return fill, outline, width

    def _draw_inequalities(self) -> None:
        sign_font_size = max(12, self.gap - 4)

        for i in range(self.N):
            for j in range(self.N - 1):
                sign = self.h_constraints[i][j]
                if not sign:
                    continue
                x = self._board_origin_x + (j * (self.cell_size + self.gap)) + self.cell_size + (
                    self.gap // 2
                )
                y = self._board_origin_y + (i * (self.cell_size + self.gap)) + (self.cell_size // 2)
                self.create_text(
                    x,
                    y,
                    text=sign,
                    fill=BORDER,
                    font=mono_font(self, sign_font_size, "bold"),
                    anchor=tk.CENTER,
                )

        for i in range(self.N - 1):
            for j in range(self.N):
                sign = self.v_constraints[i][j]
                if not sign:
                    continue
                display_sign = "∧" if sign == "^" else "∨" if sign == "v" else sign
                x = self._board_origin_x + (j * (self.cell_size + self.gap)) + (self.cell_size // 2)
                y = self._board_origin_y + (i * (self.cell_size + self.gap)) + self.cell_size + (
                    self.gap // 2
                )
                self.create_text(
                    x,
                    y,
                    text=display_sign,
                    fill=BORDER,
                    font=mono_font(self, sign_font_size, "bold"),
                    anchor=tk.CENTER,
                )

    def _draw_values(self) -> None:
        for i in range(self.N):
            for j in range(self.N):
                value = self.board[i][j]
                if value is None:
                    continue

                x, y = self._cell_center(i, j)
                text_item = self.create_text(
                    x,
                    y,
                    text=str(value),
                    fill=self._value_color(i, j),
                    font=self._value_font(i, j),
                )
                self._value_items[(i, j)] = text_item

    def _draw_outer_border(self) -> None:
        x1 = self._board_origin_x
        y1 = self._board_origin_y
        x2 = x1 + self.grid_pixel_size
        y2 = y1 + self.grid_pixel_size
        # Neo-brutalist thick border
        self.create_rectangle(x1, y1, x2, y2, outline=BORDER, width=4, fill="")

    def _value_font(self, i: int, j: int) -> tuple:
        base = get_cell_font(self.N, self)
        if (i, j) in self.given_cells:
            return (base[0], base[1], "bold")
        mode = self.value_modes.get((i, j), "player")
        if mode == "player":
            return (base[0], max(10, base[1] - 1), "normal")
        return (base[0], base[1], "normal")

    def _cell_background(self, i: int, j: int) -> str:
        fill, _outline, _width = self._cell_style(i, j)
        return fill

    def _value_color(self, i: int, j: int) -> str:
        if (i, j) in self.given_cells:
            return GIVEN_COLOR

        if self.board[i][j] is not None:
            if not check_cell_valid(self.board, i, j, self.h_constraints, self.v_constraints, self.N):
                return ERROR_COLOR

        mode = self.value_modes.get((i, j), "player")
        mode_to_color = {
            "player": PLAYER_COLOR,
            "algo": ALGO_COLOR,
            "hint": HINT_COLOR,
        }
        return mode_to_color.get(mode, PLAYER_COLOR)

    def _on_cell_click(self, event: tk.Event) -> None:
        hit_cell = self._point_to_cell(event.x, event.y)
        if hit_cell is None:
            return

        i, j = hit_cell

        if not self._in_bounds(i, j):
            return

        self.focus_set()

        def select_cell(row: int, col: int) -> None:
            previous = self.selected_cell
            self.selected_cell = (row, col)

            if previous and previous in self._cell_items:
                prev_fill, prev_outline, prev_width = self._cell_style(previous[0], previous[1])
                self.itemconfigure(
                    self._cell_items[previous],
                    fill=prev_fill,
                    outline=prev_outline,
                    width=prev_width,
                )

            if self.selected_cell in self._cell_items:
                fill, outline, width = self._cell_style(row, col)
                self.itemconfigure(
                    self._cell_items[self.selected_cell],
                    fill=fill,
                    outline=outline,
                    width=width,
                )

        input_mode = self._get_input_mode()

        if input_mode == "popup":
            select_cell(i, j)
            if (i, j) in self.given_cells:
                return

            if self._input_popup is not None and self._input_popup.winfo_exists():
                self._input_popup.destroy()

            popup = tk.Toplevel(self)
            self._input_popup = popup
            popup.title("Select Value")
            popup.configure(bg=BG)
            popup.transient(self.winfo_toplevel())
            popup.resizable(False, False)
            popup.grab_set()

            def close_popup() -> None:
                if popup.grab_current() is popup:
                    popup.grab_release()
                if popup.winfo_exists():
                    popup.destroy()
                if self._input_popup is popup:
                    self._input_popup = None

            popup.protocol("WM_DELETE_WINDOW", close_popup)

            def choose_value(v: int) -> None:
                self.set_value(i, j, v, "player")
                close_popup()

            def clear_current() -> None:
                self.clear_value(i, j)
                close_popup()

            border_frame = tk.Frame(popup, bg=BORDER, bd=0, relief=tk.FLAT)
            border_frame.pack(fill="both", expand=True)

            content = tk.Frame(border_frame, bg=BG, bd=0, relief=tk.FLAT)
            content.pack(fill="both", expand=True, padx=1, pady=1)

            tk.Label(
                content,
                text="SELECT VALUE",
                font=mono_font(self, 8, "bold"),
                fg=BORDER,
                bg=BG,
            ).grid(row=0, column=0, columnspan=2, padx=8, pady=(8, 6), sticky="w")

            buttons_frame = tk.Frame(content, bg=BG, bd=0, relief=tk.FLAT)
            buttons_frame.grid(row=1, column=0, columnspan=2, padx=8, pady=(0, 4))

            for value in range(1, self.N + 1):
                if self.N >= 7:
                    split = (self.N + 1) // 2
                    row_idx = 0 if value <= split else 1
                    col_idx = value - 1 if row_idx == 0 else value - split - 1
                else:
                    row_idx = 0
                    col_idx = value - 1

                number_button = make_button(
                    buttons_frame,
                    str(value),
                    lambda chosen=value: choose_value(chosen),
                    style="normal",
                )
                number_button.configure(width=3)
                number_button.grid(row=row_idx, column=col_idx, padx=2, pady=2)

            clear_button = make_button(content, "CLR", clear_current, style="danger")
            clear_button.configure(width=6)
            clear_button.grid(row=2, column=0, padx=8, pady=(0, 8), sticky="w")

            popup.update_idletasks()
            cell_center_x = (
                self.winfo_rootx()
                + self._board_origin_x
                + (j * (self.cell_size + self.gap))
                + (self.cell_size // 2)
            )
            cell_center_y = (
                self.winfo_rooty()
                + self._board_origin_y
                + (i * (self.cell_size + self.gap))
                + (self.cell_size // 2)
            )
            x = cell_center_x - (popup.winfo_width() // 2)
            y = cell_center_y - (popup.winfo_height() // 2)
            popup.geometry(f"+{x}+{y}")
            popup.lift()
            popup.focus_set()
            return

        if input_mode == "cycle":
            if self.selected_cell != (i, j):
                select_cell(i, j)
                return

            if (i, j) in self.given_cells:
                return

            current = self.board[i][j]
            if current is None:
                next_value = 1
            elif current >= self.N:
                next_value = 0
            else:
                next_value = current + 1

            if next_value == 0:
                self.clear_value(i, j)
            else:
                self.set_value(i, j, next_value, "player")
            return

        # keyboard (default): keep existing click-to-select behavior.
        select_cell(i, j)

    def _on_click(self, event: tk.Event) -> None:
        self._on_cell_click(event)

    def _on_key_press(self, event: tk.Event) -> None:
        if not self.keyboard_input_enabled:
            return

        if self.selected_cell is None:
            return

        i, j = self.selected_cell
        if (i, j) in self.given_cells:
            return

        if event.keysym in {"BackSpace", "Delete"}:
            self.clear_value(i, j)
            return

        if not event.char or not event.char.isdigit():
            return

        value = int(event.char)
        if not (1 <= value <= self.N):
            return

        self.board[i][j] = value
        self.value_modes[(i, j)] = "player"
        self.redraw()
        self._check_and_notify_solved()

        # TODO: Add optional pencil-mark input mode in a future iteration.

    def _in_bounds(self, i: int, j: int) -> bool:
        return 0 <= i < self.N and 0 <= j < self.N

    def set_value(self, i: int, j: int, v: int, mode: str) -> None:
        """Set a non-given cell value and style it by mode."""
        if not self._in_bounds(i, j) or (i, j) in self.given_cells:
            return
        if mode not in {"player", "algo", "error", "hint"}:
            raise ValueError("mode must be one of: player, algo, error, hint")

        self.board[i][j] = v
        self.value_modes[(i, j)] = mode
        self.redraw()
        self._check_and_notify_solved()

    def clear_value(self, i: int, j: int) -> None:
        """Erase a non-given cell value from the canvas."""
        if not self._in_bounds(i, j) or (i, j) in self.given_cells:
            return

        self.board[i][j] = None
        self.value_modes.pop((i, j), None)
        self.redraw()
        self._check_and_notify_solved()

    def set_keyboard_enabled(self, enabled: bool) -> None:
        """Enable or disable player keyboard entry for selected cells."""
        self.keyboard_input_enabled = enabled

    def flash_cell(self, i: int, j: int, color: str) -> None:
        """Temporarily color a cell, then restore its normal background."""
        if not self._in_bounds(i, j):
            return

        item_id = self._cell_items.get((i, j))
        if item_id is None:
            return

        existing_job = self._flash_jobs.get((i, j))
        if existing_job is not None:
            self.after_cancel(existing_job)

        self.itemconfigure(item_id, fill=color)

        def restore() -> None:
            if (i, j) in self._cell_items:
                fill, outline, width = self._cell_style(i, j)
                self.itemconfigure(
                    self._cell_items[(i, j)],
                    fill=fill,
                    outline=outline,
                    width=width,
                )
            self._flash_jobs.pop((i, j), None)

        self._flash_jobs[(i, j)] = self.after(180, restore)

    def _is_puzzle_solved(self) -> bool:
        for i in range(self.N):
            for j in range(self.N):
                if self.board[i][j] is None:
                    return False
                if not check_cell_valid(
                    self.board,
                    i,
                    j,
                    self.h_constraints,
                    self.v_constraints,
                    self.N,
                ):
                    return False
        return True

    def _check_and_notify_solved(self) -> None:
        solved = self._is_puzzle_solved()
        if solved and not self._solved_announced:
            self._solved_announced = True
            if self._on_solved is not None:
                self._on_solved()
        elif not solved:
            self._solved_announced = False


class FutoshikiGridWidget(FutoshikiGrid):
    """Backward-compatible wrapper around FutoshikiGrid."""

    def __init__(self, master: tk.Misc, grid_size: int = 4, **kwargs: Any) -> None:
        empty_grid = [[None for _ in range(grid_size)] for _ in range(grid_size)]
        h_constraints = [["" for _ in range(max(grid_size - 1, 0))] for _ in range(grid_size)]
        v_constraints = [["" for _ in range(grid_size)] for _ in range(max(grid_size - 1, 0))]
        super().__init__(
            master,
            N=grid_size,
            grid=empty_grid,
            h_constraints=h_constraints,
            v_constraints=v_constraints,
            **kwargs,
        )
