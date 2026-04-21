from __future__ import annotations

from ..solvers.brute_force import is_valid
from .bc_engine import build_kb, query_candidates_bc, Predicate


def filter_by_uniqueness(candidates, i, j, solution, N):
    used_in_row = set(solution[i - 1][c] for c in range(N) if solution[i - 1][c] != 0)
    used_in_col = set(solution[r][j - 1] for r in range(N) if solution[r][j - 1] != 0)
    forbidden = used_in_row | used_in_col
    return [v for v in candidates if v not in forbidden]


def _dynamic_given_facts(solution, N):
    facts = []
    for i in range(1, N + 1):
        for j in range(1, N + 1):
            v = solution[i - 1][j - 1]
            if v != 0:
                facts.append(Predicate('Given', i, j, v))
    return facts


def _cell_candidates(kb, i, j, solution, N, h_con, v_con):
    dynamic_facts = _dynamic_given_facts(solution, N)
    bc_candidates = query_candidates_bc(
        kb,
        i,
        j,
        dynamic_facts=dynamic_facts,
        max_depth=8 if N >= 7 else 12,
        max_steps=2000 if N >= 7 else 5000,
    )
    if not bc_candidates:
        bc_candidates = list(range(1, N + 1))

    filtered = filter_by_uniqueness(bc_candidates, i, j, solution, N)
    legal = [
        v
        for v in filtered
        if is_valid(solution, i - 1, j - 1, v, h_con, v_con, N)
    ]
    return sorted(legal)


def _find_mrv_cell(kb, solution, N, h_con, v_con):
    best_cell = None
    best_candidates = None

    for i in range(1, N + 1):
        for j in range(1, N + 1):
            if solution[i - 1][j - 1] != 0:
                continue

            candidates = _cell_candidates(kb, i, j, solution, N, h_con, v_con)
            if best_cell is None or len(candidates) < len(best_candidates):
                best_cell = (i, j)
                best_candidates = candidates
                if len(best_candidates) == 0:
                    return best_cell, best_candidates

    return best_cell, best_candidates


def _search_with_sld(kb, solution, N, h_con, v_con, stats):
    cell, candidates = _find_mrv_cell(kb, solution, N, h_con, v_con)
    if cell is None:
        return True

    if not candidates:
        return False

    i, j = cell
    for val in candidates:
        solution[i - 1][j - 1] = val
        stats['search_calls'] += 1

        if _search_with_sld(kb, solution, N, h_con, v_con, stats):
            return True

        solution[i - 1][j - 1] = 0
        stats['backtracks'] += 1

    return False


def solve_deductive(N, grid, h_con, v_con, debug=False):
    kb = build_kb(N, grid, h_con, v_con)
    solution = [row[:] for row in grid]
    stats = {'bc_calls': 0, 'loops': 0, 'search_calls': 0, 'backtracks': 0}

    changed = True
    while changed:
        changed = False
        stats['loops'] += 1

        if debug:
            print(f"\n--- Starting Iteration {stats['loops']} ---")

        for i in range(1, N + 1):
            for j in range(1, N + 1):
                if solution[i - 1][j - 1] == 0:
                    stats['bc_calls'] += 1
                    filtered = _cell_candidates(kb, i, j, solution, N, h_con, v_con)

                    if debug:
                        print(f"  Cell ({i},{j}) -> Candidates: {filtered}")

                    if len(filtered) == 1:
                        val = filtered[0]
                        solution[i - 1][j - 1] = val
                        kb.add_fact(Predicate('Given', i, j, val))
                        changed = True
                        if debug:
                            print(f"  >>> ASSIGNED Cell ({i},{j}) = {val}")

    if all(cell != 0 for row in solution for cell in row):
        return solution, stats

    solved = _search_with_sld(kb, solution, N, h_con, v_con, stats)
    if solved:
        return solution, stats

    return solution, stats
