from __future__ import annotations

import argparse
from pathlib import Path
import sys

if __package__ in (None, ""):
    # When run as: python src/tools/forward_pruning_report.py
    # add src/ so `futoshiki` package is importable.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from futoshiki.solvers.forward_chaining import run_forward_chaining
from futoshiki.io_parser import parse_puzzle_file
from futoshiki.state import FutoshikiState
from futoshiki.util.pretty import render_domains, render_puzzle


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Forward-pruning report (domain pruning + inequality propagation)"
    )
    parser.add_argument("input_file", type=Path, help="Path to a puzzle input file")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print full puzzle and domain tables (default prints summary only)",
    )
    args = parser.parse_args()

    puzzle = parse_puzzle_file(args.input_file)
    initial_state = FutoshikiState.from_puzzle(puzzle)
    result = run_forward_chaining(puzzle)

    print(f"Loaded puzzle size: {puzzle.n}x{puzzle.n}")

    if args.verbose:
        print("\nGrid + inequalities:")
        print(render_puzzle(puzzle))

        print("\nDomains before forward pruning:")
        print(render_domains(initial_state))

        print("\nDomains after forward pruning:")
        print(render_domains(result.state))

    print("\nForward pruning result:")
    print(f"Iterations: {result.iterations}")
    print(f"Solved: {result.solved}")
    print(f"Inconsistent: {result.inconsistent}")


if __name__ == "__main__":
    main()