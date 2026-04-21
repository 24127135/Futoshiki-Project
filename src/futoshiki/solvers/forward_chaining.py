from __future__ import annotations

from dataclasses import dataclass
from typing import List

from ..io_parser import Puzzle
from ..state import FutoshikiState


@dataclass
class ForwardChainingResult:
    state: FutoshikiState
    solved: bool
    inconsistent: bool
    iterations: int


def _remove_values(domain: List[int], forbidden: set[int]) -> tuple[List[int], bool]:
    new_domain = [v for v in domain if v not in forbidden]
    return new_domain, new_domain != domain


def _prune_row_column(state: FutoshikiState) -> tuple[bool, bool]:
    changed = False

    for i in range(state.n):
        fixed_vals = [state.domains[i][j][0] for j in range(state.n) if len(state.domains[i][j]) == 1]
        if len(fixed_vals) != len(set(fixed_vals)):
            return changed, True

        fixed = {state.domains[i][j][0] for j in range(state.n) if len(state.domains[i][j]) == 1}
        for j in range(state.n):
            if len(state.domains[i][j]) == 1:
                continue
            new_domain, did_change = _remove_values(state.domains[i][j], fixed)
            if did_change:
                state.domains[i][j] = new_domain
                changed = True
            if not state.domains[i][j]:
                return changed, True

    for j in range(state.n):
        fixed_vals = [state.domains[i][j][0] for i in range(state.n) if len(state.domains[i][j]) == 1]
        if len(fixed_vals) != len(set(fixed_vals)):
            return changed, True

        fixed = {state.domains[i][j][0] for i in range(state.n) if len(state.domains[i][j]) == 1}
        for i in range(state.n):
            if len(state.domains[i][j]) == 1:
                continue
            new_domain, did_change = _remove_values(state.domains[i][j], fixed)
            if did_change:
                state.domains[i][j] = new_domain
                changed = True
            if not state.domains[i][j]:
                return changed, True

    return changed, False


def _assign_hidden_singles(state: FutoshikiState) -> tuple[bool, bool]:
    changed = False

    for i in range(state.n):
        for v in range(1, state.n + 1):
            positions = [j for j in range(state.n) if v in state.domains[i][j]]
            if not positions:
                return changed, True
            if len(positions) == 1:
                j = positions[0]
                if state.domains[i][j] != [v]:
                    state.domains[i][j] = [v]
                    changed = True

    for j in range(state.n):
        for v in range(1, state.n + 1):
            positions = [i for i in range(state.n) if v in state.domains[i][j]]
            if not positions:
                return changed, True
            if len(positions) == 1:
                i = positions[0]
                if state.domains[i][j] != [v]:
                    state.domains[i][j] = [v]
                    changed = True

    return changed, False


def _filter_pair(left: List[int], right: List[int], sign: int) -> tuple[List[int], List[int]]:
    if sign == 1:
        new_left = [a for a in left if any(a < b for b in right)]
        new_right = [b for b in right if any(a < b for a in left)]
    else:
        new_left = [a for a in left if any(a > b for b in right)]
        new_right = [b for b in right if any(a > b for a in left)]
    return new_left, new_right


def _prune_inequalities(puzzle: Puzzle, state: FutoshikiState) -> tuple[bool, bool]:
    changed = False

    for i in range(puzzle.n):
        for j in range(puzzle.n - 1):
            sign = puzzle.horizontal[i][j]
            if sign == 0:
                continue

            left = state.domains[i][j]
            right = state.domains[i][j + 1]
            new_left, new_right = _filter_pair(left, right, sign)

            if not new_left or not new_right:
                return changed, True

            if new_left != left:
                state.domains[i][j] = new_left
                changed = True
            if new_right != right:
                state.domains[i][j + 1] = new_right
                changed = True

    for i in range(puzzle.n - 1):
        for j in range(puzzle.n):
            sign = puzzle.vertical[i][j]
            if sign == 0:
                continue

            top = state.domains[i][j]
            bottom = state.domains[i + 1][j]
            new_top, new_bottom = _filter_pair(top, bottom, sign)

            if not new_top or not new_bottom:
                return changed, True

            if new_top != top:
                state.domains[i][j] = new_top
                changed = True
            if new_bottom != bottom:
                state.domains[i + 1][j] = new_bottom
                changed = True

    return changed, False


def _is_solved(state: FutoshikiState) -> bool:
    return all(len(state.domains[i][j]) == 1 for i in range(state.n) for j in range(state.n))


def run_forward_chaining(puzzle: Puzzle) -> ForwardChainingResult:
    state = FutoshikiState.from_puzzle(puzzle)
    iterations = 0

    while True:
        iterations += 1
        any_change = False

        row_col_changed, inconsistent = _prune_row_column(state)
        if inconsistent:
            return ForwardChainingResult(
                state=state,
                solved=False,
                inconsistent=True,
                iterations=iterations,
            )
        any_change = any_change or row_col_changed

        ineq_changed, inconsistent = _prune_inequalities(puzzle, state)
        if inconsistent:
            return ForwardChainingResult(
                state=state,
                solved=False,
                inconsistent=True,
                iterations=iterations,
            )
        any_change = any_change or ineq_changed

        hidden_changed, inconsistent = _assign_hidden_singles(state)
        if inconsistent:
            return ForwardChainingResult(
                state=state,
                solved=False,
                inconsistent=True,
                iterations=iterations,
            )
        any_change = any_change or hidden_changed

        if _is_solved(state):
            return ForwardChainingResult(
                state=state,
                solved=True,
                inconsistent=False,
                iterations=iterations,
            )

        if not any_change:
            return ForwardChainingResult(
                state=state,
                solved=False,
                inconsistent=False,
                iterations=iterations,
            )
