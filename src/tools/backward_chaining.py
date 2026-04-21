from __future__ import annotations

import argparse
from pathlib import Path
import sys

if __package__ in (None, ""):
    # When run as: python src/tools/backward_chaining.py
    # add src/ so `futoshiki` package is importable.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from futoshiki.inference.backward_chaining import solve_deductive
from futoshiki.io_parser import parse_puzzle_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Query Futoshiki using Deductive Backward Chaining and search fallback")
    parser.add_argument("input_file", type=Path, help="Path to input-*.txt puzzle file")
    parser.add_argument("--debug", action="store_true", help="Print debug information")
    args = parser.parse_args()

    puzzle = parse_puzzle_file(args.input_file)
    board = [row[:] for row in puzzle.grid]

    from time import perf_counter

    start = perf_counter()
    solution, stats = solve_deductive(
        puzzle.n,
        board,
        puzzle.horizontal,
        puzzle.vertical,
        debug=args.debug
    )
    elapsed = perf_counter() - start

    # A check to see if it's completely solved, the deductive solver might not guess when stuck
    is_solved = all(cell != 0 for row in solution for cell in row)

    if not is_solved:
        print(f"[UNFINISHED] {args.input_file.name} ({puzzle.n}x{puzzle.n}) - SLD + search could not complete it.")
        print(
            "time="
            f"{elapsed:.3f}s | bc_calls={stats['bc_calls']} | loops={stats['loops']} "
            f"| search_calls={stats.get('search_calls', 0)} | backtracks={stats.get('backtracks', 0)}"
        )
        for row in solution:
            print(" ".join(str(v) if v != 0 else "_" for v in row))
        raise SystemExit(1)

    print(f"[SOLVED] {args.input_file.name} ({puzzle.n}x{puzzle.n})")
    print(
        "time="
        f"{elapsed:.3f}s | bc_calls={stats['bc_calls']} | loops={stats['loops']} "
        f"| search_calls={stats.get('search_calls', 0)} | backtracks={stats.get('backtracks', 0)}"
    )
    for row in solution:
        print(" ".join(str(v) for v in row))


if __name__ == "__main__":
    main()
