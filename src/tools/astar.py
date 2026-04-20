from __future__ import annotations

import argparse
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from futoshiki.solvers.astar import astar_solve
from futoshiki.io_parser import parse_puzzle_file


__all__ = ["astar_solve"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Solve a Futoshiki puzzle using A* search with AC-3")
    parser.add_argument("input_file", type=Path, help="Path to input-*.txt puzzle file")
    args = parser.parse_args()

    puzzle = parse_puzzle_file(args.input_file)
    stats = {"expansions": 0}

    from time import perf_counter

    start = perf_counter()
    solution = astar_solve(
        puzzle.grid,
        puzzle.horizontal,
        puzzle.vertical,
        puzzle.n,
        stats,
    )
    elapsed = perf_counter() - start

    if solution is None:
        print(f"[UNSOLVED] {args.input_file.name} ({puzzle.n}x{puzzle.n})")
        print(f"time={elapsed:.3f}s | expansions={stats['expansions']}")
        raise SystemExit(1)

    print(f"[SOLVED] {args.input_file.name} ({puzzle.n}x{puzzle.n})")
    print(f"time={elapsed:.3f}s | expansions={stats['expansions']}")
    for row in solution:
        print(" ".join(str(v) for v in row))


if __name__ == "__main__":
    main()
