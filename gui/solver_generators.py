"""Generator-based Futoshiki solver adapters.

Each solver yields UI-friendly events in the form:
(event_type, i, j, v)

Event types:
- "try": set value v at cell (i, j)
- "backtrack": clear cell (i, j)
- "solved": puzzle is complete
"""

from __future__ import annotations

import copy
import heapq
import itertools
import os
import sys
from collections import deque
from collections.abc import Generator

# Ensure src/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from futoshiki.solvers.brute_force import brute_force_gen as _src_brute_force_gen
from futoshiki.solvers.backtracking import backtracking_gen as _src_backtracking_gen
from futoshiki.solvers.brute_force import is_valid as _brute_is_valid
from futoshiki.solvers.astar import (
    ac3 as _astar_ac3,
    get_h_base as _astar_get_h_base,
    get_h_tie as _astar_get_h_tie,
    lcv_sort as _astar_lcv_sort,
)

SolverEvent = tuple[str, int | None, int | None, int | None]
SolverGen = Generator[SolverEvent, None, None]


# ---------------------------------------------------------------------------
#  Constraint symbol helpers (GUI uses str symbols, src uses int signs)
# ---------------------------------------------------------------------------

def _h_sym_to_int(h_constraints: list[list[str]]) -> list[list[int]]:
    """Convert GUI horizontal constraints ('<', '>', '') to int (-1, 0, 1)."""
    return [
        [1 if c == "<" else -1 if c == ">" else 0 for c in row]
        for row in h_constraints
    ]


def _v_sym_to_int(v_constraints: list[list[str]]) -> list[list[int]]:
    """Convert GUI vertical constraints ('^', 'v', '') to int (-1, 0, 1)."""
    return [
        [1 if c == "^" else -1 if c == "v" else 0 for c in row]
        for row in v_constraints
    ]


def _grid_none_to_zero(grid: list[list[int | None]]) -> list[list[int]]:
    """Convert GUI grid (None=empty) to solver grid (0=empty)."""
    return [[0 if v is None else v for v in row] for row in grid]


def _normalize_event(event: tuple) -> SolverEvent:
    """Normalize variable-length src solver events into 4-tuples."""
    etype = event[0]
    if etype == "try":
        return (etype, event[1], event[2], event[3])
    if etype == "backtrack":
        return (etype, event[1], event[2], None)
    if etype == "solved":
        return (etype, None, None, None)
    # Unknown event type — pass through with padding
    return (etype, None, None, None)


# ---------------------------------------------------------------------------
#  1. Brute Force — delegates to src/futoshiki/solvers/brute_force.py
# ---------------------------------------------------------------------------

def brute_force_solver_gen(
    grid: list[list[int | None]],
    h_constraints: list[list[str]],
    v_constraints: list[list[str]],
    N: int,
) -> SolverGen:
    """Yield brute-force style search steps for visualization."""
    int_grid = _grid_none_to_zero(grid)
    int_h = _h_sym_to_int(h_constraints)
    int_v = _v_sym_to_int(v_constraints)
    for event in _src_brute_force_gen(int_grid, int_h, int_v, N):
        yield _normalize_event(event)


# ---------------------------------------------------------------------------
#  2. Backtracking (MRV) — delegates to src/futoshiki/solvers/backtracking.py
# ---------------------------------------------------------------------------

def backtracking_solver_gen(
    grid: list[list[int | None]],
    h_constraints: list[list[str]],
    v_constraints: list[list[str]],
    N: int,
) -> SolverGen:
    """Yield classic backtracking assignment and undo events."""
    int_grid = _grid_none_to_zero(grid)
    int_h = _h_sym_to_int(h_constraints)
    int_v = _v_sym_to_int(v_constraints)
    for event in _src_backtracking_gen(int_grid, int_h, int_v, N):
        yield _normalize_event(event)


# ---------------------------------------------------------------------------
#  3. Forward Chaining — domain-pruning style generator
# ---------------------------------------------------------------------------

def forward_chaining_solver_gen(
    grid: list[list[int | None]],
    h_constraints: list[list[str]],
    v_constraints: list[list[str]],
    N: int,
) -> SolverGen:
    """Yield forward-chaining (arc consistency + backtracking) steps.

    Uses domain pruning with arc consistency propagation.  When propagation
    alone cannot solve the puzzle, it falls back to search (guess + propagate).
    """
    int_grid = _grid_none_to_zero(grid)
    int_h = _h_sym_to_int(h_constraints)
    int_v = _v_sym_to_int(v_constraints)

    # Build initial domains
    domains: list[list[list[int]]] = []
    for r in range(N):
        row_d: list[list[int]] = []
        for c in range(N):
            if int_grid[r][c] != 0:
                row_d.append([int_grid[r][c]])
            else:
                row_d.append(list(range(1, N + 1)))
        domains.append(row_d)

    # Initial AC-3 propagation
    if not _fc_ac3(N, domains, int_h, int_v):
        return  # Inconsistent from the start

    # Assign any cells that have been reduced to a single value
    for r in range(N):
        for c in range(N):
            if len(domains[r][c]) == 1 and int_grid[r][c] == 0:
                v = domains[r][c][0]
                int_grid[r][c] = v
                yield ("try", r, c, v)

    # Search with propagation
    yield from _fc_search(int_grid, domains, int_h, int_v, N)


def _fc_ac3(
    N: int,
    domains: list[list[list[int]]],
    h_con: list[list[int]],
    v_con: list[list[int]],
    assigned_cell: tuple[int, int] | None = None,
) -> bool:
    """AC-3 arc consistency propagation. Returns False if a domain becomes empty."""
    queue: deque[tuple[int, int, int, int]] = deque()

    if assigned_cell:
        r, c = assigned_cell
        for nr, nc in _fc_neighbors(r, c, N):
            queue.append((nr, nc, r, c))
    else:
        for r in range(N):
            for c in range(N):
                for nr, nc in _fc_neighbors(r, c, N):
                    queue.append((r, c, nr, nc))

    while queue:
        r1, c1, r2, c2 = queue.popleft()
        if _fc_revise(domains, r1, c1, r2, c2, h_con, v_con):
            if len(domains[r1][c1]) == 0:
                return False
            for nr, nc in _fc_neighbors(r1, c1, N):
                if (nr, nc) != (r2, c2):
                    queue.append((nr, nc, r1, c1))
    return True


def _fc_neighbors(r: int, c: int, N: int) -> list[tuple[int, int]]:
    neighbors = set()
    for i in range(N):
        if i != c:
            neighbors.add((r, i))
        if i != r:
            neighbors.add((i, c))
    return list(neighbors)


def _fc_revise(
    domains: list[list[list[int]]],
    r1: int, c1: int, r2: int, c2: int,
    h_con: list[list[int]], v_con: list[list[int]],
) -> bool:
    revised = False
    to_remove = []
    for v1 in domains[r1][c1]:
        if not any(_fc_check(r1, c1, v1, r2, c2, v2, h_con, v_con) for v2 in domains[r2][c2]):
            to_remove.append(v1)
    for v in to_remove:
        domains[r1][c1].remove(v)
        revised = True
    return revised


def _fc_check(r1, c1, v1, r2, c2, v2, h_con, v_con) -> bool:
    if r1 == r2 or c1 == c2:
        if v1 == v2:
            return False
    if r1 == r2:
        if c2 == c1 + 1:
            if h_con[r1][c1] == 1 and not (v1 < v2):
                return False
            if h_con[r1][c1] == -1 and not (v1 > v2):
                return False
        elif c1 == c2 + 1:
            if h_con[r2][c2] == 1 and not (v1 > v2):
                return False
            if h_con[r2][c2] == -1 and not (v1 < v2):
                return False
    if c1 == c2:
        if r2 == r1 + 1:
            if v_con[r1][c1] == 1 and not (v1 < v2):
                return False
            if v_con[r1][c1] == -1 and not (v1 > v2):
                return False
        elif r1 == r2 + 1:
            if v_con[r2][c2] == 1 and not (v1 > v2):
                return False
            if v_con[r2][c2] == -1 and not (v1 < v2):
                return False
    return True


def _fc_search(
    grid: list[list[int]],
    domains: list[list[list[int]]],
    h_con: list[list[int]],
    v_con: list[list[int]],
    N: int,
) -> Generator[SolverEvent, None, bool]:
    # Find unassigned cell with smallest domain (MRV)
    best_cell = None
    best_len = N + 1
    for r in range(N):
        for c in range(N):
            if grid[r][c] == 0:
                dl = len(domains[r][c])
                if dl < best_len:
                    best_len = dl
                    best_cell = (r, c)

    if best_cell is None:
        yield ("solved", None, None, None)
        return True

    r, c = best_cell
    for v in list(domains[r][c]):
        # Save state
        old_domains = [[list(d) for d in row] for row in domains]
        grid[r][c] = v
        domains[r][c] = [v]
        yield ("try", r, c, v)

        if _fc_ac3(N, domains, h_con, v_con, assigned_cell=(r, c)):
            # Assign any newly-fixed cells
            newly_fixed: list[tuple[int, int, int]] = []
            for rr in range(N):
                for cc in range(N):
                    if len(domains[rr][cc]) == 1 and grid[rr][cc] == 0:
                        fv = domains[rr][cc][0]
                        grid[rr][cc] = fv
                        newly_fixed.append((rr, cc, fv))
                        yield ("try", rr, cc, fv)

            solved = yield from _fc_search(grid, domains, h_con, v_con, N)
            if solved:
                return True

            # Undo newly fixed cells
            for rr, cc, fv in reversed(newly_fixed):
                grid[rr][cc] = 0
                yield ("backtrack", rr, cc, None)

        # Restore
        grid[r][c] = 0
        for rr in range(N):
            for cc in range(N):
                domains[rr][cc] = old_domains[rr][cc]
        yield ("backtrack", r, c, None)

    return False


# ---------------------------------------------------------------------------
#  4. A* Search — priority-queue based generator
# ---------------------------------------------------------------------------

def a_star_solver_gen(
    grid: list[list[int | None]],
    h_constraints: list[list[str]],
    v_constraints: list[list[str]],
    N: int,
) -> SolverGen:
    """Yield A* search steps for visualization.

    Uses the real A* solver logic from src/futoshiki/solvers/astar.py
    with AC-3 propagation, MRV cell selection, and LCV value ordering.
    Each state expansion emits events to visualize progress on the grid.
    """
    int_grid = _grid_none_to_zero(grid)
    int_h = _h_sym_to_int(h_constraints)
    int_v = _v_sym_to_int(v_constraints)

    # Build initial domains
    initial_domains: list[list[list[int]]] = []
    for r in range(N):
        row_d: list[list[int]] = []
        for c in range(N):
            if int_grid[r][c] != 0:
                row_d.append([int_grid[r][c]])
            else:
                row_d.append(list(range(1, N + 1)))
        initial_domains.append(row_d)

    if not _astar_ac3(N, initial_domains, int_h, int_v):
        return  # No solution

    counter = itertools.count()
    open_list: list = []
    best_g: dict = {}

    initial_state = [row[:] for row in int_grid]
    g = 0
    h_base = _astar_get_h_base(initial_state, N)
    f = g + h_base
    h_tie = _astar_get_h_tie(initial_domains, initial_state, N)

    heapq.heappush(open_list, (f, h_tie, g, next(counter), initial_state, initial_domains))

    # Track what is currently displayed on the GUI grid so we can diff
    displayed = [row[:] for row in int_grid]

    while open_list:
        curr_f, curr_h_tie, curr_g, _, curr_state, curr_domains = heapq.heappop(open_list)

        state_key = (
            tuple(tuple(row) for row in curr_state),
            tuple(tuple(tuple(d) for d in row) for row in curr_domains),
        )
        if state_key in best_g and best_g[state_key] <= curr_g:
            continue
        best_g[state_key] = curr_g

        curr_h_base = curr_f - curr_g

        # Emit events to update the display to match curr_state
        for r in range(N):
            for c in range(N):
                if curr_state[r][c] != displayed[r][c]:
                    if curr_state[r][c] != 0:
                        yield ("try", r, c, curr_state[r][c])
                    else:
                        yield ("backtrack", r, c, None)
                    displayed[r][c] = curr_state[r][c]

        if curr_h_base == 0:
            yield ("solved", None, None, None)
            return

        # Select cell with smallest domain (MRV)
        min_len = float("inf")
        best_cell = None
        for r in range(N):
            for c in range(N):
                if curr_state[r][c] == 0:
                    dl = len(curr_domains[r][c])
                    if dl < min_len:
                        min_len = dl
                        best_cell = (r, c)

        if not best_cell:
            continue

        r, c = best_cell
        sorted_values = _astar_lcv_sort(
            curr_domains[r][c], r, c, curr_domains, N, int_h, int_v
        )

        for val in sorted_values:
            child_state = [row[:] for row in curr_state]
            child_state[r][c] = val

            child_domains = [[list(d) for d in row] for row in curr_domains]
            child_domains[r][c] = [val]

            if _astar_ac3(N, child_domains, int_h, int_v, assigned_cell=(r, c)):
                child_g = curr_g + 1
                child_h_base = _astar_get_h_base(child_state, N)
                child_f = child_g + child_h_base
                child_h_tie = _astar_get_h_tie(child_domains, child_state, N)

                heapq.heappush(
                    open_list,
                    (child_f, child_h_tie, child_g, next(counter), child_state, child_domains),
                )


# ---------------------------------------------------------------------------
#  5. Backward Chaining — FOL deductive solver generator
# ---------------------------------------------------------------------------

from futoshiki.solvers.backward_chaining import solve_deductive as _bc_solve_deductive
from futoshiki.solvers.brute_force import is_valid as _bc_is_valid_check


def backward_chaining_solver_gen(
    grid: list[list[int | None]],
    h_constraints: list[list[str]],
    v_constraints: list[list[str]],
    N: int,
) -> SolverGen:
    """Yield backward-chaining deductive steps for visualization.

    Pre-computes the solution using the FOL backward chaining solver,
    then replays the assignments as GUI events. If pure deduction stalls,
    falls back to backtracking search for remaining cells.
    """
    int_grid = _grid_none_to_zero(grid)
    int_h = _h_sym_to_int(h_constraints)
    int_v = _v_sym_to_int(v_constraints)

    # Run the deductive solver to completion
    solution, _stats = _bc_solve_deductive(N, int_grid, int_h, int_v)

    # Collect which cells were filled by deduction (not original clues)
    deduced: list[tuple[int, int, int]] = []
    for r in range(N):
        for c in range(N):
            if int_grid[r][c] == 0 and solution[r][c] != 0:
                deduced.append((r, c, solution[r][c]))

    # Yield deduced assignments
    for r, c, v in deduced:
        yield ("try", r, c, v)

    # Check if there are remaining empty cells — fill with backtracking
    remaining: list[tuple[int, int]] = []
    for r in range(N):
        for c in range(N):
            if solution[r][c] == 0:
                remaining.append((r, c))

    if remaining:
        yield from _bc_backtrack_remaining(solution, remaining, 0, int_h, int_v, N)

    # Final solved event
    is_complete = all(solution[r][c] != 0 for r in range(N) for c in range(N))
    if is_complete:
        yield ("solved", None, None, None)


def _bc_backtrack_remaining(
    grid: list[list[int]],
    cells: list[tuple[int, int]],
    idx: int,
    h_con: list[list[int]],
    v_con: list[list[int]],
    N: int,
) -> Generator[SolverEvent, None, bool]:
    """Backtrack over cells that deduction couldn't resolve."""
    if idx >= len(cells):
        return True

    r, c = cells[idx]
    for v in range(1, N + 1):
        if _brute_is_valid(grid, r, c, v, h_con, v_con, N):
            grid[r][c] = v
            yield ("try", r, c, v)

            solved = yield from _bc_backtrack_remaining(grid, cells, idx + 1, h_con, v_con, N)
            if solved:
                return True

            grid[r][c] = 0
            yield ("backtrack", r, c, None)

    return False


# ---------------------------------------------------------------------------
#  Registry
# ---------------------------------------------------------------------------

SOLVER_GENERATORS = {
    "Brute Force": brute_force_solver_gen,
    "Backtracking": backtracking_solver_gen,
    "Forward Chaining": forward_chaining_solver_gen,
    "Backward Chaining": backward_chaining_solver_gen,
    "A*": a_star_solver_gen,
}
