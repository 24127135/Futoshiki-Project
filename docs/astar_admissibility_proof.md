# A* Heuristic Admissibility Proof

## Context

The A* solver in this project is implemented in src/futoshiki/solvers/astar.py.

It uses:
- State: a partial assignment of the N x N grid.
- Action: assign one value to one empty cell.
- Step cost: 1 per assignment.
- Goal: fully assigned grid that satisfies all constraints.

The evaluation function is:

f(s) = g(s) + h(s)

where:
- g(s) = number of assignments made from the initial state.
- h(s) = number of currently empty cells.

In code:
- get_h_base(state, N) returns the empty-cell count.
- get_h_tie(...) is a tie-break score only and is not added to f.

## Claim

h(s) = number of empty cells is admissible.

## Proof

Let E(s) be the number of empty cells in state s.
The heuristic is h(s) = E(s).

Each legal action in this search fills exactly one empty cell.
Therefore, any path from s to a goal state must perform at least E(s) actions, because all E(s) empty cells must eventually be assigned.

Let h*(s) be the true optimal remaining path cost from s to a goal.
From the argument above:

h*(s) >= E(s) = h(s)

So h(s) never overestimates h*(s). Therefore h is admissible.

## Consistency (Monotonicity)

For any transition s -> s' by assigning one cell:
- Cost c(s, s') = 1
- E(s') = E(s) - 1

Hence:

h(s) = E(s) <= 1 + E(s') = c(s, s') + h(s')

So h is also consistent.

## Note on Tie-Breaking

The implementation includes get_h_tie(...) to break ties among states with equal f.
This tie-break value is only the second sorting key in the heap tuple and does not alter f = g + h.
Therefore it does not affect admissibility of the A* heuristic.
