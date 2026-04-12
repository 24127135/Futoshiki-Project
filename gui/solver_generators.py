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
from collections.abc import Generator

SolverEvent = tuple[str, int | None, int | None, int | None]
SolverGen = Generator[SolverEvent, None, None]


def brute_force_solver_gen(
    grid: list[list[int | None]],
    h_constraints: list[list[str]],
    v_constraints: list[list[str]],
    N: int,
) -> SolverGen:
    """Yield brute-force style search steps for visualization.

    TODO: Separate strict brute-force behavior from shared backtracking helper.
    """
    board = _copy_grid(grid, N)
    yield from _search(board, h_constraints, v_constraints, N, strategy="brute_force")


def backtracking_solver_gen(
    grid: list[list[int | None]],
    h_constraints: list[list[str]],
    v_constraints: list[list[str]],
    N: int,
) -> SolverGen:
    """Yield classic backtracking assignment and undo events."""
    board = _copy_grid(grid, N)
    yield from _search(board, h_constraints, v_constraints, N, strategy="backtracking")


def forward_chaining_solver_gen(
    grid: list[list[int | None]],
    h_constraints: list[list[str]],
    v_constraints: list[list[str]],
    N: int,
) -> SolverGen:
    """Yield forward-chaining style steps using a constrained-cell ordering.

    TODO: Add explicit domain-pruning trace events for forward chaining.
    """
    board = _copy_grid(grid, N)
    yield from _search(board, h_constraints, v_constraints, N, strategy="forward_chaining")


def a_star_solver_gen(
    grid: list[list[int | None]],
    h_constraints: list[list[str]],
    v_constraints: list[list[str]],
    N: int,
) -> SolverGen:
    """Yield A*-style events.

    TODO: Replace placeholder depth-first traversal with a real A* frontier.
    """
    board = _copy_grid(grid, N)
    yield from _search(board, h_constraints, v_constraints, N, strategy="a_star")


def _search(
    board: list[list[int | None]],
    h_constraints: list[list[str]],
    v_constraints: list[list[str]],
    N: int,
    strategy: str,
) -> Generator[SolverEvent, None, bool]:
    next_cell = _select_next_cell(board, h_constraints, v_constraints, N, strategy)
    if next_cell is None:
        if _is_complete_and_valid(board, h_constraints, v_constraints, N):
            yield ("solved", None, None, None)
            return True
        return False

    i, j = next_cell
    candidates = _candidate_values(board, i, j, h_constraints, v_constraints, N)

    for v in candidates:
        yield ("try", i, j, v)
        board[i][j] = v

        solved = yield from _search(board, h_constraints, v_constraints, N, strategy)
        if solved:
            return True

        board[i][j] = None
        yield ("backtrack", i, j, None)

    return False


def _select_next_cell(
    board: list[list[int | None]],
    h_constraints: list[list[str]],
    v_constraints: list[list[str]],
    N: int,
    strategy: str,
) -> tuple[int, int] | None:
    empty_cells = [(i, j) for i in range(N) for j in range(N) if board[i][j] is None]
    if not empty_cells:
        return None

    if strategy in {"forward_chaining", "a_star"}:
        # Prefer cells with fewer legal candidates to visualize stronger inference.
        return min(
            empty_cells,
            key=lambda cell: len(
                _candidate_values(board, cell[0], cell[1], h_constraints, v_constraints, N)
            ),
        )

    # Brute force and backtracking currently scan in row-major order.
    return empty_cells[0]


def _candidate_values(
    board: list[list[int | None]],
    i: int,
    j: int,
    h_constraints: list[list[str]],
    v_constraints: list[list[str]],
    N: int,
) -> list[int]:
    values: list[int] = []
    for v in range(1, N + 1):
        board[i][j] = v
        if _check_cell_valid(board, i, j, h_constraints, v_constraints, N):
            values.append(v)
        board[i][j] = None
    return values


def _check_cell_valid(
    grid: list[list[int | None]],
    i: int,
    j: int,
    h_constraints: list[list[str]],
    v_constraints: list[list[str]],
    N: int,
) -> bool:
    value = grid[i][j]
    if value is None or not (1 <= value <= N):
        return False

    for col in range(N):
        if col != j and grid[i][col] == value:
            return False

    for row in range(N):
        if row != i and grid[row][j] == value:
            return False

    if j > 0 and i < len(h_constraints) and (j - 1) < len(h_constraints[i]):
        sign = h_constraints[i][j - 1]
        left = grid[i][j - 1]
        if sign == "<" and left is not None and not (left < value):
            return False
        if sign == ">" and left is not None and not (left > value):
            return False

    if j < (N - 1) and i < len(h_constraints) and j < len(h_constraints[i]):
        sign = h_constraints[i][j]
        right = grid[i][j + 1]
        if sign == "<" and right is not None and not (value < right):
            return False
        if sign == ">" and right is not None and not (value > right):
            return False

    if i > 0 and (i - 1) < len(v_constraints) and j < len(v_constraints[i - 1]):
        sign = v_constraints[i - 1][j]
        top = grid[i - 1][j]
        if sign == "^" and top is not None and not (top < value):
            return False
        if sign == "v" and top is not None and not (top > value):
            return False

    if i < (N - 1) and i < len(v_constraints) and j < len(v_constraints[i]):
        sign = v_constraints[i][j]
        bottom = grid[i + 1][j]
        if sign == "^" and bottom is not None and not (value < bottom):
            return False
        if sign == "v" and bottom is not None and not (value > bottom):
            return False

    return True


def _is_complete_and_valid(
    grid: list[list[int | None]],
    h_constraints: list[list[str]],
    v_constraints: list[list[str]],
    N: int,
) -> bool:
    for i in range(N):
        for j in range(N):
            if grid[i][j] is None:
                return False
            if not _check_cell_valid(grid, i, j, h_constraints, v_constraints, N):
                return False
    return True


def _copy_grid(grid: list[list[int | None]], N: int) -> list[list[int | None]]:
    copied = copy.deepcopy(grid)
    if len(copied) < N:
        copied.extend([[None for _ in range(N)] for _ in range(N - len(copied))])

    return [
        [copied[i][j] if i < len(copied) and j < len(copied[i]) else None for j in range(N)]
        for i in range(N)
    ]


SOLVER_GENERATORS = {
    "Brute Force": brute_force_solver_gen,
    "Backtracking": backtracking_solver_gen,
    "Forward Chaining": forward_chaining_solver_gen,
    "A*": a_star_solver_gen,
}
