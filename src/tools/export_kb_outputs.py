from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Optional

if __package__ in (None, ""):
    # When run as: python src/tools/export_kb_outputs.py
    # add src/ so project modules are importable.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from futoshiki.io_parser import parse_puzzle_file
from futoshiki.knowledge_base import KnowledgeBase


def _render_clause(clause: list[str]) -> str:
    return " OR ".join(clause)


def _build_report_text(
    input_file: Path,
    kb: KnowledgeBase,
    max_clauses: Optional[int],
) -> str:
    lines: list[str] = [
        f"Input file: {input_file.name}",
        "",
        "Knowledge Base Summary",
        "----------------------",
        kb.summary(),
        "",
        "Given facts",
        "-----------",
    ]

    if kb.given_facts:
        lines.extend(kb.given_facts)
    else:
        lines.append("(none)")

    lines.extend([
        "",
        "CNF Clauses",
        "-----------",
    ])

    total_clauses = len(kb.clauses)
    if max_clauses is None or max_clauses <= 0:
        limit = total_clauses
    else:
        limit = min(max_clauses, total_clauses)

    for idx, clause in enumerate(kb.clauses[:limit], start=1):
        lines.append(f"{idx}: {_render_clause(clause)}")

    if limit < total_clauses:
        lines.append("")
        lines.append(f"... truncated {total_clauses - limit} additional clauses")

    return "\n".join(lines) + "\n"


def export_kb_for_input(
    input_file: Path,
    output_dir: Path,
    max_clauses: Optional[int],
) -> Path:
    puzzle = parse_puzzle_file(input_file)

    kb = KnowledgeBase(puzzle.n)
    kb.build_full_kb(puzzle.grid, puzzle.horizontal, puzzle.vertical)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{input_file.stem.replace('input-', 'output-', 1)}.txt"
    output_file.write_text(_build_report_text(input_file, kb, max_clauses), encoding="utf-8")
    return output_file


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export Knowledge Base conversion outputs for Futoshiki input files"
    )
    parser.add_argument(
        "--inputs-dir",
        type=Path,
        default=Path("inputs"),
        help="Directory containing input-*.txt files",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs"),
        help="Directory where output reports are written",
    )
    parser.add_argument(
        "--max-clauses",
        type=int,
        default=0,
        help="Maximum clauses per output file (0 means write all)",
    )
    args = parser.parse_args()

    input_files = sorted(args.inputs_dir.glob("input-*.txt"))
    if not input_files:
        raise SystemExit(f"No input files found in {args.inputs_dir}")

    max_clauses = None if args.max_clauses <= 0 else args.max_clauses

    for input_file in input_files:
        out = export_kb_for_input(input_file, args.output_dir, max_clauses)
        print(f"[OK] {input_file.name} -> {out}")


if __name__ == "__main__":
    main()
