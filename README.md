# Futoshiki Logic Solver

A comprehensive solver suite for the Futoshiki (Inequality Sudoku) puzzle using multiple algorithmic approaches, including constraint propagation, heuristic search, and logical inference.

## Overview

This project implements multiple solving strategies for Futoshiki puzzles, ranging from brute-force enumeration to sophisticated A* search with heuristics and backward-chaining inference. The system includes a graphical user interface, command-line tools, and a formal first-order logic representation with CNF grounding.

### Key Features

- **Multiple Solver Implementations**: Brute force, backtracking with Minimum Remaining Values (MRV), A* search, and SLD backward chaining
- **Constraint Propagation**: Forward pruning for efficient domain reduction
- **Graphical User Interface**: Interactive puzzle solving with visual feedback
- **Knowledge Base System**: First-order logic representation with conversion to Conjunctive Normal Form
- **Benchmark Suite**: Comprehensive testing across puzzle sizes 4x4 through 9x9
- **Zero External Dependencies**: Pure Python implementation with no required packages

## Prerequisites

- Python 3.7 or later
- No external packages required

## Project Structure

### Core Components

```
src/
├── futoshiki/                 # Core solver package
│   ├── io_parser.py           # Input file parsing
│   ├── state.py               # Puzzle state representation
│   ├── knowledge_base.py       # FOL to CNF grounding logic
│   ├── inference/              # Logical inference engines
│   │   ├── backward_chaining.py
│   │   └── bc_engine.py
│   └── solvers/                # Solver implementations
│       ├── brute_force.py
│       ├── backtracking.py
│       ├── forward_chaining.py
│       └── astar.py
│
└── tools/                      # Command-line tools and utilities
    ├── parse_checker.py        # Input validation
    ├── forward_pruning_report.py     # Single-puzzle analysis
    ├── forward_pruning_smoke.py      # Batch testing
    ├── brute_force.py          # CLI solver: brute force
    ├── backtracking.py         # CLI solver: MRV backtracking
    ├── backward_chaining.py    # CLI solver: SLD inference
    ├── astar.py                # CLI solver: A* search
    ├── export_kb_outputs.py    # Knowledge base export
    └── gui_launcher.py         # GUI entry point
```

### Supporting Directories

- **gui/** - Tkinter user interface modules
- **docs/** - Technical documentation (including A* admissibility proof)
- **inputs/** - Test puzzles (4x4 to 9x9)
- **solutions/** - Reference solutions for validation
- **outputs/** - Generated Knowledge Base outputs

## Input Format

Input files define a Futoshiki puzzle using the following structure:

```
N                           # Puzzle dimension (4-9)
[grid]                      # N lines: puzzle grid
[h_constraints]             # N lines: horizontal constraints
[v_constraints]             # N-1 lines: vertical constraints
```

**Grid Values:**
- `0` = empty cell (to be filled)
- `1..N` = fixed clue

**Horizontal Constraints** (N lines, each with N values):
- `1` = left < right
- `-1` = left > right
- `0` = no constraint

**Vertical Constraints** (N-1 lines, each with N values):
- `1` = top < bottom
- `-1` = top > bottom
- `0` = no constraint

## Quick Start

Execute from the project root directory.

### Parse and Validate Input

```powershell
python src/tools/parse_checker.py inputs/input-4x4-01.txt
```

### Solve with Different Algorithms

```powershell
# Brute force (exhaustive search)
python src/tools/brute_force.py inputs/input-4x4-01.txt

# Backtracking with MRV heuristic
python src/tools/backtracking.py inputs/input-4x4-01.txt

# A* search with admissible heuristic
python src/tools/astar.py inputs/input-4x4-01.txt

# SLD backward chaining with search fallback
python src/tools/backward_chaining.py inputs/input-4x4-01.txt
```

### Forward Pruning Analysis

```powershell
# Single-puzzle analysis
python src/tools/forward_pruning_report.py inputs/input-4x4-01.txt
python src/tools/forward_pruning_report.py inputs/input-4x4-01.txt --verbose

# Batch test all inputs
python src/tools/forward_pruning_smoke.py
python src/tools/forward_pruning_smoke.py --strict
```

### Knowledge Base Export

```powershell
python src/tools/export_kb_outputs.py
```

Generates Knowledge Base summaries and CNF clause dumps for all puzzles in `outputs/`.

### Launch GUI

```powershell
python src/tools/gui_launcher.py
```

## Algorithm Details

### Solvers

| Solver | Approach | Best For | Time Complexity |
|--------|----------|----------|-----------------|
| **Brute Force** | Complete enumeration | Small puzzles, verification | O(N^(N²)) |
| **Backtracking (MRV)** | Tree search with domain reduction | Medium puzzles | O(d^N) with pruning |
| **A* Search** | Heuristic-guided search | Larger puzzles | Depends on heuristic quality |
| **Backward Chaining** | SLD inference + search fallback | Constraint-heavy puzzles | Depends on KB size |

### Constraint Propagation

Forward pruning applies domain reduction rules before search:
- Uniqueness constraints
- Ordering constraint propagation
- Consistency checking

**Note**: Forward pruning alone may not fully solve harder puzzles. Use backtracking or A* for complete solutions.

## Testing and Validation

The benchmark suite includes 10 test cases:
- 2 puzzles each at sizes 4x4, 5x5, 6x6, 7x7, and 9x9

Test files follow naming conventions:
- **Input**: `inputs/input-{N}x{N}-{ID:02d}.txt`
- **Solution**: `solutions/solution-{N}x{N}-{ID:02d}.txt`
- **KB Output**: `outputs/output-{N}x{N}-{ID:02d}.txt`

## Documentation

- **Technical Proof**: See [docs/astar_admissibility_proof.md](docs/astar_admissibility_proof.md) for formal verification of the A* heuristic admissibility
- **Experiment Results**: See [experiments/EXPERIMENT_SUMMARY.md](experiments/EXPERIMENT_SUMMARY.md) for performance benchmarks

## Notes

- Solver implementations are located in `src/futoshiki/solvers/`
- Forward pruning results showing `FAIL` indicate the pruning-only pass did not fully solve the puzzle, not a program error
- For 6x6 puzzles and larger, backtracking or A* is recommended for guaranteed completion
- Backward chaining combines inference with search fallback for robust solving across puzzle sizes

