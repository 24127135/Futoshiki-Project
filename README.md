# Futoshiki Logic Solver

This repository now uses a single Python source root: `src/`.

## Project Structure

- `gui/` - Tkinter UI modules
- `src/tools/parse_checker.py` - parse-only checker entry point
- `src/tools/forward_pruning_report.py` - Single-input forward-pruning report
- `src/tools/forward_pruning_smoke.py` - Batch smoke test for forward-pruning over multiple inputs
- `src/tools/brute_force.py` - brute-force solver CLI
- `src/tools/backtracking.py` - MRV backtracking solver CLI
- `src/tools/backward_chaining.py` - SLD backward-chaining solver CLI
- `src/tools/astar.py` - A* solver CLI
- `src/tools/export_kb_outputs.py` - Knowledge Base export CLI
- `src/tools/gui_launcher.py` - GUI launcher
- `src/futoshiki/` - parser, state, rendering, and solver packages
- `src/futoshiki/solvers/` - shared solver implementations (forward chaining, brute force, backtracking)
- `docs/astar_admissibility_proof.md` - formal admissibility proof for A* heuristic
- `src/futoshiki/knowledge_base.py` - FOL to CNF grounding logic
- `inputs/` - puzzle inputs (`input-4x4-01.txt` to `input-9x9-10.txt`)
- `solutions/` - reference solutions for the same set
- `Output/` - generated Knowledge Base conversion outputs

## Requirements

- Python 3.7 or later
- No external packages are required

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

## How To Test

From project root:

```powershell
# 1) Parse-only checker smoke test
python src/tools/parse_checker.py inputs/input-4x4-01.txt

# 2) Forward-pruning report for one puzzle
python src/tools/forward_pruning_report.py inputs/input-4x4-01.txt
python src/tools/forward_pruning_report.py inputs/input-4x4-01.txt --verbose

# 2b) Batch smoke test for all inputs
python src/tools/forward_pruning_smoke.py
python src/tools/forward_pruning_smoke.py --strict

# 3) Solver runs on a real input file
python src/tools/brute_force.py inputs/input-4x4-01.txt
python src/tools/backtracking.py inputs/input-4x4-01.txt
python src/tools/backward_chaining.py inputs/input-4x4-01.txt
python src/tools/astar.py inputs/input-4x4-01.txt

#   The solver implementations live in `src/futoshiki/solvers/`

# 4) Export KB outputs
python src/tools/export_kb_outputs.py

# 5) Launch GUI
python src/tools/gui_launcher.py
```

## Generate KB Outputs

From the project root:

```powershell
python src/tools/export_kb_outputs.py
```

This creates one output text file per input under `Output/` with KB summary and clause dumps.

## Notes on Forward Pruning Results

- `forward_pruning_report.py` prints summary lines by default to keep terminal output small.
- Use `--verbose` when you need full grid and domain dumps.
- A `FAIL` in `forward_pruning_smoke.py` means the pruning-only pass did not fully solve that puzzle (`Solved=False`, `Inconsistent=False`), not that the program crashed.
- Use `src/tools/backtracking.py` for complete solving on harder 6x6+ inputs.
- `src/tools/backward_chaining.py` combines SLD-style candidate inference with search fallback to fully solve harder inputs.

