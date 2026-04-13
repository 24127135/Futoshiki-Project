import time

# PART 1: DATA STRUCTURES & UNIFICATION

class Variable:
    def __init__(self, name): self.name = name

    def __repr__(self): return self.name

    def __eq__(self, other): return isinstance(other, Variable) and self.name == other.name

    def __hash__(self): return hash(self.name)


class Predicate:
    def __init__(self, name, *args):
        self.name = name
        self.args = list(args)

    def __repr__(self): return f"{self.name}({', '.join(map(str, self.args))})"

    def __eq__(self, other): return isinstance(other, Predicate) and self.name == other.name and self.args == other.args

    def __hash__(self): return hash((self.name, tuple(self.args)))


class Rule:
    def __init__(self, head, body):
        self.head = head
        self.body = body

    def fresh_copy(self, counter):
        mapping = {}

        def rename(pred):
            new_args = []
            for arg in pred.args:
                if isinstance(arg, Variable):
                    if arg.name not in mapping:
                        mapping[arg.name] = Variable(f"{arg.name}_{counter[0]}")
                    new_args.append(mapping[arg.name])
                else:
                    new_args.append(arg)
            return Predicate(pred.name, *new_args)

        counter[0] += 1
        return Rule(rename(self.head), [rename(b) for b in self.body])


class KnowledgeBase:
    def __init__(self):
        self.facts = []
        self.rules = []
        self._index = {}

    def add_fact(self, fact):
        if fact not in self.facts:
            self.facts.append(fact)
            key = (fact.name, len(fact.args))
            self._index.setdefault(key, []).append(fact)

    def add_rule(self, rule):
        self.rules.append(rule)

    def get_facts(self, name, arity):
        return list(self._index.get((name, arity), []))


def unify(x, y, theta):
    if theta is None: return None
    if x == y: return theta
    if isinstance(x, Variable): return unify_var(x, y, theta)
    if isinstance(y, Variable): return unify_var(y, x, theta)
    if isinstance(x, Predicate) and isinstance(y, Predicate):
        if x.name != y.name or len(x.args) != len(y.args): return None
        for a, b in zip(x.args, y.args): theta = unify(a, b, theta)
        return theta
    return None


def unify_var(var, x, theta):
    if var.name in theta: return unify(theta[var.name], x, theta)
    if isinstance(x, Variable) and x.name in theta: return unify(var, theta[x.name], theta)
    new_theta = theta.copy()
    new_theta[var.name] = x
    return new_theta


def substitute(pred, theta):
    if not isinstance(pred, Predicate): return pred
    new_args = []
    for arg in pred.args:
        if isinstance(arg, Variable) and arg.name in theta:
            new_args.append(theta[arg.name])
        else:
            new_args.append(arg)
    return Predicate(pred.name, *new_args)



# PART 2: BACKWARD CHAINING ENGINE (WITH CYCLE DETECTION)

_counter = [0]


def fol_bc_ask(kb, goals, theta, depth=0, max_depth=15, history=None):
    if theta is None: return
    if depth > max_depth: return
    if not goals:
        yield theta
        return

    if history is None: history = set()

    goal = goals[0]
    rest = goals[1:]
    subst_goal = substitute(goal, theta)

    # Cycle detection to prevent infinite loops with bi-directional rules
    goal_sig = f"{subst_goal.name}_{subst_goal.args[0]}_{subst_goal.args[1]}" if subst_goal.name == 'Val' else str(
        subst_goal)
    if goal_sig in history: return
    new_history = history | {goal_sig}

    for fact in kb.get_facts(goal.name, len(goal.args)):
        new_theta = unify(subst_goal, fact, theta)
        if new_theta is not None:
            yield from fol_bc_ask(kb, rest, new_theta, depth + 1, max_depth, new_history)

    for rule in kb.rules:
        fresh = rule.fresh_copy(_counter)
        new_theta = unify(subst_goal, fresh.head, theta)
        if new_theta is not None:
            yield from fol_bc_ask(kb, fresh.body + rest, new_theta, depth + 1, max_depth, new_history)


def query_candidates_bc(kb, i, j):
    target = Variable('?ans')
    query = [Predicate('Val', i, j, target)]
    seen = set()
    results = []
    for ans in fol_bc_ask(kb, query, {}, history=set()):
        val = ans.get('?ans')
        if isinstance(val, int) and val not in seen:
            seen.add(val)
            results.append(val)
    return results


# ==========================================
# PART 3: KNOWLEDGE BASE SETUP
# ==========================================

def build_kb(N, grid, h_con, v_con):
    kb = KnowledgeBase()
    domain = range(1, N + 1)

    for v in domain: kb.add_fact(Predicate('InRange', v))
    for a in domain:
        for b in domain:
            if a < b: kb.add_fact(Predicate('Less', a, b))
    for x in range(1, N): kb.add_fact(Predicate('Succ', x, x + 1))

    for i in range(1, N + 1):
        for j in range(1, N + 1):
            if grid[i - 1][j - 1] != 0:
                kb.add_fact(Predicate('Given', i, j, grid[i - 1][j - 1]))

    for i in range(1, N + 1):
        for j in range(1, N):
            if h_con[i - 1][j - 1] == 1:
                kb.add_fact(Predicate('LessH', i, j))
            elif h_con[i - 1][j - 1] == -1:
                kb.add_fact(Predicate('GreaterH', i, j))

    for i in range(1, N):
        for j in range(1, N + 1):
            if v_con[i - 1][j - 1] == 1:
                kb.add_fact(Predicate('LessV', i, j))
            elif v_con[i - 1][j - 1] == -1:
                kb.add_fact(Predicate('GreaterV', i, j))

    I, J = Variable('?i'), Variable('?j')
    V, V1, V2 = Variable('?v'), Variable('?v1'), Variable('?v2')
    JP, IP = Variable('?jp'), Variable('?ip')

    kb.add_rule(Rule(Predicate('Val', I, J, V), [Predicate('Given', I, J, V)]))

    # Bi-directional Inequality Rules
    kb.add_rule(Rule(Predicate('Val', I, JP, V2),
                     [Predicate('LessH', I, J), Predicate('Succ', J, JP), Predicate('Val', I, J, V1),
                      Predicate('InRange', V2), Predicate('Less', V1, V2)]))
    kb.add_rule(Rule(Predicate('Val', I, JP, V2),
                     [Predicate('GreaterH', I, J), Predicate('Succ', J, JP), Predicate('Val', I, J, V1),
                      Predicate('InRange', V2), Predicate('Less', V2, V1)]))
    kb.add_rule(Rule(Predicate('Val', IP, J, V2),
                     [Predicate('LessV', I, J), Predicate('Succ', I, IP), Predicate('Val', I, J, V1),
                      Predicate('InRange', V2), Predicate('Less', V1, V2)]))
    kb.add_rule(Rule(Predicate('Val', IP, J, V2),
                     [Predicate('GreaterV', I, J), Predicate('Succ', I, IP), Predicate('Val', I, J, V1),
                      Predicate('InRange', V2), Predicate('Less', V2, V1)]))

    kb.add_rule(Rule(Predicate('Val', I, J, V1),
                     [Predicate('LessH', I, J), Predicate('Succ', J, JP), Predicate('Val', I, JP, V2),
                      Predicate('InRange', V1), Predicate('Less', V1, V2)]))
    kb.add_rule(Rule(Predicate('Val', I, J, V1),
                     [Predicate('GreaterH', I, J), Predicate('Succ', J, JP), Predicate('Val', I, JP, V2),
                      Predicate('InRange', V1), Predicate('Less', V2, V1)]))
    kb.add_rule(Rule(Predicate('Val', I, J, V1),
                     [Predicate('LessV', I, J), Predicate('Succ', I, IP), Predicate('Val', IP, J, V2),
                      Predicate('InRange', V1), Predicate('Less', V1, V2)]))
    kb.add_rule(Rule(Predicate('Val', I, J, V1),
                     [Predicate('GreaterV', I, J), Predicate('Succ', I, IP), Predicate('Val', IP, J, V2),
                      Predicate('InRange', V1), Predicate('Less', V2, V1)]))

    return kb


# PART 4: UNIQUENESS FILTER & MAIN SOLVER


def filter_by_uniqueness(candidates, i, j, solution, N):
    used_in_row = set(solution[i - 1][c] for c in range(N) if solution[i - 1][c] != 0)
    used_in_col = set(solution[r][j - 1] for r in range(N) if solution[r][j - 1] != 0)
    forbidden = used_in_row | used_in_col
    return [v for v in candidates if v not in forbidden]


def solve_deductive(N, grid, h_con, v_con, debug=False):
    """
    Deductive Solver: Uses Backward Chaining + Row/Col Uniqueness.
    NO BACKTRACKING allowed.
    """
    kb = build_kb(N, grid, h_con, v_con)
    solution = [row[:] for row in grid]
    stats = {'bc_calls': 0, 'loops': 0}

    changed = True
    while changed:
        changed = False
        stats['loops'] += 1

        if debug: print(f"\n--- Starting Iteration {stats['loops']} ---")

        for i in range(1, N + 1):
            for j in range(1, N + 1):
                if solution[i - 1][j - 1] == 0:
                    stats['bc_calls'] += 1

                    bc_candidates = query_candidates_bc(kb, i, j)
                    candidates = bc_candidates if bc_candidates else list(range(1, N + 1))
                    filtered = filter_by_uniqueness(candidates, i, j, solution, N)

                    if debug: print(f"  Cell ({i},{j}) -> BC: {candidates} -> Filtered: {filtered}")

                    if len(filtered) == 1:
                        val = filtered[0]
                        solution[i - 1][j - 1] = val
                        kb.add_fact(Predicate('Given', i, j, val))
                        changed = True
                        if debug: print(f"  >>> ASSIGNED Cell ({i},{j}) = {val}")

    return solution, stats