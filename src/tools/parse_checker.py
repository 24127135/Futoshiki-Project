from __future__ import annotations

import argparse
from pathlib import Path
import sys

if __package__ in (None, ""):
    # When run as: python src/tools/parse_checker.py
    # add src/ so `futoshiki` package is importable.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from futoshiki.io_parser import parse_puzzle_file
from futoshiki.util.pretty import render_puzzle


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse-only checker for Futoshiki input files")
    parser.add_argument("input_file", type=Path, help="Path to a puzzle input file")
    args = parser.parse_args()

    puzzle = parse_puzzle_file(args.input_file)

    print(f"Parsing OK: {args.input_file}")
    print(f"Loaded puzzle size: {puzzle.n}x{puzzle.n}")
    print("\nGrid + inequalities:")
    print(render_puzzle(puzzle))


if __name__ == "__main__":
    main()
