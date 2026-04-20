import heapq
import itertools
from collections import deque
from typing import Dict, List, Optional, Tuple


def get_neighbors(r: int, c: int, N: int) -> List[Tuple[int, int]]:
    neighbors = set()
    for i in range(N):
        if i != c: neighbors.add((r, i))
        if i != r: neighbors.add((i, c))
    return list(neighbors)


def check_constraint(r1, c1, v1, r2, c2, v2, h_con, v_con) -> bool:
    if r1 == r2 or c1 == c2:
        if v1 == v2: return False

    if r1 == r2:
        if c2 == c1 + 1:
            if h_con[r1][c1] == 1 and not (v1 < v2): return False
            if h_con[r1][c1] == -1 and not (v1 > v2): return False
        elif c1 == c2 + 1:
            if h_con[r2][c2] == 1 and not (v1 > v2): return False
            if h_con[r2][c2] == -1 and not (v1 < v2): return False

    if c1 == c2:
        if r2 == r1 + 1:
            if v_con[r1][c1] == 1 and not (v1 < v2): return False
            if v_con[r1][c1] == -1 and not (v1 > v2): return False
        elif r1 == r2 + 1:
            if v_con[r2][c2] == 1 and not (v1 > v2): return False
            if v_con[r2][c2] == -1 and not (v1 < v2): return False

    return True


def revise(domains, r1, c1, r2, c2, h_con, v_con) -> bool:
    revised = False
    to_remove = []

    for v1 in domains[r1][c1]:
        if not any(check_constraint(r1, c1, v1, r2, c2, v2, h_con, v_con) for v2 in domains[r2][c2]):
            to_remove.append(v1)

    for v in to_remove:
        domains[r1][c1].remove(v)
        revised = True

    return revised


def ac3(N, domains, h_con, v_con, assigned_cell=None) -> bool:
    queue = deque()

    if assigned_cell:
        r, c = assigned_cell
        for nr, nc in get_neighbors(r, c, N):
            queue.append((nr, nc, r, c))
    else:
        for r in range(N):
            for c in range(N):
                for nr, nc in get_neighbors(r, c, N):
                    queue.append((r, c, nr, nc))

    while queue:
        r1, c1, r2, c2 = queue.popleft()
        if revise(domains, r1, c1, r2, c2, h_con, v_con):
            if len(domains[r1][c1]) == 0:
                return False
            for nr, nc in get_neighbors(r1, c1, N):
                if (nr, nc) != (r2, c2):
                    queue.append((nr, nc, r1, c1))
    return True


def get_h_base(state, N) -> int:
    return sum(1 for r in range(N) for c in range(N) if state[r][c] == 0)


def get_h_tie(domains, state, N) -> int:
    score = 0
    min_dom = float('inf')
    has_empty = False
    for r in range(N):
        for c in range(N):
            if state[r][c] == 0:
                has_empty = True
                d_len = len(domains[r][c])
                score += (d_len - 1)
                if d_len < min_dom:
                    min_dom = d_len
    if has_empty:
        return score + 2 * min_dom
    return 0


def lcv_sort(values, r, c, domains, N, h_con, v_con):
    neighbors = get_neighbors(r, c, N)

    def impact(val):
        score = 0
        for nr, nc in neighbors:
            if 1 < len(domains[nr][nc]) <= 3:
                for v2 in domains[nr][nc]:
                    if not check_constraint(r, c, val, nr, nc, v2, h_con, v_con):
                        score += 1
        return score

    return sorted(values, key=impact)


def astar_solve(grid: List[List[int]], h_con: List[List[int]], v_con: List[List[int]], N: int, stats: Dict[str, int]) -> Optional[List[List[int]]]:
    stats.setdefault("expansions", 0)

    initial_state = [row[:] for row in grid]
    initial_domains = []
    for r in range(N):
        row_d = []
        for c in range(N):
            if initial_state[r][c] != 0:
                row_d.append([initial_state[r][c]])
            else:
                row_d.append(list(range(1, N + 1)))
        initial_domains.append(row_d)

    if not ac3(N, initial_domains, h_con, v_con):
        return None

    open_list = []
    counter = itertools.count()
    best_g = {}

    g = 0
    h_base = get_h_base(initial_state, N)
    f = g + h_base
    h_tie = get_h_tie(initial_domains, initial_state, N)

    heapq.heappush(open_list, (f, h_tie, g, next(counter), initial_state, initial_domains))

    while open_list:
        curr_f, curr_h_tie, curr_g, _, curr_state, curr_domains = heapq.heappop(open_list)

        state_key = (
            tuple(tuple(row) for row in curr_state),
            tuple(tuple(tuple(d) for d in row) for row in curr_domains)
        )
        if state_key in best_g and best_g[state_key] <= curr_g:
            continue
        best_g[state_key] = curr_g

        stats['expansions'] += 1
        curr_h_base = curr_f - curr_g

        if curr_h_base == 0:
            return curr_state

        min_len = float('inf')
        best_cell = None
        for r in range(N):
            for c in range(N):
                if curr_state[r][c] == 0:
                    dl = len(curr_domains[r][c])
                    if dl < min_len:
                        min_len = dl
                        best_cell = (r, c)

        if not best_cell: continue
        r, c = best_cell

        sorted_values = lcv_sort(curr_domains[r][c], r, c, curr_domains, N, h_con, v_con)

        for val in sorted_values:
            child_state = [row[:] for row in curr_state]
            child_state[r][c] = val

            child_domains = [[list(d) for d in row] for row in curr_domains]
            child_domains[r][c] = [val]

            if ac3(N, child_domains, h_con, v_con, assigned_cell=(r, c)):
                child_g = curr_g + 1
                child_h_base = get_h_base(child_state, N)
                child_f = child_g + child_h_base
                child_h_tie = get_h_tie(child_domains, child_state, N)

                heapq.heappush(open_list, (child_f, child_h_tie, child_g, next(counter), child_state, child_domains))

    return None
