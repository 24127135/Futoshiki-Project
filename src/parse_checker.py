from __future__ import annotations

import argparse
from pathlib import Path

from futoshiki.io_parser import parse_puzzle_file
from futoshiki.util.pretty import render_domains, render_puzzle
from futoshiki.state import FutoshikiState


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 1 checker for Futoshiki")
    parser.add_argument("input_file", type=Path, help="Path to input-XX.txt")
    args = parser.parse_args()

    puzzle = parse_puzzle_file(args.input_file)
    state = FutoshikiState.from_puzzle(puzzle)

    print(f"Loaded puzzle size: {puzzle.n}x{puzzle.n}")
    print("\nGrid + inequalities:")
    print(render_puzzle(puzzle))

    print("\nInitial domains:")
    print(render_domains(state))


if __name__ == "__main__":
    main()
