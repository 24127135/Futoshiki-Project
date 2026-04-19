"""Adapter for consuming generator-based solver events."""

from __future__ import annotations

import os
import sys
from collections.abc import Callable, Iterator

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from futoshiki.solvers.backtracking import backtracking_gen
from futoshiki.solvers.brute_force import brute_force_gen
from .solver_generators import SolverEvent


SOLVER_GENERATORS = {
    "brute": brute_force_gen,
    "backtrack": backtracking_gen,
}


def get_kb_summary(N, grid, h_constraints, v_constraints) -> str:
    from futoshiki.knowledge_base import KnowledgeBase

    kb = KnowledgeBase(N)
    kb.build_full_kb(grid, h_constraints, v_constraints)
    return kb.summary()


class SolverRunner:
    """Wrap a solver generator and expose step-by-step execution helpers."""

    def __init__(self, solver_generator: Iterator[SolverEvent]) -> None:
        self._iterator = iter(solver_generator)
        self._is_done = False

    def next_step(self) -> SolverEvent | None:
        """Return the next solver event, or None when the generator is exhausted."""
        if self._is_done:
            return None

        try:
            return next(self._iterator)
        except StopIteration:
            self._is_done = True
            return None

    def run_all(
        self,
        callback: Callable[[str, int | None, int | None, int | None], None],
    ) -> None:
        """Execute all remaining steps and invoke callback(event, i, j, v) for each."""
        while True:
            step = self.next_step()
            if step is None:
                return
            event_type, i, j, v = step
            callback(event_type, i, j, v)

        # TODO: Add pause/cancel hooks when long-running solve control is needed.
