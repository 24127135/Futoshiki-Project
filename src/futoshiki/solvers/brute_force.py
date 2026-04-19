from __future__ import annotations

import argparse
from pathlib import Path
from time import perf_counter
from typing import Dict, List, Optional, Tuple

from ..io_parser import parse_puzzle_file


def is_valid(
    grid: List[List[int]],
    r: int,
    c: int,
    v: int,
    h_constraints: List[List[int]],
    v_constraints: List[List[int]],
    N: int,
) -> bool:
    for j in range(N):
        if j != c and grid[r][j] == v:
            return False

    for i in range(N):
        if i != r and grid[i][c] == v:
            return False

    if c > 0 and grid[r][c - 1] != 0:
        left_val = grid[r][c - 1]
        relation = h_constraints[r][c - 1]
        if relation == 1 and not (left_val < v):
            return False
        if relation == -1 and not (left_val > v):
            return False

    if c < N - 1 and grid[r][c + 1] != 0:
        right_val = grid[r][c + 1]
        relation = h_constraints[r][c]
        if relation == 1 and not (v < right_val):
            return False
        if relation == -1 and not (v > right_val):
            return False

    if r > 0 and grid[r - 1][c] != 0:
        top_val = grid[r - 1][c]
        relation = v_constraints[r - 1][c]
        if relation == 1 and not (top_val < v):
            return False
        if relation == -1 and not (top_val > v):
            return False

    if r < N - 1 and grid[r + 1][c] != 0:
        bottom_val = grid[r + 1][c]
        relation = v_constraints[r][c]
        if relation == 1 and not (v < bottom_val):
            return False
        if relation == -1 and not (v > bottom_val):
            return False

    return True


def brute_force_solve(
    grid: List[List[int]],
    h_constraints: List[List[int]],
    v_constraints: List[List[int]],
    N: int,
    stats: Dict[str, int],
) -> Optional[List[List[int]]]:
    stats.setdefault("calls", 0)
    stats.setdefault("backtracks", 0)

    for r in range(N):
        for c in range(N):
            if grid[r][c] != 0:
                continue

            for v in range(1, N + 1):
                grid[r][c] = v
                stats["calls"] += 1

                if is_valid(grid, r, c, v, h_constraints, v_constraints, N):
                    result = brute_force_solve(grid, h_constraints, v_constraints, N, stats)
                    if result is not None:
                        return result

                grid[r][c] = 0
                stats["backtracks"] += 1

            return None

    return grid


def brute_force_gen(
    grid: List[List[int]],
    h_constraints: List[List[int]],
    v_constraints: List[List[int]],
    N: int,
):
    stats: Dict[str, int] = {"calls": 0, "backtracks": 0}

    def _solve():
        for r in range(N):
            for c in range(N):
                if grid[r][c] != 0:
                    continue

                for v in range(1, N + 1):
                    grid[r][c] = v
                    stats["calls"] += 1
                    event_try: Tuple[str, int, int, int] = ("try", r, c, v)
                    yield event_try

                    if is_valid(grid, r, c, v, h_constraints, v_constraints, N):
                        solved = yield from _solve()
                        if solved:
                            return True

                    grid[r][c] = 0
                    stats["backtracks"] += 1
                    event_backtrack: Tuple[str, int, int] = ("backtrack", r, c)
                    yield event_backtrack

                return False

        event_solved: Tuple[str, List[List[int]]] = ("solved", grid)
        yield event_solved
        return True

    yield from _solve()


def main() -> None:
    parser = argparse.ArgumentParser(description="Solve a Futoshiki puzzle using brute force")
    parser.add_argument("input_file", type=Path, help="Path to input-*.txt puzzle file")
    args = parser.parse_args()

    puzzle = parse_puzzle_file(args.input_file)
    stats = {"calls": 0, "backtracks": 0}
    board = [row[:] for row in puzzle.grid]

    start = perf_counter()
    solution = brute_force_solve(
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


if __name__ == "__main__":
    main()
