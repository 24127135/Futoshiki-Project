from __future__ import annotations

from .io_parser import Puzzle
from .state import FutoshikiState


def _h_symbol(sign: int) -> str:
    if sign == 1:
        return "<"
    if sign == -1:
        return ">"
    return " "


def _v_symbol(sign: int) -> str:
    if sign == 1:
        return "v"
    if sign == -1:
        return "^"
    return " "


def render_puzzle(puzzle: Puzzle) -> str:
    lines = []
    n = puzzle.n

    for i in range(n):
        row_parts = []
        for j in range(n):
            v = puzzle.grid[i][j]
            if v == 0:
                cell = "[ ]"
            else:
                cell = f"[{v}]"
            row_parts.append(cell)
            if j < n - 1:
                h_constraint = puzzle.horizontal[i][j]
                if h_constraint == 0:
                    row_parts.append("   ")
                else:
                    row_parts.append(f" {_h_symbol(h_constraint)} ")
        lines.append("".join(row_parts))

        if i < n - 1:
            vrow_parts = []
            for j in range(n):
                v_constraint = puzzle.vertical[i][j]
                if v_constraint == 0:
                    vrow_parts.append("   ")
                else:
                    vrow_parts.append(f" {_v_symbol(v_constraint)} ")
                if j < n - 1:
                    vrow_parts.append("   ")
            lines.append("".join(vrow_parts))

    return "\n".join(lines)


def render_domains(state: FutoshikiState) -> str:
    full_domain = list(range(1, state.n + 1))
    domain_texts = []
    for i in range(state.n):
        row_texts = []
        for j in range(state.n):
            domain = state.domains[i][j]
            row_texts.append("-" if domain == full_domain else str(domain))
        domain_texts.append(row_texts)

    cell_width = max(5, max(len(text) for row in domain_texts for text in row))
    row_label_width = max(2, len(f"r{state.n}"))

    lines = []
    header_cells = ["".rjust(row_label_width)]
    for j in range(state.n):
        header_cells.append(f"c{j + 1}".center(cell_width))
    lines.append(" | ".join(header_cells))
    lines.append("-+-".join(["-" * row_label_width] + ["-" * cell_width] * state.n))

    for i in range(state.n):
        row_cells = [f"r{i + 1}".rjust(row_label_width)]
        for j in range(state.n):
            row_cells.append(domain_texts[i][j].center(cell_width))
        lines.append(" | ".join(row_cells))

    return "\n".join(lines)
