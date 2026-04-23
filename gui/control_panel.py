"""Control panel widget for puzzle actions and algorithm selection."""

from collections.abc import Callable
from pathlib import Path
import tkinter as tk

from .theme import (
    BG,
    BORDER,
    DISABLED,
    GRID_LINE,
    PANEL_BG,
    make_button,
    mono_font,
    bind_continuous_grid,
)


class ControlPanel(tk.Canvas):
    """Widget that groups command buttons and selection controls.

    Responsibilities:
    - Expose puzzle loading and solver action controls.
    - Provide solver algorithm and visualization speed selectors.
    - Display runtime statistics from the active solving session.
    - Offer a clean callback surface for the main app controller.
    """

    QUICK_LOAD_DEFAULTS = (
        ("4×4 Example 01", "inputs/input-4x4-01.txt"),
        ("4×4 Example 02", "inputs/input-4x4-02.txt"),
        ("5×5 Example 03", "inputs/input-5x5-03.txt"),
        ("5×5 Example 04", "inputs/input-5x5-04.txt"),
        ("6×6 Example 05", "inputs/input-6x6-05.txt"),
        ("6×6 Example 06", "inputs/input-6x6-06.txt"),
        ("7×7 Example 07", "inputs/input-7x7-07.txt"),
        ("7×7 Example 08", "inputs/input-7x7-08.txt"),
        ("9×9 Example 09", "inputs/input-9x9-09.txt"),
        ("9×9 Example 10", "inputs/input-9x9-10.txt"),
    )
    INPUT_FORMAT_TEXT = (
        "Input file format (.txt):\n"
        "Line 1: N\n"
        "Lines 2–N+1: grid rows (whitespace-separated integers, 0=empty)\n"
        "Lines N+2–2N+1: horizontal constraints (-1, 0, 1)\n"
        "Lines 2N+2–3N: vertical constraints (-1, 0, 1)"
    )

    def __init__(
        self,
        master: tk.Misc,
        on_load_puzzle: Callable[[str], None] | None = None,
        on_solve: Callable[[str, int], None] | None = None,
        on_step: Callable[[str], None] | None = None,
        on_reset: Callable[[], None] | None = None,
        on_speed_change: Callable[[int], None] | None = None,
        on_manual_toggle: Callable[[bool], None] | None = None,
        on_hint: Callable[[], None] | None = None,
        on_show_info: Callable[[str, str], None] | None = None,
    ) -> None:
        """Create a control panel and wire optional callback handlers."""
        super().__init__(
            master,
            bg=PANEL_BG,
            bd=0,
            highlightthickness=0,
        )
        bind_continuous_grid(self)

        self._label_font = self._resolve_label_font()

        self.on_load_puzzle = on_load_puzzle
        self.on_solve = on_solve
        self.on_step = on_step
        self.on_reset = on_reset
        self.on_speed_change = on_speed_change
        self.on_manual_toggle = on_manual_toggle
        self.on_hint = on_hint
        self.on_show_info = on_show_info

        self.selected_puzzle_path_var = tk.StringVar(value="")
        self.input_mode_var = tk.StringVar(value="keyboard")
        self.speed_value = tk.IntVar(value=5)
        self.speed_text_var = tk.StringVar(value=f"{self.speed_value.get():.0f}")
        self.manual_play_enabled = tk.BooleanVar(value=False)
        self.manual_time_var = tk.StringVar(value="Manual time: 00:00")

        self.time_elapsed_var = tk.StringVar(value="Time   : 0.000 s")
        self.recursive_calls_var = tk.StringVar(value="Calls  : 0")
        self.nodes_expanded_var = tk.StringVar(value="Nodes  : 0")

        self.manual_toggle_button: tk.Button | None = None
        self.hint_button: tk.Button | None = None
        self.manual_timer_label: tk.Label | None = None

        self.build_controls()
        self._emit_speed_change()

    def _resolve_label_font(self) -> tuple[str | int, ...]:
        return mono_font(self, 9)

    def _make_section(self, title: str) -> tk.Canvas:
        frame = tk.Canvas(
            self,
            bg=PANEL_BG,
            bd=0,
            highlightthickness=0,
        )
        bind_continuous_grid(frame)
        
        # Add a custom text label since tk.Canvas doesn't have LabelFrame titles natively
        tk.Label(
            frame,
            text=title,
            bg=PANEL_BG,
            fg=BORDER,
            font=mono_font(self, 8)
        ).grid(row=0, column=0, sticky="nw", pady=(0, 4))
        
        return frame

    def _add_divider(self, row: int) -> None:
        pass # Remove divider, grid lines make it obsolete

    @staticmethod
    def _set_disabled_color(button: tk.Button) -> None:
        button.configure(disabledforeground=DISABLED)

    def build_controls(self) -> None:
        """Build control rows for loading puzzles and solver actions."""
        self.columnconfigure(0, weight=1)
        current_row = 0

        quick_load_frame = self._make_section("Quick Load")
        quick_load_frame.grid(row=current_row, column=0, sticky="ew", pady=(0, 8), padx=12)
        quick_load_frame.columnconfigure(0, weight=1)

        quick_title_row = tk.Canvas(quick_load_frame, bg=PANEL_BG, bd=0, highlightthickness=0)
        bind_continuous_grid(quick_title_row)
        quick_title_row.grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 4))
        quick_title_row.columnconfigure(0, weight=1)

        tk.Label(
            quick_title_row,
            text="Examples",
            font=mono_font(self, 9, "bold"),
            fg=BORDER,
            bg=PANEL_BG,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        format_help_btn = make_button(
            quick_title_row,
            "?",
            self._show_input_format_popup,
            style="small",
        )
        self._set_disabled_color(format_help_btn)
        format_help_btn.configure(width=2)
        format_help_btn.grid(row=0, column=1, sticky="e")

        for idx, (label, path) in enumerate(self.QUICK_LOAD_DEFAULTS):
            quick_button = make_button(
                quick_load_frame,
                label,
                lambda p=path: self._on_quick_load(p),
            )
            self._set_disabled_color(quick_button)
            quick_button.grid(row=idx + 2, column=0, sticky="ew", padx=4, pady=2)

        current_row += 1
        self._add_divider(current_row)

        self._apply_manual_mode_ui()

    def wire_callbacks(
        self,
        on_load_puzzle: Callable[[str], None] | None = None,
        on_solve: Callable[[str, int], None] | None = None,
        on_step: Callable[[str], None] | None = None,
        on_reset: Callable[[], None] | None = None,
        on_speed_change: Callable[[int], None] | None = None,
        on_manual_toggle: Callable[[bool], None] | None = None,
        on_hint: Callable[[], None] | None = None,
    ) -> None:
        """Update action callbacks without coupling UI to application state."""
        if on_load_puzzle is not None:
            self.on_load_puzzle = on_load_puzzle
        if on_solve is not None:
            self.on_solve = on_solve
        if on_step is not None:
            self.on_step = on_step
        if on_reset is not None:
            self.on_reset = on_reset
        if on_speed_change is not None:
            self.on_speed_change = on_speed_change
        if on_manual_toggle is not None:
            self.on_manual_toggle = on_manual_toggle
        if on_hint is not None:
            self.on_hint = on_hint

    def _handle_load_puzzle(self) -> None:
        selected_path = self.selected_puzzle_path_var.get().strip()
        if self.on_load_puzzle is not None and selected_path:
            self.on_load_puzzle(selected_path)

    def _handle_clear_puzzle_path(self) -> None:
        self.selected_puzzle_path_var.set("")

    def _show_input_format_popup(self) -> None:
        if self.on_show_info is not None:
            self.on_show_info("Input File Format", self.INPUT_FORMAT_TEXT)
            return
        # Fallback: print to console if no callback is wired
        print(self.INPUT_FORMAT_TEXT)

    def _on_quick_load(self, path: str) -> None:
        base_dir = Path(__file__).resolve().parent.parent
        candidate = Path(path)
        resolved_path = candidate if candidate.is_absolute() else (base_dir / candidate)
        resolved_path_str = str(resolved_path.resolve())

        self.selected_puzzle_path_var.set(resolved_path_str)
        if self.on_load_puzzle is not None:
            self.on_load_puzzle(resolved_path_str)

    def _handle_solve(self) -> None:
        if self.on_solve is not None:
            self.on_solve("Backtracking", self.get_delay_ms())

    def _handle_step(self) -> None:
        if self.on_step is not None:
            self.on_step("Backtracking")

    def _handle_reset(self) -> None:
        if self.on_reset is not None:
            self.on_reset()

    def _handle_manual_toggle(self) -> None:
        enabled = not self.manual_play_enabled.get()
        self.set_manual_mode(enabled)
        if self.on_manual_toggle is not None:
            self.on_manual_toggle(enabled)

    def _handle_hint(self) -> None:
        if self.on_hint is not None:
            self.on_hint()

    def _handle_speed_change(self, _value: str) -> None:
        speed = round(self.speed_value.get())
        self.speed_value.set(speed)
        self.speed_text_var.set(f"{speed}")
        self._emit_speed_change()

    def _emit_speed_change(self) -> None:
        if self.on_speed_change is not None:
            self.on_speed_change(self.get_delay_ms())

    def get_delay_ms(self) -> int:
        """Convert speed slider value (1..10) into animation delay in ms."""
        speed = max(1, min(10, int(round(self.speed_value.get()))))
        return 100 + (10 - speed) * 100

    @property
    def input_mode(self) -> str:
        return self.input_mode_var.get()

    def set_manual_mode(self, enabled: bool) -> None:
        """Programmatically set Manual Play mode and refresh related controls."""
        self.manual_play_enabled.set(enabled)
        self._apply_manual_mode_ui()

    def update_manual_timer(self, elapsed_seconds: float) -> None:
        """Update Manual Play timer display in MM:SS or HH:MM:SS format."""
        total_seconds = max(0, int(elapsed_seconds))
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            self.manual_time_var.set(f"Manual time: {hours:02d}:{minutes:02d}:{seconds:02d}")
            return
        self.manual_time_var.set(f"Manual time: {minutes:02d}:{seconds:02d}")

    def update_stats(
        self,
        time_elapsed: float | str | None = None,
        recursive_calls: int | None = None,
        nodes_expanded: int | None = None,
    ) -> None:
        """Update row-4 labels from app/scheduler progress callbacks."""
        if time_elapsed is not None:
            if isinstance(time_elapsed, str):
                self.time_elapsed_var.set(f"Time   : {time_elapsed}")
            else:
                self.time_elapsed_var.set(f"Time   : {time_elapsed:.3f} s")

        if recursive_calls is not None:
            self.recursive_calls_var.set(f"Calls  : {recursive_calls}")

        if nodes_expanded is not None:
            self.nodes_expanded_var.set(f"Nodes  : {nodes_expanded}")

    def reset_stats(self) -> None:
        """Reset displayed statistics before a new solve session starts."""
        self.update_stats(time_elapsed=0.0, recursive_calls=0, nodes_expanded=0)

    def _apply_manual_mode_ui(self) -> None:
        enabled = self.manual_play_enabled.get()
        if self.manual_toggle_button is not None:
            self.manual_toggle_button.configure(
                text="Manual Play: ON" if enabled else "Manual Play: OFF"
            )

        if enabled:
            if self.hint_button is not None:
                self.hint_button.grid()
            if self.manual_timer_label is not None:
                self.manual_timer_label.grid()
            return

        if self.hint_button is not None:
            self.hint_button.grid_remove()
        if self.manual_timer_label is not None:
            self.manual_timer_label.grid_remove()
