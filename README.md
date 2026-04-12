# Futoshiki Logic Solver

This workspace contains the Phase 1 starter code for a Futoshiki logic solver.

## Project Structure

- `src/parse_checker.py` - Phase 1 checker / entry point
- `src/futoshiki/io_parser.py` - input parser
- `src/futoshiki/state.py` - domain-based puzzle state
- `src/futoshiki/util/pretty.py` - puzzle and domain rendering
- `inputs/` - sample test cases (`input-01.txt` to `input-10.txt`)

## Requirements

- Python 3.7 or later
- No external packages are required for the current Phase 1 code

## Input Format

Each input file uses this structure:

1. First line: `N`, the puzzle size
2. Next `N` lines: the `N x N` grid
   - `0` means empty
   - `1..N` means a fixed clue
3. Next `N` lines: horizontal constraints
   - `1` means left `<` right
   - `-1` means left `>` right
   - `0` means no constraint
4. Next `N - 1` lines: vertical constraints
   - `1` means top `<` bottom
   - `-1` means top `>` bottom
   - `0` means no constraint

## Run the Checker

From the project root:

```powershell
python src/parse_checker.py inputs/input-01.txt
```

## What the Checker Prints

The checker loads the puzzle, builds the initial domains, and prints:

- the puzzle grid with inequality signs
- the initial domain table

In the domain table:
- `-` means the cell still has the full initial domain `1..N`
- `[2]`, `[1, 3]`, etc. mean the domain has been reduced

## Current Phase 1 Status

Completed:
- input parsing
- initial domain generation
- puzzle rendering
- 10 validated test cases

Next phases can build on this foundation with domain pruning, forward chaining, backward chaining, and search.
