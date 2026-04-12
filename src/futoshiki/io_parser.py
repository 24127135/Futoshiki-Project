from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

_ALLOWED_SIGNS = {-1, 0, 1}


@dataclass
class Puzzle:
    n: int
    grid: List[List[int]]
    horizontal: List[List[int]]  # n rows, n-1 columns
    vertical: List[List[int]]  # n-1 rows, n columns


def _strip_lines(raw: str) -> List[str]:
    lines: List[str] = []
    for line in raw.splitlines():
        cleaned = line.strip()
        if not cleaned or cleaned.startswith("#"):
            continue
        lines.append(cleaned)
    return lines


def _parse_row(line: str, expected_len: int, ctx: str) -> List[int]:
    parts = line.split()
    if len(parts) != expected_len:
        raise ValueError(f"{ctx}: expected {expected_len} values, got {len(parts)}")
    try:
        return [int(x) for x in parts]
    except ValueError as exc:
        raise ValueError(f"{ctx}: non-integer token found") from exc


def parse_puzzle_text(text: str) -> Puzzle:
    lines = _strip_lines(text)
    if not lines:
        raise ValueError("Input is empty")

    try:
        n = int(lines[0])
    except ValueError as exc:
        raise ValueError("First non-comment line must be integer N") from exc

    if n < 2:
        raise ValueError("N must be >= 2")

    cursor = 1
    need = 1 + n + n + (n - 1)
    if len(lines) < need:
        raise ValueError(
            "Not enough lines. Expected at least "
            f"{need} non-empty, non-comment lines for N={n}."
        )

    grid: List[List[int]] = []
    for r in range(n):
        row = _parse_row(lines[cursor], n, f"grid row {r + 1}")
        for v in row:
            if v < 0 or v > n:
                raise ValueError(
                    f"grid row {r + 1}: values must be in [0, {n}]"
                )
        grid.append(row)
        cursor += 1

    horizontal: List[List[int]] = []
    for r in range(n):
        row = _parse_row(lines[cursor], n - 1, f"horizontal row {r + 1}")
        if any(v not in _ALLOWED_SIGNS for v in row):
            raise ValueError(
                f"horizontal row {r + 1}: signs must be in {{-1, 0, 1}}"
            )
        horizontal.append(row)
        cursor += 1

    vertical: List[List[int]] = []
    for r in range(n - 1):
        row = _parse_row(lines[cursor], n, f"vertical row {r + 1}")
        if any(v not in _ALLOWED_SIGNS for v in row):
            raise ValueError(
                f"vertical row {r + 1}: signs must be in {{-1, 0, 1}}"
            )
        vertical.append(row)
        cursor += 1

    return Puzzle(n=n, grid=grid, horizontal=horizontal, vertical=vertical)


def parse_puzzle_file(path: str | Path) -> Puzzle:
    content = Path(path).read_text(encoding="utf-8")
    return parse_puzzle_text(content)
