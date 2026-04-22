"""Main application window for the Futoshiki GUI."""

from __future__ import annotations

import copy
from pathlib import Path
import re
import sys
from time import perf_counter
import tkinter as tk
from tkinter import messagebox

from .control_panel import ControlPanel
from .grid_widget import FutoshikiGrid
from .solver_generators import SOLVER_GENERATORS, SolverEvent, backtracking_solver_gen
from .solver_runner import SolverRunner
from .theme import (
    BG,
    BORDER,
    BTN_FILL,
    BTN_HOVER,
    BTN_HOVER_TEXT,
    BTN_TEXT,
    CELL_SIZES,
    GRID_PATTERN_COLOR,
    make_button,
    mono_font,
)

try:
    from futoshiki.io_parser import parse_puzzle_text
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
    from futoshiki.io_parser import parse_puzzle_text


class FutoshikiApp(tk.Tk):
    """Top-level Tkinter application shell.

    Responsibilities:
    - Build and own the top-level four-zone GUI layout.
    - Handle puzzle loading, reset, and solver visualization callbacks.
    - Keep UI responsive during solving via Tkinter's after scheduler.
    """

    def __init__(self) -> None:
        """Initialize app state, layout containers, and default board."""
        super().__init__()

        self.configure(bg=BG)
        self.title("FUTOSHIKI  —  Logic Puzzle Solver")
        self.minsize(900, 620)

        self.project_root = Path(__file__).resolve().parent.parent
        self._title_art_text = self._load_title_art_text()

        self.current_N = 4
        self.current_grid = [[None for _ in range(self.current_N)] for _ in range(self.current_N)]
        self.current_h_constraints = [
            ["" for _ in range(self.current_N - 1)] for _ in range(self.current_N)
        ]
        self.current_v_constraints = [
            ["" for _ in range(self.current_N)] for _ in range(self.current_N - 1)
        ]
        self.initial_grid = copy.deepcopy(self.current_grid)

        self.grid_widget: FutoshikiGrid | None = None
        self.control_panel: ControlPanel | None = None
        self._title_area: tk.Frame | None = None
        self._top_bar_area: tk.Frame | None = None
        self._grid_area: tk.Frame | None = None
        self._control_area: tk.Frame | None = None
        self._placeholder_canvas: tk.Canvas | None = None
        self._grid_area_pattern: tk.Canvas | None = None
        self._loading_canvas: tk.Canvas | None = None

        self._solver_algorithm: str | None = None
        self._solver_runner: SolverRunner | None = None
        self._animation_job: str | None = None
        self._animation_delay_ms = 600
        self._solve_start_time: float | None = None
        self._recursive_calls = 0
        self._nodes_expanded = 0

        self._halt_agent = False
        self._agent_timer_job: str | None = None
        self._agent_start_time: float | None = None

        self.AGENT_ALGORITHMS = ("Brute Force", "Backtracking", "Forward Chaining", "Backward Chaining", "A*")
        self.selected_algorithm = tk.StringVar(value="Backtracking")
        self._algo_buttons: dict[str, tk.Button] = {}
        self.SPEED_LEVELS = {1: ("Slow", 500), 2: ("Normal", 150), 3: ("Very Fast", 10)}
        self._speed_var = tk.IntVar(value=2)

        self._manual_play_enabled = False
        self._manual_timer_job: str | None = None
        self._puzzle_loaded_at = perf_counter()
        self._hint_solution_cache: list[list[int | None]] | None = None
        self.input_mode = "cycle"
        self._input_mode_buttons: dict[str, tk.Button] = {}

        self._show_loading_screen(duration_ms=4000)

    def _load_title_art_text(self) -> str:
        candidates = (
            self.project_root / "gui" / "fonts" / "FUTOSHIKI.txt",
            self.project_root / "FUTOSHIKI.txt",
        )

        for candidate in candidates:
            if not (candidate.exists() and candidate.is_file()):
                continue

            try:
                text = candidate.read_text(encoding="utf-8-sig").replace("\r\n", "\n").rstrip("\n")
            except OSError:
                continue

            if text.strip():
                return text

        return "FUTOSHIKI"

    def _show_loading_screen(self, duration_ms: int = 4000) -> None:
        self._loading_canvas = tk.Canvas(
            self,
            bg=BG,
            highlightthickness=0,
            bd=0,
            relief=tk.FLAT,
        )
        self._loading_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.update_idletasks()
        self._draw_background_pattern(self._loading_canvas)

        width = self._loading_canvas.winfo_width()
        height = self._loading_canvas.winfo_height()
        if width <= 1:
            width = max(900, int(float(self._loading_canvas.cget("width") or 900)))
        if height <= 1:
            height = max(620, int(float(self._loading_canvas.cget("height") or 620)))

        line_count = self._title_art_text.count("\n") + 1
        title_font_size = 10 if line_count >= 4 else 12
        title_y = int(height * 0.45)
        footer_y = min(height - 40, title_y + int(line_count * title_font_size * 0.75) + 42)

        self._loading_canvas.create_text(
            width / 2,
            title_y,
            text=self._title_art_text,
            font=mono_font(self, title_font_size, "bold"),
            fill=BORDER,
            justify=tk.CENTER,
        )
        self._loading_canvas.create_text(
            width / 2,
            footer_y,
            text="Loading...",
            font=mono_font(self, 11),
            fill=BORDER,
            justify=tk.CENTER,
        )

        self.after(max(1, duration_ms), self._finish_loading_screen)

    def _finish_loading_screen(self) -> None:
        if self._loading_canvas is not None:
            self._loading_canvas.destroy()
            self._loading_canvas = None

        self.build_layout()
        self._build_menu()
        self._show_start_placeholder()

    def build_layout(self) -> None:
        """Create and place a fixed-header 4-zone grid layout."""
        self.columnconfigure(0, weight=0, minsize=280)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=0, minsize=90)
        self.rowconfigure(1, weight=1)

        self._title_area = tk.Frame(self, bg=BG, width=280, height=90, bd=0, relief=tk.FLAT)
        self._title_area.grid(row=0, column=0, sticky="nsew")
        self._title_area.grid_propagate(False)
        self._title_area.columnconfigure(0, weight=1)
        self._title_area.rowconfigure(0, weight=1)

        tk.Label(
            self._title_area,
            text=self._title_art_text,
            font=mono_font(self, 4),
            fg=BORDER,
            bg=BG,
            anchor="center",
            justify=tk.CENTER,
            padx=2,
        ).grid(row=0, column=0, sticky="nsew")

        self._top_bar_area = tk.Frame(self, bg=BG, height=90, bd=0, relief=tk.FLAT)
        self._top_bar_area.grid(row=0, column=1, sticky="nsew")
        self._top_bar_area.grid_propagate(False)
        self._top_bar_area.columnconfigure(0, weight=1)
        self._top_bar_area.rowconfigure(0, weight=0)
        self._top_bar_area.rowconfigure(1, weight=1)

        self._control_area = tk.Frame(
            self,
            bg=BG,
            width=280,
            padx=0,
            pady=0,
            bd=0,
            relief=tk.FLAT,
        )
        self._control_area.grid(row=1, column=0, sticky="nsew")
        self._control_area.grid_propagate(False)
        self._control_area.columnconfigure(0, weight=1)
        self._control_area.rowconfigure(0, weight=1)

        self._grid_area = tk.Frame(
            self,
            bg=BG,
            padx=16,
            pady=16,
            bd=0,
            relief=tk.FLAT,
        )
        self._grid_area.grid(row=1, column=1, sticky="nsew")
        self._grid_area.columnconfigure(0, weight=1)
        self._grid_area.rowconfigure(0, weight=1)

        self._grid_area_pattern = tk.Canvas(
            self._grid_area,
            bg=BG,
            highlightthickness=0,
            bd=0,
            relief=tk.FLAT,
        )
        self._grid_area_pattern.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._grid_area.bind("<Configure>", self._on_grid_area_resize)
        self._draw_background_pattern(self._grid_area_pattern)

        self.control_panel = ControlPanel(
            self._control_area,
            on_load_puzzle=self.on_load,
            on_solve=self.on_solve,
            on_step=self.on_step,
            on_reset=self.on_reset,
            on_speed_change=self._on_speed_change,
            on_manual_toggle=self.on_manual_toggle,
            on_hint=self.on_hint,
        )
        self.control_panel.grid(row=0, column=0, sticky="nsew")
        self.control_panel.input_mode_var.set(self.input_mode)
        self.control_panel.input_mode_var.trace_add("write", self._on_control_panel_input_mode_change)

    def _build_menu(self) -> None:
        if self._top_bar_area is None:
            return

        for child in self._top_bar_area.winfo_children():
            child.destroy()
        self._input_mode_buttons.clear()
        self._algo_buttons.clear()

        # --- Row 0: Algorithm selector ---
        algo_row = tk.Frame(self._top_bar_area, bg=BG)
        algo_row.grid(row=0, column=0, sticky="ew", padx=12, pady=(8, 0))

        tk.Label(
            algo_row, text="Agent:", bg=BG, fg=BORDER,
            font=mono_font(self, 9, "bold"),
        ).pack(side="left", padx=(0, 8))

        for algo in self.AGENT_ALGORITHMS:
            btn = make_button(algo_row, algo, lambda a=algo: self._select_algorithm(a))
            btn.pack(side="left", padx=3)
            self._algo_buttons[algo] = btn

        self._refresh_algo_buttons()

        # --- Row 1: Action controls ---
        action_row = tk.Frame(self._top_bar_area, bg=BG)
        action_row.grid(row=1, column=0, sticky="ew", padx=12, pady=(4, 8))

        self.btn_run_agent = make_button(action_row, "▶ Run Agent", self.on_run_agent)
        self.btn_run_agent.pack(side="left", padx=(0, 4))

        self.btn_halt_agent = make_button(action_row, "■ Halt", self.on_halt_agent, style="danger")
        self.btn_halt_agent.pack(side="left", padx=4)
        self.btn_halt_agent.configure(state="disabled")

        self.btn_reset_agent = make_button(action_row, "↺ Reset", self.on_reset)
        self.btn_reset_agent.pack(side="left", padx=4)

        # Separator
        sep = tk.Frame(action_row, bg=BORDER, width=1, height=20, bd=0)
        sep.pack(side="left", padx=10, fill="y")

        self.lbl_agent_timer = tk.Label(
            action_row, text="00:00.0s", bg=BG, fg=BORDER,
            font=mono_font(self, 12, "bold"),
        )
        self.lbl_agent_timer.pack(side="left", padx=(6, 12))

        self.lbl_agent_nodes = tk.Label(
            action_row, text="Nodes: 0", bg=BG, fg=BORDER,
            font=mono_font(self, 9),
        )
        self.lbl_agent_nodes.pack(side="left", padx=(0, 12))

        # Speed slider (3 levels)
        sep2 = tk.Frame(action_row, bg=BORDER, width=1, height=20, bd=0)
        sep2.pack(side="left", padx=10, fill="y")
        self._speed_label = tk.Label(
            action_row, text="Normal", bg=BG, fg=BORDER,
            font=mono_font(self, 8), width=9, anchor="center",
        )
        self._speed_label.pack(side="left", padx=(0, 2))
        self._speed_scale = tk.Scale(
            action_row, from_=1, to=3, orient="horizontal",
            variable=self._speed_var,
            bg=BG, fg=BORDER, highlightthickness=0, bd=0,
            length=60, showvalue=False, resolution=1,
            command=self._on_speed_slider_change,
        )
        self._speed_scale.pack(side="left")

    def _select_algorithm(self, algo: str) -> None:
        """Handle clicking an algorithm button in the top bar."""
        self.selected_algorithm.set(algo)
        self._refresh_algo_buttons()

    def _refresh_algo_buttons(self) -> None:
        """Highlight the currently selected algorithm button."""
        current = self.selected_algorithm.get()
        for name, btn in self._algo_buttons.items():
            if name == current:
                btn.configure(bg=BTN_HOVER, fg=BTN_HOVER_TEXT)
                # Override hover bindings so it stays highlighted
                btn.unbind("<Enter>")
                btn.unbind("<Leave>")
                btn.bind("<Enter>", lambda _e, b=btn: b.configure(bg=BTN_HOVER, fg=BTN_HOVER_TEXT))
                btn.bind("<Leave>", lambda _e, b=btn: b.configure(bg=BTN_HOVER, fg=BTN_HOVER_TEXT))
            else:
                btn.configure(bg=BTN_FILL, fg=BTN_TEXT)
                btn.unbind("<Enter>")
                btn.unbind("<Leave>")
                btn.bind("<Enter>", lambda _e, b=btn: b.configure(bg=BTN_HOVER, fg=BTN_HOVER_TEXT))
                btn.bind("<Leave>", lambda _e, b=btn: b.configure(bg=BTN_FILL, fg=BTN_TEXT))

    def on_run_agent(self) -> None:
        if self.grid_widget is None:
            messagebox.showwarning("Run Agent", "Please load a puzzle first.")
            return

        self._halt_agent = False
        self.btn_run_agent.configure(state="disabled")
        self.btn_halt_agent.configure(state="normal")

        self._agent_start_time = perf_counter()
        self._start_agent_timer()

        algorithm = self.selected_algorithm.get()
        self.on_solve(algorithm, self._get_agent_delay_ms())

    def on_halt_agent(self) -> None:
        self._halt_agent = True
        self.btn_halt_agent.configure(state="disabled")

    def _get_agent_delay_ms(self) -> int:
        level = self._speed_var.get()
        _, delay = self.SPEED_LEVELS.get(level, ("Normal", 150))
        return delay

    def _on_speed_slider_change(self, value: str) -> None:
        level = int(value)
        name, delay = self.SPEED_LEVELS.get(level, ("Normal", 150))
        self._animation_delay_ms = delay
        if hasattr(self, '_speed_label'):
            self._speed_label.config(text=name)

    def _start_agent_timer(self) -> None:
        self._stop_agent_timer()
        self._agent_timer_tick()

    def _stop_agent_timer(self) -> None:
        if self._agent_timer_job is not None:
            self.after_cancel(self._agent_timer_job)
            self._agent_timer_job = None

    def _agent_timer_tick(self) -> None:
        if self._agent_start_time is not None:
            elapsed = perf_counter() - self._agent_start_time
            mins = int(elapsed // 60)
            secs = elapsed % 60
            self.lbl_agent_timer.config(text=f"{mins:02d}:{secs:04.1f}s")

        self._agent_timer_job = self.after(100, self._agent_timer_tick)

    @staticmethod
    def _bind_top_button_hover(button: tk.Button) -> None:
        button.bind("<Enter>", lambda _event: button.configure(bg=BTN_HOVER, fg=BTN_HOVER_TEXT))
        button.bind("<Leave>", lambda _event: button.configure(bg=BTN_FILL, fg=BTN_TEXT))

    def _on_grid_area_resize(self, _event: tk.Event) -> None:
        if self._grid_area_pattern is None:
            return
        self._draw_background_pattern(self._grid_area_pattern)

    @staticmethod
    def _draw_background_pattern(canvas: tk.Canvas, spacing: int = 15) -> None:
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width <= 1:
            width = int(float(canvas.cget("width")))
        if height <= 1:
            height = int(float(canvas.cget("height")))

        canvas.delete("bg_pattern")
        for x in range(0, width + 1, spacing):
            canvas.create_line(x, 0, x, height, fill=GRID_PATTERN_COLOR, width=1, tags="bg_pattern")
        for y in range(0, height + 1, spacing):
            canvas.create_line(0, y, width, y, fill=GRID_PATTERN_COLOR, width=1, tags="bg_pattern")

    def _on_control_panel_input_mode_change(self, *_args: object) -> None:
        if self.control_panel is None:
            return
        selected_mode = self.control_panel.input_mode_var.get()
        if selected_mode != self.input_mode:
            self.set_input_mode(selected_mode)

    def _on_mode_button_enter(self, mode: str) -> None:
        button = self._input_mode_buttons.get(mode)
        if button is None:
            return

        if mode == self.input_mode:
            button.configure(bg=BTN_HOVER, fg=BTN_HOVER_TEXT)
            return

        button.configure(bg=BTN_HOVER, fg=BTN_HOVER_TEXT)

    def _refresh_input_mode_buttons(self) -> None:
        for mode, button in self._input_mode_buttons.items():
            if mode == self.input_mode:
                button.configure(
                    bg=BTN_HOVER,
                    fg=BTN_HOVER_TEXT,
                    activebackground=BTN_HOVER,
                    activeforeground=BTN_HOVER_TEXT,
                )
                continue

            button.configure(
                bg=BTN_FILL,
                fg=BTN_TEXT,
                activebackground=BTN_HOVER,
                activeforeground=BTN_HOVER_TEXT,
            )

    def set_input_mode(self, mode: str) -> None:
        if mode not in {"keyboard", "popup", "cycle"}:
            return

        self.input_mode = mode
        self._refresh_input_mode_buttons()
        if self.control_panel is not None and self.control_panel.input_mode_var.get() != mode:
            self.control_panel.input_mode_var.set(mode)

    def on_new_game(self) -> None:
        """TODO: Implement new game action from top bar."""
        # TODO: Wire to puzzle creation/loading flow.

    def on_restart(self) -> None:
        """TODO: Implement restart action from top bar."""
        # TODO: Wire to board reset/restart flow.

    def _show_start_placeholder(self) -> None:
        if self._grid_area is None:
            return

        if self.grid_widget is not None:
            self.grid_widget.destroy()
            self.grid_widget = None

        if self._placeholder_canvas is not None:
            self._placeholder_canvas.destroy()

        # Measure text to size the canvas correctly
        import tkinter.font as tkfont
        measure_font = tkfont.Font(font=mono_font(self, 8, "bold"))
        lines = self._title_art_text.split("\n")
        text_width = max(measure_font.measure(line) for line in lines) + 40
        text_height = measure_font.metrics("linespace") * len(lines) + 40
        canvas_w = max(400, text_width)
        canvas_h = max(400, text_height)

        self._placeholder_canvas = tk.Canvas(
            self._grid_area,
            width=canvas_w,
            height=canvas_h,
            bg=BG,
            highlightthickness=0,
            bd=0,
            relief=tk.FLAT,
        )
        self._placeholder_canvas.place(relx=0.5, rely=0.5, anchor="center")
        self._draw_background_pattern(self._placeholder_canvas)
        self._placeholder_canvas.create_text(
            canvas_w / 2,
            canvas_h / 2,
            text=self._title_art_text,
            font=mono_font(self, 8, "bold"),
            fill=BORDER,
            justify=tk.CENTER,
        )

    def bind_events(self) -> None:
        """Reserved for global event bindings.

        TODO: Add app-level keyboard shortcuts after gameplay controls stabilize.
        """

    def on_load(self, filename: str) -> None:
        """Parse a puzzle file and rebuild the grid with the loaded size N."""
        self._cancel_animation()

        try:
            file_path = self._resolve_puzzle_file(filename)
            N, grid, h_constraints, v_constraints = self._parse_puzzle_file(file_path)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Load Puzzle", str(exc))
            return

        self.current_N = N
        self.current_grid = grid
        self.current_h_constraints = h_constraints
        self.current_v_constraints = v_constraints
        self.initial_grid = copy.deepcopy(grid)
        self._puzzle_loaded_at = perf_counter()
        self._hint_solution_cache = None

        self._solver_algorithm = None
        self._solver_runner = None
        self._rebuild_grid_widget()
        self._reset_stats_state()
        self._refresh_manual_timer_label()
        if self._manual_play_enabled:
            self._start_manual_timer()

    def _new_blank_puzzle(self, N: int) -> None:
        self._cancel_animation()
        self._stop_manual_timer()

        self.current_N = N
        self.current_grid = [[0 for _ in range(N)] for _ in range(N)]
        self.current_h_constraints = [["" for _ in range(max(N - 1, 0))] for _ in range(N)]
        self.current_v_constraints = [["" for _ in range(N)] for _ in range(max(N - 1, 0))]
        self.initial_grid = copy.deepcopy(self.current_grid)
        self._puzzle_loaded_at = perf_counter()
        self._hint_solution_cache = None
        self._solver_algorithm = None
        self._solver_runner = None

        self._rebuild_grid_widget()
        self._reset_stats_state()
        self._refresh_manual_timer_label()
        if self._manual_play_enabled:
            self._start_manual_timer()

        if self.control_panel is not None:
            self.control_panel.selected_puzzle_path_var.set(f"Blank {N}×{N}")
        self.set_input_mode("cycle")

    def on_solve(self, algorithm: str, delay_ms: int) -> None:
        """Run the selected algorithm and animate assignments onto the grid."""
        if self._manual_play_enabled:
            return
        if self.grid_widget is None:
            print("[WARN] on_solve: no puzzle loaded yet.", file=sys.stderr)
            return

        self._cancel_animation()
        self._solver_algorithm = algorithm
        self._animation_delay_ms = max(1, int(delay_ms))
        self._solver_runner = self._build_solver_runner(algorithm)
        if self._solver_runner is None:
            messagebox.showerror("Solve", f"Unsupported solver: {algorithm}")
            return
        self._start_stats_state()
        self._schedule_next_animation_step()

    def on_step(self, algorithm: str) -> None:
        """Advance the selected solver by one assignment for visualization."""
        if self._manual_play_enabled:
            return
        if self.grid_widget is None:
            print("[WARN] on_step: no puzzle loaded yet.", file=sys.stderr)
            return

        self._cancel_animation()
        if self._solver_runner is None or self._solver_algorithm != algorithm:
            self._solver_algorithm = algorithm
            self._solver_runner = self._build_solver_runner(algorithm)
            if self._solver_runner is None:
                messagebox.showerror("Step", f"Unsupported solver: {algorithm}")
                return
            self._start_stats_state()

        if self._apply_next_solver_step():
            self._update_stats_view()
        else:
            self._finish_animation_session(halted=False)

    def on_reset(self) -> None:
        """Restore original clues and remove all player/solver entries."""
        self._cancel_animation()
        if self._manual_timer_job is not None:
            self.after_cancel(self._manual_timer_job)
            self._manual_timer_job = None
        self._stop_manual_timer()

        self.current_grid = copy.deepcopy(self.initial_grid)
        self._solver_runner = None
        self._solver_algorithm = None
        self._rebuild_grid_widget()
        self._reset_stats_state()

    def on_manual_toggle(self, enabled: bool) -> None:
        """Enable or disable Manual Play interactions and timer updates."""
        self._manual_play_enabled = enabled
        self._cancel_animation()
        self._solver_runner = None
        self._solver_algorithm = None

        if self.grid_widget is not None:
            self.grid_widget.set_keyboard_enabled(enabled)

        if enabled:
            self._refresh_manual_timer_label()
            self._start_manual_timer()
            return

        self._stop_manual_timer()

    def on_hint(self) -> None:
        """Reveal one empty cell using a backtracking-derived solution."""
        if not self._manual_play_enabled:
            return
        if self.grid_widget is None:
            print("[WARN] on_hint: no puzzle loaded yet.", file=sys.stderr)
            return

        target_cell: tuple[int, int] | None = None
        for i in range(self.current_N):
            for j in range(self.current_N):
                if self.grid_widget.board[i][j] is None and (i, j) not in self.grid_widget.given_cells:
                    target_cell = (i, j)
                    break
            if target_cell is not None:
                break

        if target_cell is None:
            messagebox.showinfo("Hint", "No empty cells available for a hint.")
            return

        solution = self._get_hint_solution()
        if solution is None:
            messagebox.showerror("Hint", "No valid solution was found for this puzzle.")
            return

        i, j = target_cell
        hint_value = solution[i][j]
        if hint_value is None:
            messagebox.showerror("Hint", "Could not compute a hint value for the selected cell.")
            return

        self.grid_widget.set_value(i, j, hint_value, mode="hint")
        self.current_grid = copy.deepcopy(self.grid_widget.board)

        # TODO: Prefer strategy-aware hint selection instead of first-empty behavior.

    def _on_speed_change(self, delay_ms: int) -> None:
        """Receive speed slider updates from the control panel."""
        self._animation_delay_ms = max(1, int(delay_ms))

    def _rebuild_grid_widget(self) -> None:
        if self._grid_area is None:
            return

        if self._placeholder_canvas is not None:
            self._placeholder_canvas.destroy()
            self._placeholder_canvas = None

        if self.grid_widget is not None:
            self.grid_widget.destroy()

        self.grid_widget = FutoshikiGrid(
            self._grid_area,
            N=self.current_N,
            grid=copy.deepcopy(self.current_grid),
            h_constraints=copy.deepcopy(self.current_h_constraints),
            v_constraints=copy.deepcopy(self.current_v_constraints),
            get_input_mode=lambda: self.input_mode,
        )
        self.grid_widget.set_keyboard_enabled(self._manual_play_enabled)
        self.grid_widget.pack(expand=True, fill="both")
        tk.Misc.tkraise(self.grid_widget)

    def _cancel_animation(self) -> None:
        if self._animation_job is not None:
            self.after_cancel(self._animation_job)
            self._animation_job = None

    def _schedule_next_animation_step(self) -> None:
        self._animation_job = self.after(self._animation_delay_ms, self._run_animation_step)

    def _run_animation_step(self) -> None:
        self._animation_job = None
        
        if self._halt_agent:
            self._finish_animation_session(halted=True)
            return

        if self._apply_next_solver_step():
            self._update_stats_view()
            self._schedule_next_animation_step()
            return

        self._finish_animation_session(halted=False)

    def _apply_next_solver_step(self) -> bool:
        if self.grid_widget is None or self._solver_runner is None:
            return False

        step = self._solver_runner.next_step()
        if step is None:
            return False

        should_continue = self._apply_solver_event(step)
        self.current_grid = copy.deepcopy(self.grid_widget.board)
        return should_continue

    def _build_solver_runner(self, algorithm: str) -> SolverRunner | None:
        if self.grid_widget is None:
            return None

        solver_factory = SOLVER_GENERATORS.get(algorithm)
        if solver_factory is None:
            return None

        generator = solver_factory(
            grid=copy.deepcopy(self.grid_widget.board),
            h_constraints=copy.deepcopy(self.current_h_constraints),
            v_constraints=copy.deepcopy(self.current_v_constraints),
            N=self.current_N,
        )
        return SolverRunner(generator)

    def _apply_solver_event(self, event: SolverEvent) -> bool:
        if self.grid_widget is None:
            return False

        event_type, i, j, v = event
        if event_type == "try":
            if i is None or j is None or v is None:
                return False
            self.grid_widget.set_value(i, j, v, mode="algo")
            self._nodes_expanded += 1
            if hasattr(self, 'lbl_agent_nodes'):
                self.lbl_agent_nodes.config(text=f"Nodes: {self._nodes_expanded}")
            return True

        if event_type == "backtrack":
            if i is None or j is None:
                return False
            self.grid_widget.clear_value(i, j)
            self._recursive_calls += 1
            self._nodes_expanded += 1
            if hasattr(self, 'lbl_agent_nodes'):
                self.lbl_agent_nodes.config(text=f"Nodes: {self._nodes_expanded}")
            return True

        if event_type == "solved":
            return False

        # TODO: Handle additional visualization event types if solvers emit richer traces.
        return True

    def _start_stats_state(self) -> None:
        self._solve_start_time = perf_counter()
        self._recursive_calls = 0
        self._nodes_expanded = 0
        if self.control_panel is not None:
            self.control_panel.reset_stats()

    def _finish_animation_session(self, halted: bool = False) -> None:
        self._cancel_animation()
        self._update_stats_view()
        self._stop_agent_timer()
        
        if hasattr(self, 'btn_run_agent'):
            self.btn_run_agent.configure(state="normal")
            self.btn_halt_agent.configure(state="disabled")

        if not halted and self._solve_start_time is not None:
            elapsed = perf_counter() - self._solve_start_time
            messagebox.showinfo(
                "Solver Agent Finished!",
                f"Solver Agent Finished!\n\nTotal Time Taken: {elapsed:.3f}s\nNodes Expanded: {self._nodes_expanded}"
            )

    def _reset_stats_state(self) -> None:
        self._solve_start_time = None
        self._recursive_calls = 0
        self._nodes_expanded = 0
        self._stop_agent_timer()
        if hasattr(self, 'lbl_agent_timer'):
            self.lbl_agent_timer.config(text="00:00.0s")
        if hasattr(self, 'lbl_agent_nodes'):
            self.lbl_agent_nodes.config(text="Nodes: 0")
        if hasattr(self, 'btn_run_agent'):
            self.btn_run_agent.configure(state="normal")
            self.btn_halt_agent.configure(state="disabled")
        if self.control_panel is not None:
            self.control_panel.reset_stats()

    def _update_stats_view(self) -> None:
        if self.control_panel is None:
            return

        elapsed = 0.0
        if self._solve_start_time is not None:
            elapsed = perf_counter() - self._solve_start_time

        self.control_panel.update_stats(
            time_elapsed=elapsed,
            recursive_calls=self._recursive_calls,
            nodes_expanded=self._nodes_expanded,
        )

    def _get_hint_solution(self) -> list[list[int | None]] | None:
        if self._hint_solution_cache is not None:
            return copy.deepcopy(self._hint_solution_cache)

        simulated_grid = copy.deepcopy(self.initial_grid)
        generator = backtracking_solver_gen(
            grid=copy.deepcopy(self.initial_grid),
            h_constraints=copy.deepcopy(self.current_h_constraints),
            v_constraints=copy.deepcopy(self.current_v_constraints),
            N=self.current_N,
        )

        for event_type, i, j, v in generator:
            if event_type == "try":
                if i is None or j is None or v is None:
                    continue
                simulated_grid[i][j] = v
                continue

            if event_type == "backtrack":
                if i is None or j is None:
                    continue
                simulated_grid[i][j] = None
                continue

            if event_type == "solved":
                self._hint_solution_cache = copy.deepcopy(simulated_grid)
                return copy.deepcopy(self._hint_solution_cache)

        return None

    def _start_manual_timer(self) -> None:
        self._stop_manual_timer()
        self._manual_timer_job = self.after(1000, self._manual_timer_tick)

    def _stop_manual_timer(self) -> None:
        if self._manual_timer_job is not None:
            self.after_cancel(self._manual_timer_job)
            self._manual_timer_job = None

    def _manual_timer_tick(self) -> None:
        self._manual_timer_job = None
        self._refresh_manual_timer_label()
        if self._manual_play_enabled:
            self._manual_timer_job = self.after(1000, self._manual_timer_tick)

    def _refresh_manual_timer_label(self) -> None:
        if self.control_panel is None:
            return
        elapsed = perf_counter() - self._puzzle_loaded_at
        self.control_panel.update_manual_timer(elapsed)

    def _resolve_puzzle_file(self, filename: str) -> Path:
        cleaned = filename.strip().strip("\"").strip("'")
        requested = Path(cleaned)

        if requested.is_absolute():
            candidates = (requested,)
        else:
            candidates = (
                self.project_root / requested,
                self.project_root / "inputs" / requested,
                self.project_root / "inputs" / requested.name,
                self.project_root / "puzzle_inputs" / "Inputs" / requested,
                self.project_root / "puzzle_inputs" / "Inputs" / requested.name,
                self.project_root / "puzzles" / requested,
                Path.cwd() / requested,
            )

        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                return candidate.resolve()

        raise ValueError(f"Puzzle file not found: {filename}")

    def _parse_puzzle_file(
        self,
        file_path: Path,
    ) -> tuple[int, list[list[int | None]], list[list[str]], list[list[str]]]:
        """Parse input via the shared team parser and convert into GUI symbols."""
        raw_text = file_path.read_text(encoding="utf-8-sig")
        puzzle = parse_puzzle_text(raw_text)

        N = puzzle.n
        if N not in {4, 5, 6, 7, 9}:
            raise ValueError(f"Unsupported grid size {N}; expected one of 4, 5, 6, 7, 9.")

        grid = [
            [None if value == 0 else value for value in row]
            for row in puzzle.grid
        ]
        h_constraints = [
            ["<" if relation == 1 else ">" if relation == -1 else "" for relation in row]
            for row in puzzle.horizontal
        ]
        v_constraints = [
            ["^" if relation == 1 else "v" if relation == -1 else "" for relation in row]
            for row in puzzle.vertical
        ]

        return N, grid, h_constraints, v_constraints

    def _parse_grid_row(self, line: str, N: int) -> list[int | None]:
        tokens = self._split_tokens(line)
        if len(tokens) == 1 and len(tokens[0]) == N:
            tokens = list(tokens[0])
        if len(tokens) != N:
            raise ValueError(f"Invalid grid row '{line}': expected {N} entries.")

        row: list[int | None] = []
        for token in tokens:
            if token in {".", "0", "-", "_"}:
                row.append(None)
                continue

            try:
                value = int(token)
            except ValueError as exc:
                raise ValueError(f"Invalid grid value '{token}' in row '{line}'.") from exc

            if not (1 <= value <= N):
                raise ValueError(f"Grid value '{value}' out of range 1..{N}.")
            row.append(value)

        return row

    def _parse_constraint_row(self, line: str, expected_len: int, allowed: set[str]) -> list[str]:
        tokens = self._split_tokens(line)
        if len(tokens) == 1 and len(tokens[0]) == expected_len:
            tokens = list(tokens[0])
        if len(tokens) != expected_len:
            raise ValueError(
                f"Invalid constraint row '{line}': expected {expected_len} entries."
            )

        is_horizontal = "<" in allowed and ">" in allowed
        is_vertical = "^" in allowed and "v" in allowed

        row: list[str] = []
        for token in tokens:
            if token in allowed:
                row.append(token)
            elif token in {".", "0", "-", "_"}:
                row.append("")
            elif token in {"1", "+1"}:
                if is_horizontal:
                    row.append("<")
                elif is_vertical:
                    row.append("^")
                else:
                    raise ValueError(f"Invalid constraint token '{token}' in row '{line}'.")
            elif token == "-1":
                if is_horizontal:
                    row.append(">")
                elif is_vertical:
                    row.append("v")
                else:
                    raise ValueError(f"Invalid constraint token '{token}' in row '{line}'.")
            else:
                raise ValueError(f"Invalid constraint token '{token}' in row '{line}'.")

        return row

    @staticmethod
    def _split_tokens(line: str) -> list[str]:
        return [token for token in line.replace(",", " ").split() if token]

    @staticmethod
    def _parse_size_line(first_line: str, file_path: Path) -> int:
        stripped = first_line.strip().lstrip("\ufeff")

        if stripped.isdigit():
            return int(stripped)

        match = re.match(r"^[Nn]\s*[:=]?\s*(\d+)\s*$", stripped)
        if match is not None:
            return int(match.group(1))

        raise ValueError(
            "First non-empty line must be an integer grid size N "
            f"(example: '4'). Got '{stripped}' in {file_path.name}."
        )
