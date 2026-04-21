"""
Comprehensive experiment runner for all Futoshiki solvers.

Collects timing, memory, and operation count metrics across all algorithms and inputs.
Outputs results to CSV and generates summary reports.
"""

from __future__ import annotations

import argparse
import csv
import json
import multiprocessing as mp
import sys
import time
import tracemalloc
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from futoshiki.io_parser import parse_puzzle_file
from futoshiki.solvers.forward_chaining import run_forward_chaining
from futoshiki.solvers.backtracking import backtracking_solve
from futoshiki.solvers.brute_force import brute_force_solve
from futoshiki.solvers.astar import astar_solve


@dataclass
class ExperimentResult:
    """Single experiment result."""
    input_file: str
    size: str  # "4x4", "5x5", etc
    algorithm: str
    status: str  # "SOLVED", "UNSOLVED", "TIMEOUT", "ERROR"
    time_ms: float
    memory_mb: float
    iterations: Optional[int] = None
    calls: Optional[int] = None
    backtracks: Optional[int] = None
    expansions: Optional[int] = None
    error_msg: Optional[str] = None


def _run_algorithm_worker(input_file: str, algorithm: str, output_queue) -> None:
    """Run one algorithm in a child process for hard timeout control."""
    try:
        puzzle = parse_puzzle_file(Path(input_file))
        tracemalloc.start()

        solved = False
        iterations = None
        calls = None
        backtracks = None
        expansions = None

        if algorithm == "forward-chaining":
            result = run_forward_chaining(puzzle)
            solved = bool(result.solved and not result.inconsistent)
            iterations = int(result.iterations)
        elif algorithm == "backtracking":
            board = [row[:] for row in puzzle.grid]
            stats = {"calls": 0, "backtracks": 0}
            solution = backtracking_solve(
                board,
                puzzle.horizontal,
                puzzle.vertical,
                puzzle.n,
                stats,
            )
            solved = solution is not None
            calls = int(stats.get("calls", 0))
            backtracks = int(stats.get("backtracks", 0))
        elif algorithm == "brute-force":
            board = [row[:] for row in puzzle.grid]
            stats = {"calls": 0, "backtracks": 0}
            solution = brute_force_solve(
                board,
                puzzle.horizontal,
                puzzle.vertical,
                puzzle.n,
                stats,
            )
            solved = solution is not None
            calls = int(stats.get("calls", 0))
            backtracks = int(stats.get("backtracks", 0))
        elif algorithm == "astar":
            board = [row[:] for row in puzzle.grid]
            stats = {"expansions": 0}
            solution = astar_solve(
                board,
                puzzle.horizontal,
                puzzle.vertical,
                puzzle.n,
                stats,
            )
            solved = solution is not None
            expansions = int(stats.get("expansions", 0))
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        _current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        output_queue.put(
            {
                "ok": True,
                "solved": solved,
                "memory_mb": peak / 1024 / 1024,
                "iterations": iterations,
                "calls": calls,
                "backtracks": backtracks,
                "expansions": expansions,
            }
        )
    except Exception as e:
        output_queue.put({"ok": False, "error": str(e)})


class ExperimentRunner:
    """Orchestrates experiment execution across all algorithms and inputs."""

    def __init__(
        self,
        inputs_dir: Path,
        output_dir: Path,
        default_timeout_s: float,
        timeout_config_path: Optional[Path],
    ):
        self.inputs_dir = Path(inputs_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.default_timeout_s = default_timeout_s
        self.timeout_config_path = Path(timeout_config_path) if timeout_config_path else None
        self.timeout_config = self._load_timeout_config()
        self.results: list[ExperimentResult] = []

    def _load_timeout_config(self) -> Dict[str, Any]:
        """Load timeout mapping config from JSON file."""
        if self.timeout_config_path is None:
            return {}

        if not self.timeout_config_path.exists():
            return {}

        try:
            with open(self.timeout_config_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            return payload if isinstance(payload, dict) else {}
        except Exception:
            return {}

    def _get_timeout_for_algorithm(self, algorithm: str) -> float:
        """Resolve timeout from algorithm-level config map with fallback.

        Priority order:
        1) algorithms[algorithm]
        2) default
        3) CLI --default-timeout
        """
        algo_map = self.timeout_config.get("algorithms", {})
        default_cfg = self.timeout_config.get("default")

        candidate = None
        if isinstance(algo_map, dict):
            candidate = algo_map.get(algorithm)

        if candidate is None:
            candidate = default_cfg

        if candidate is not None:
            try:
                return max(0.0, float(candidate))
            except (TypeError, ValueError):
                pass

        return max(0.0, float(self.default_timeout_s))

    def _run_with_timeout(
        self,
        puzzle_file: Path,
        algorithm: str,
        display_name: Optional[str] = None,
    ) -> ExperimentResult:
        """Run one algorithm with process-level timeout enforcement."""
        try:
            puzzle = parse_puzzle_file(puzzle_file)
            size_str = f"{puzzle.n}x{puzzle.n}"
            timeout_s = self._get_timeout_for_algorithm(algorithm)

            ctx = mp.get_context("spawn")
            output_queue = ctx.Queue()
            proc = ctx.Process(
                target=_run_algorithm_worker,
                args=(str(puzzle_file), algorithm, output_queue),
            )

            start = time.perf_counter()
            proc.start()
            proc.join(timeout_s if timeout_s > 0 else None)

            if proc.is_alive():
                proc.terminate()
                proc.join()
                return ExperimentResult(
                    input_file=puzzle_file.name,
                    size=size_str,
                    algorithm=display_name or algorithm,
                    status="TIMEOUT",
                    time_ms=timeout_s * 1000,
                    memory_mb=0,
                    error_msg=f"timeout after {timeout_s:.1f}s",
                )

            elapsed = time.perf_counter() - start

            if output_queue.empty():
                return ExperimentResult(
                    input_file=puzzle_file.name,
                    size=size_str,
                    algorithm=display_name or algorithm,
                    status="ERROR",
                    time_ms=elapsed * 1000,
                    memory_mb=0,
                    error_msg="worker ended without result",
                )

            payload = output_queue.get()
            if not payload.get("ok", False):
                return ExperimentResult(
                    input_file=puzzle_file.name,
                    size=size_str,
                    algorithm=display_name or algorithm,
                    status="ERROR",
                    time_ms=elapsed * 1000,
                    memory_mb=0,
                    error_msg=payload.get("error", "unknown error"),
                )

            return ExperimentResult(
                input_file=puzzle_file.name,
                size=size_str,
                algorithm=display_name or algorithm,
                status="SOLVED" if bool(payload.get("solved", False)) else "UNSOLVED",
                time_ms=elapsed * 1000,
                memory_mb=float(payload.get("memory_mb", 0.0)),
                iterations=payload.get("iterations"),
                calls=payload.get("calls"),
                backtracks=payload.get("backtracks"),
                expansions=payload.get("expansions"),
            )
        except Exception as e:
            return ExperimentResult(
                input_file=puzzle_file.name,
                size="?",
                algorithm=display_name or algorithm,
                status="ERROR",
                time_ms=0,
                memory_mb=0,
                error_msg=str(e),
            )
    
    def get_input_files(self) -> list[Path]:
        """Get all input puzzle files sorted."""
        files = sorted(self.inputs_dir.glob("input-*.txt"))
        return files
    
    def run_forward_chaining_exp(self, puzzle_file: Path) -> ExperimentResult:
        """Run forward chaining experiment."""
        return self._run_with_timeout(puzzle_file, "forward-chaining")
    
    def run_backtracking_exp(self, puzzle_file: Path) -> ExperimentResult:
        """Run backtracking experiment."""
        return self._run_with_timeout(puzzle_file, "backtracking")
    
    def run_brute_force_exp(self, puzzle_file: Path) -> ExperimentResult:
        """Run brute force experiment."""
        return self._run_with_timeout(puzzle_file, "brute-force")
    
    def run_astar_exp(self, puzzle_file: Path) -> ExperimentResult:
        """Run A* experiment."""
        return self._run_with_timeout(puzzle_file, "astar")
    
    def run_all_experiments(self, verbose: bool = False) -> None:
        """Run all experiments on all input files."""
        input_files = self.get_input_files()
        algorithms = [
            ("forward-chaining", self.run_forward_chaining_exp),
            ("backtracking", self.run_backtracking_exp),
            ("brute-force", self.run_brute_force_exp),
            ("astar", self.run_astar_exp),
        ]
        
        total = len(input_files) * len(algorithms)
        completed = 0
        
        for input_file in input_files:
            for algo_name, algo_func in algorithms:
                completed += 1
                status_msg = f"[{completed}/{total}] {input_file.name:20s} + {algo_name:15s}"
                
                if verbose:
                    print(status_msg, end=" ", flush=True)
                
                result = algo_func(input_file)
                self.results.append(result)
                
                if verbose:
                    print(f"-> {result.status:8s} ({result.time_ms:7.2f}ms)", flush=True)
        
        print(f"\n[OK] Completed {total} experiments")
    
    def save_csv(self, filename: str = "experiment_results.csv") -> Path:
        """Export results to CSV."""
        output_file = self.output_dir / filename
        
        fieldnames = [
            "input_file", "size", "algorithm", "status",
            "time_ms", "memory_mb", "iterations", "calls",
            "backtracks", "expansions", "error_msg"
        ]
        
        with open(output_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for result in self.results:
                writer.writerow(asdict(result))
        
        print(f"[OK] Results saved to: {output_file}")
        return output_file
    
    def print_summary(self) -> None:
        """Print summary table."""
        if not self.results:
            print("No results to display")
            return
        
        print("\n" + "=" * 100)
        print("EXPERIMENT SUMMARY")
        print("=" * 100)
        
        # Group by algorithm
        by_algo = {}
        for result in self.results:
            if result.algorithm not in by_algo:
                by_algo[result.algorithm] = []
            by_algo[result.algorithm].append(result)
        
        for algo in sorted(by_algo.keys()):
            results = by_algo[algo]
            solved = sum(1 for r in results if r.status == "SOLVED")
            errors = sum(1 for r in results if r.status == "ERROR")
            total = len(results)
            
            avg_time = sum(r.time_ms for r in results if r.status != "ERROR") / max(1, total - errors)
            avg_mem = sum(r.memory_mb for r in results if r.status != "ERROR") / max(1, total - errors)
            
            print(f"\n{algo.upper()}:")
            print(f"  Results:  {solved} SOLVED, {errors} ERRORS, {total} total")
            print(f"  Avg Time: {avg_time:8.2f} ms")
            print(f"  Avg Mem:  {avg_mem:8.4f} MB")
        
        print("\n" + "=" * 100)
    
    def save_json(self, filename: str = "experiment_results.json") -> Path:
        """Export results to JSON for detailed analysis."""
        output_file = self.output_dir / filename
        
        with open(output_file, "w") as f:
            json.dump(
                [asdict(r) for r in self.results],
                f,
                indent=2
            )
        
        print(f"[OK] JSON export saved to: {output_file}")
        return output_file


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run comprehensive experiments on all Futoshiki solvers"
    )
    parser.add_argument(
        "--inputs",
        type=Path,
        default=Path("inputs"),
        help="Path to inputs directory (default: inputs/)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("experiments"),
        help="Path to output directory (default: experiments/)"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print progress for each experiment"
    )
    parser.add_argument(
        "--default-timeout",
        type=float,
        default=120.0,
        help="Default timeout in seconds per algorithm/input when config does not override (default: 120)",
    )
    parser.add_argument(
        "--timeout-config",
        type=Path,
        default=Path("experiments/timeout_config.json"),
        help="JSON file mapping per-algorithm timeout values (default: experiments/timeout_config.json)",
    )
    
    args = parser.parse_args()
    
    runner = ExperimentRunner(
        args.inputs,
        args.output,
        default_timeout_s=args.default_timeout,
        timeout_config_path=args.timeout_config,
    )
    
    print(f"Starting experiments...")
    print(f"Inputs:  {args.inputs}")
    print(f"Output:  {args.output}")
    print()
    
    runner.run_all_experiments(verbose=args.verbose)
    runner.print_summary()
    runner.save_csv()
    runner.save_json()


if __name__ == "__main__":
    main()
