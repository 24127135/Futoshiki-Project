from typing import Dict, List, Optional, Tuple


class KnowledgeBase:
    def __init__(self, N: int):
        self.N = N
        self.propositions: List[str] = []   # All Val(i,j,v) atoms
        self.clauses: List[List[str]] = []  # CNF clauses (lists of literals)
        self.given_facts: List[str] = []    # Ground facts from puzzle clues
        self.h_less: List[Tuple[int, int]] = []       # (i,j) pairs where LessH holds
        self.h_greater: List[Tuple[int, int]] = []
        self.v_less: List[Tuple[int, int]] = []
        self.v_greater: List[Tuple[int, int]] = []

    # ------------------------------------------------------------------
    # DAY 1 - Atom generation
    # ------------------------------------------------------------------
    def generate_propositions(self) -> List[str]:
        """
        Generate every Val(i,j,v) proposition for i,j,v in 1..N.
        Store in self.propositions and return the list.
        Expected count: N^3
        """
        self.propositions = [
            f"Val({i},{j},{v})"
            for i in range(1, self.N + 1)
            for j in range(1, self.N + 1)
            for v in range(1, self.N + 1)
        ]
        return self.propositions

    def load_puzzle(
        self,
        grid: List[List[Optional[int]]],
        h_constraints: List[List[int]],
        v_constraints: List[List[int]],
    ) -> None:
        """
        Read a concrete puzzle instance and populate:
          self.given_facts  - "Val(i,j,v)" strings for pre-filled cells
          self.h_less       - (i,j) tuples where h_constraints[i-1][j-1] == 1
          self.h_greater    - (i,j) tuples where h_constraints[i-1][j-1] == -1
          self.v_less       - (i,j) tuples where v_constraints[i-1][j-1] == 1
          self.v_greater    - (i,j) tuples where v_constraints[i-1][j-1] == -1
        All coordinates are 1-indexed to match FOL notation.
        """
        self.given_facts = []
        self.h_less = []
        self.h_greater = []
        self.v_less = []
        self.v_greater = []

        for i in range(1, self.N + 1):
            for j in range(1, self.N + 1):
                value = grid[i - 1][j - 1]
                if value is None:
                    continue
                try:
                    v = int(value)
                except (TypeError, ValueError):
                    continue
                if 1 <= v <= self.N:
                    self.given_facts.append(f"Val({i},{j},{v})")

        for i, row in enumerate(h_constraints, start=1):
            for j, relation in enumerate(row, start=1):
                if relation == 1:
                    self.h_less.append((i, j))
                elif relation == -1:
                    self.h_greater.append((i, j))

        for i, row in enumerate(v_constraints, start=1):
            for j, relation in enumerate(row, start=1):
                if relation == 1:
                    self.v_less.append((i, j))
                elif relation == -1:
                    self.v_greater.append((i, j))

    # ------------------------------------------------------------------
    # DAY 2 - Grounding FOL axioms into CNF clauses
    # ------------------------------------------------------------------
    def ground_cell_uniqueness(self) -> None:
        """
        A1: every cell has at least one value.
          Clause: [Val(i,j,1), Val(i,j,2), ..., Val(i,j,N)]  for each (i,j)

        A2: every cell has at most one value.
          Clause: [~Val(i,j,v1), ~Val(i,j,v2)]  for each (i,j), each v1<v2 pair
        """
        for i in range(1, self.N + 1):
            for j in range(1, self.N + 1):
                self.clauses.append([f"Val({i},{j},{v})" for v in range(1, self.N + 1)])
                for v1 in range(1, self.N + 1):
                    for v2 in range(v1 + 1, self.N + 1):
                        self.clauses.append([f"~Val({i},{j},{v1})", f"~Val({i},{j},{v2})"])

    def ground_row_permutation(self) -> None:
        """
        A3 (at-least): each value appears at least once per row.
          Clause: [Val(i,1,v), Val(i,2,v), ..., Val(i,N,v)]  for each i,v

        A3 (at-most): each value appears at most once per row.
          Clause: [~Val(i,j1,v), ~Val(i,j2,v)]  for each i, each j1<j2 pair, each v
        """
        for i in range(1, self.N + 1):
            for v in range(1, self.N + 1):
                self.clauses.append([f"Val({i},{j},{v})" for j in range(1, self.N + 1)])
                for j1 in range(1, self.N + 1):
                    for j2 in range(j1 + 1, self.N + 1):
                        self.clauses.append([f"~Val({i},{j1},{v})", f"~Val({i},{j2},{v})"])

    def ground_col_permutation(self) -> None:
        """
        A4 (at-least): each value appears at least once per column.
          Clause: [Val(1,j,v), Val(2,j,v), ..., Val(N,j,v)]  for each j,v

        A4 (at-most): each value appears at most once per column.
          Clause: [~Val(i1,j,v), ~Val(i2,j,v)]  for each j, each i1<i2 pair, each v
        """
        for j in range(1, self.N + 1):
            for v in range(1, self.N + 1):
                self.clauses.append([f"Val({i},{j},{v})" for i in range(1, self.N + 1)])
                for i1 in range(1, self.N + 1):
                    for i2 in range(i1 + 1, self.N + 1):
                        self.clauses.append([f"~Val({i1},{j},{v})", f"~Val({i2},{j},{v})"])

    def ground_inequality_constraints(self) -> None:
        """
        For each (i,j) in self.h_less:
          For each v1, v2 where NOT v1 < v2:
            Clause: [~Val(i,j,v1), ~Val(i,j+1,v2)]
          (If LessH(i,j) holds, we cannot have Val(i,j,v1) AND Val(i,j+1,v2)
           unless v1 < v2. So for all (v1,v2) violating the constraint, forbid them.)

        Same pattern for h_greater, v_less, v_greater.
        """
        for i, j in self.h_less:
            for v1 in range(1, self.N + 1):
                for v2 in range(1, self.N + 1):
                    if not (v1 < v2):
                        self.clauses.append([f"~Val({i},{j},{v1})", f"~Val({i},{j + 1},{v2})"])

        for i, j in self.h_greater:
            for v1 in range(1, self.N + 1):
                for v2 in range(1, self.N + 1):
                    if not (v1 > v2):
                        self.clauses.append([f"~Val({i},{j},{v1})", f"~Val({i},{j + 1},{v2})"])

        for i, j in self.v_less:
            for v1 in range(1, self.N + 1):
                for v2 in range(1, self.N + 1):
                    if not (v1 < v2):
                        self.clauses.append([f"~Val({i},{j},{v1})", f"~Val({i + 1},{j},{v2})"])

        for i, j in self.v_greater:
            for v1 in range(1, self.N + 1):
                for v2 in range(1, self.N + 1):
                    if not (v1 > v2):
                        self.clauses.append([f"~Val({i},{j},{v1})", f"~Val({i + 1},{j},{v2})"])

    def ground_given_facts(self) -> None:
        """
        For each (i,j,v) pre-filled cell:
          Unit clause: [Val(i,j,v)]   (this cell MUST have this value)
          For every other value u != v:
            Unit clause: [~Val(i,j,u)]  (no other value allowed)
        """
        for fact in self.given_facts:
            if not (fact.startswith("Val(") and fact.endswith(")")):
                continue

            parts = fact[4:-1].split(",")
            if len(parts) != 3:
                continue

            try:
                i = int(parts[0].strip())
                j = int(parts[1].strip())
                v = int(parts[2].strip())
            except ValueError:
                continue

            self.clauses.append([f"Val({i},{j},{v})"])
            for u in range(1, self.N + 1):
                if u != v:
                    self.clauses.append([f"~Val({i},{j},{u})"])

    def build_full_kb(
        self,
        grid: List[List[Optional[int]]],
        h_constraints: List[List[int]],
        v_constraints: List[List[int]],
    ) -> None:
        """
        Master method. Call in this order:
          1. generate_propositions()
          2. load_puzzle(grid, h_constraints, v_constraints)
          3. ground_given_facts()
          4. ground_cell_uniqueness()
          5. ground_row_permutation()
          6. ground_col_permutation()
          7. ground_inequality_constraints()
        """
        self.clauses = []
        self.generate_propositions()
        self.load_puzzle(grid, h_constraints, v_constraints)
        self.ground_given_facts()
        self.ground_cell_uniqueness()
        self.ground_row_permutation()
        self.ground_col_permutation()
        self.ground_inequality_constraints()

    # ------------------------------------------------------------------
    # Reporting helpers (for the project report)
    # ------------------------------------------------------------------
    def summary(self) -> str:
        """
        Return a multiline string:
          N                 : {N}
          Propositions      : {len(propositions)}
          Total CNF clauses : {len(clauses)}
          Given facts       : {len(given_facts)}
          H-less pairs      : {len(h_less)}
          H-greater pairs   : {len(h_greater)}
          V-less pairs      : {len(v_less)}
          V-greater pairs   : {len(v_greater)}
        """
        return (
            f"N                 : {self.N}\n"
            f"Propositions      : {len(self.propositions)}\n"
            f"Total CNF clauses : {len(self.clauses)}\n"
            f"Given facts       : {len(self.given_facts)}\n"
            f"H-less pairs      : {len(self.h_less)}\n"
            f"H-greater pairs   : {len(self.h_greater)}\n"
            f"V-less pairs      : {len(self.v_less)}\n"
            f"V-greater pairs   : {len(self.v_greater)}"
        )

    def get_unit_clauses(self) -> List[str]:
        """Return all single-literal clauses (unit clauses) as strings."""
        return [clause[0] for clause in self.clauses if len(clause) == 1]

    def get_clauses_by_type(self, prefix: str) -> List[List[str]]:
        """
        Return all clauses whose first literal starts with prefix.
        Example: prefix="Val(1,1," returns clauses about cell (1,1).
        """
        return [clause for clause in self.clauses if clause and clause[0].startswith(prefix)]


if __name__ == "__main__":
    N = 3
    kb = KnowledgeBase(N)
    grid = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    h = [[0, 0], [0, 0], [0, 0]]
    v = [[0, 0, 0], [0, 0, 0]]
    kb.build_full_kb(grid, h, v)
    print(kb.summary())
    assert len(kb.propositions) == N ** 3, f"Expected {N ** 3} propositions"
    assert all(len(c) >= 1 for c in kb.clauses), "Empty clause found"
    print("DAY 1-2 PASS: KB builds correctly for N=3")

    N = 4
    kb4 = KnowledgeBase(N)
    kb4.build_full_kb([[0] * 4] * 4, [[0] * 3] * 4, [[0] * 4] * 3)
    print(kb4.summary())
    print("DAY 1-2 PASS: KB builds correctly for N=4")