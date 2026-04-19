from __future__ import annotations

import argparse
from pathlib import Path
import sys

if __package__ in (None, ""):
    # When run as: python src/tools/forward_pruning_smoke.py
    # add src/ so `futoshiki` package is importable.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from futoshiki.io_parser import parse_puzzle_file
from futoshiki.solvers.forward_chaining import run_forward_chaining


def evaluate_file(path: Path) -> dict[str, object]:
    puzzle = parse_puzzle_file(path)
    result = run_forward_chaining(puzzle)
    status = "PASS" if result.solved and not result.inconsistent else "FAIL"
    return {
        "file": path.name,
        "iterations": result.iterations,
        "solved": result.solved,
        "inconsistent": result.inconsistent,
        "status": status,
    }


def print_table(rows: list[dict[str, object]]) -> None:
    headers = ["File", "Iterations", "Solved", "Inconsistent", "Status"]
    widths = [
        max(len(headers[0]), *(len(str(r["file"])) for r in rows)),
        max(len(headers[1]), *(len(str(r["iterations"])) for r in rows)),
        max(len(headers[2]), *(len(str(r["solved"])) for r in rows)),
        max(len(headers[3]), *(len(str(r["inconsistent"])) for r in rows)),
        max(len(headers[4]), *(len(str(r["status"])) for r in rows)),
    ]

    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    print(fmt.format(*("-" * w for w in widths)))
    for row in rows:
        print(
            fmt.format(
                row["file"],
                row["iterations"],
                row["solved"],
                row["inconsistent"],
                row["status"],
            )
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run forward-pruning smoke tests across input files"
    )
    parser.add_argument(
        "--inputs-dir",
        type=Path,
        default=Path("inputs"),
        help="Directory containing input-*.txt files (default: inputs)",
    )
    parser.add_argument(
        "--pattern",
        default="input-*.txt",
        help="Glob pattern for input files (default: input-*.txt)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero exit code if any file is FAIL",
    )
    args = parser.parse_args()

    files = sorted(args.inputs_dir.glob(args.pattern))
    if not files:
        print(f"No files matched: {args.inputs_dir / args.pattern}")
        raise SystemExit(2)

    rows = [evaluate_file(path) for path in files]
    print_table(rows)

    passed = sum(1 for r in rows if r["status"] == "PASS")
    failed = len(rows) - passed
    print(f"\nSummary: PASS={passed} FAIL={failed} TOTAL={len(rows)}")

    if failed:
        print("\nFailing files:")
        for row in rows:
            if row["status"] == "FAIL":
                print(
                    f"- {row['file']}: Iterations={row['iterations']} "
                    f"Solved={row['solved']} Inconsistent={row['inconsistent']}"
                )

    if args.strict and failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()