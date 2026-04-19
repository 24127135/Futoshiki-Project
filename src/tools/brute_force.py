from __future__ import annotations

import argparse
from pathlib import Path
import sys

if __package__ in (None, ""):
    # When run as: python src/tools/brute_force.py
    # add src/ so `futoshiki` package is importable.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from futoshiki.solvers.brute_force import brute_force_solve, is_valid
from futoshiki.io_parser import parse_puzzle_file


# Re-export for compatibility with code that imported the old top-level module.
__all__ = ["is_valid", "brute_force_solve"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Solve a Futoshiki puzzle using brute force")
    parser.add_argument("input_file", type=Path, help="Path to input-*.txt puzzle file")
    args = parser.parse_args()

    puzzle = parse_puzzle_file(args.input_file)
    stats = {"calls": 0, "backtracks": 0}
    board = [row[:] for row in puzzle.grid]

    from time import perf_counter

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
