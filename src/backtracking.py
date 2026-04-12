import argparse
from pathlib import Path
from time import perf_counter
from typing import Dict, List, Optional, Tuple

from brute_force import is_valid
from futoshiki.io_parser import parse_puzzle_file


_MRV_H_CONSTRAINTS: Optional[List[List[int]]] = None
_MRV_V_CONSTRAINTS: Optional[List[List[int]]] = None


def _get_candidates(
    grid: List[List[int]],
    r: int,
    c: int,
    h_constraints: List[List[int]],
    v_constraints: List[List[int]],
    N: int,
) -> List[int]:
    """
    Return values 1..N that pass is_valid for cell (r,c).
    This is the only "smart" part of backtracking vs brute force.
    """
    if grid[r][c] != 0:
        return []

    candidates: List[int] = []
    for v in range(1, N + 1):
        if is_valid(grid, r, c, v, h_constraints, v_constraints, N):
            candidates.append(v)
    return candidates


def _select_cell(grid: List[List[int]], N: int) -> Optional[Tuple[int, int]]:
    """
    MRV heuristic: among all empty cells, return the one with the
    fewest valid candidates. Return None if no empty cells.
    If two cells have equal candidates, prefer lower row then lower col.
    """
    h_constraints = _MRV_H_CONSTRAINTS
    v_constraints = _MRV_V_CONSTRAINTS

    if h_constraints is None:
        h_constraints = [[0 for _ in range(max(N - 1, 0))] for _ in range(N)]
    if v_constraints is None:
        v_constraints = [[0 for _ in range(N)] for _ in range(max(N - 1, 0))]

    best_cell: Optional[Tuple[int, int]] = None
    best_count = N + 1

    for r in range(N):
        for c in range(N):
            if grid[r][c] != 0:
                continue

            count = len(_get_candidates(grid, r, c, h_constraints, v_constraints, N))
            if best_cell is None or count < best_count:
                best_cell = (r, c)
                best_count = count
                if best_count == 0:
                    return best_cell

    return best_cell


def backtracking_solve(
    grid: List[List[int]],
    h_constraints: List[List[int]],
    v_constraints: List[List[int]],
    N: int,
    stats: Dict[str, int],
) -> Optional[List[List[int]]]:
    """
    Backtracking solver WITH MRV cell selection and candidate filtering.

    stats dict:
      'calls'     : recursive calls
      'backtracks': times a cell was reset to 0

    Algorithm:
      1. cell = _select_cell(grid, N)
      2. If None: return grid  (solved)
      3. r, c = cell
      4. candidates = _get_candidates(grid, r, c, h, v_c, N)
      5. For v in candidates:
           grid[r][c] = v
           stats['calls'] += 1
           result = backtracking_solve(...)
           if result: return result
           grid[r][c] = 0
           stats['backtracks'] += 1
      6. Return None
    """
    global _MRV_H_CONSTRAINTS
    global _MRV_V_CONSTRAINTS

    _MRV_H_CONSTRAINTS = h_constraints
    _MRV_V_CONSTRAINTS = v_constraints

    stats.setdefault("calls", 0)
    stats.setdefault("backtracks", 0)

    cell = _select_cell(grid, N)
    if cell is None:
        return grid

    r, c = cell
    candidates = _get_candidates(grid, r, c, h_constraints, v_constraints, N)

    for v in candidates:
        grid[r][c] = v
        stats["calls"] += 1

        result = backtracking_solve(grid, h_constraints, v_constraints, N, stats)
        if result is not None:
            return result

        grid[r][c] = 0
        stats["backtracks"] += 1

    return None


def backtracking_gen(
    grid: List[List[int]],
    h_constraints: List[List[int]],
    v_constraints: List[List[int]],
    N: int,
):
    """
    Generator version for GUI animation.
    Yield ('try', r, c, v), ('backtrack', r, c), ('solved', grid).
    Same as brute_force_gen but uses MRV selection and candidate filtering.
    """
    global _MRV_H_CONSTRAINTS
    global _MRV_V_CONSTRAINTS

    _MRV_H_CONSTRAINTS = h_constraints
    _MRV_V_CONSTRAINTS = v_constraints

    stats: Dict[str, int] = {"calls": 0, "backtracks": 0}

    def _solve():
        cell = _select_cell(grid, N)
        if cell is None:
            yield ("solved", grid)
            return True

        r, c = cell
        candidates = _get_candidates(grid, r, c, h_constraints, v_constraints, N)

        for v in candidates:
            grid[r][c] = v
            stats["calls"] += 1
            yield ("try", r, c, v)

            solved = yield from _solve()
            if solved:
                return True

            grid[r][c] = 0
            stats["backtracks"] += 1
            yield ("backtrack", r, c)

        return False

    yield from _solve()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Solve a Futoshiki puzzle using MRV backtracking")
    parser.add_argument("input_file", type=Path, help="Path to input-*.txt puzzle file")
    args = parser.parse_args()

    puzzle = parse_puzzle_file(args.input_file)
    stats = {"calls": 0, "backtracks": 0}
    board = [row[:] for row in puzzle.grid]

    start = perf_counter()
    solution = backtracking_solve(
        board,
        puzzle.horizontal,
        puzzle.vertical,
        puzzle.n,
        stats,
    )
    elapsed = perf_counter() - start

    if solution is None:
        print(f"[UNSOLVED] {args.input_file.name} ({puzzle.n}x{puzzle.n})")
        print(f"time={elapsed:.3f}s | calls={stats['calls']} | backtracks={stats['backtracks']}")
        raise SystemExit(1)

    print(f"[SOLVED] {args.input_file.name} ({puzzle.n}x{puzzle.n})")
    print(f"time={elapsed:.3f}s | calls={stats['calls']} | backtracks={stats['backtracks']}")
    for row in solution:
        print(" ".join(str(v) for v in row))