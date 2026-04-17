# Futoshiki Logic Solver

This repository now uses a single Python source root: `src/`.

## Project Structure

- `main.py` - GUI launcher
- `gui/` - Tkinter UI modules
- `src/parse_checker.py` - parser/domain checker entry point
- `src/futoshiki/` - parser, state, and rendering package
- `src/brute_force.py` - brute-force baseline solver
- `src/backtracking.py` - MRV backtracking solver
- `src/knowledge_base.py` - FOL to CNF grounding logic
- `src/export_kb_outputs.py` - writes KB conversion outputs into `Output/`
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
# 1) Parse + domain checker smoke test
python src/parse_checker.py inputs/input-4x4-01.txt

# 2) Solver runs on a real input file
python src/brute_force.py inputs/input-4x4-01.txt
python src/backtracking.py inputs/input-4x4-01.txt

# 3) Launch GUI
python main.py
```

## Generate KB Outputs

From the project root:

```powershell
python src/export_kb_outputs.py
```

This creates one output text file per input under `Output/` with KB summary and clause dumps.

