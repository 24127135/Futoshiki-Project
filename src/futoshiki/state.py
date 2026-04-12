from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .io_parser import Puzzle


@dataclass
class FutoshikiState:
    n: int
    domains: List[List[List[int]]]

    @classmethod
    def from_puzzle(cls, puzzle: Puzzle) -> "FutoshikiState":
        all_values = list(range(1, puzzle.n + 1))
        domains: List[List[List[int]]] = []

        for i in range(puzzle.n):
            row_domains: List[List[int]] = []
            for j in range(puzzle.n):
                clue = puzzle.grid[i][j]
                if clue == 0:
                    row_domains.append(all_values.copy())
                else:
                    row_domains.append([clue])
            domains.append(row_domains)

        return cls(n=puzzle.n, domains=domains)

    def domain_size_grid(self) -> List[List[int]]:
        return [[len(self.domains[i][j]) for j in range(self.n)] for i in range(self.n)]
