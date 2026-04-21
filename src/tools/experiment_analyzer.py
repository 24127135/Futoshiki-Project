"""
Experiment analysis and comparison tool.

Processes experiment_results.csv and generates comparative analysis,
tables suitable for reports, and statistical summaries.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple
import statistics

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


@dataclass
class ResultRow:
    """Single result row."""
    input_file: str
    size: str
    algorithm: str
    status: str
    time_ms: float
    memory_mb: float
    iterations: str
    calls: str
    backtracks: str
    expansions: str
    error_msg: str


class ExperimentAnalyzer:
    """Analyzes experiment results."""
    
    def __init__(self, csv_file: Path):
        self.csv_file = Path(csv_file)
        self.results: List[ResultRow] = []
        self.load_csv()
    
    def load_csv(self) -> None:
        """Load results from CSV."""
        with open(self.csv_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.results.append(ResultRow(
                    input_file=row["input_file"],
                    size=row["size"],
                    algorithm=row["algorithm"],
                    status=row["status"],
                    time_ms=float(row["time_ms"]) if row["time_ms"] else 0,
                    memory_mb=float(row["memory_mb"]) if row["memory_mb"] else 0,
                    iterations=row["iterations"],
                    calls=row["calls"],
                    backtracks=row["backtracks"],
                    expansions=row["expansions"],
                    error_msg=row["error_msg"],
                ))
    
    def get_algorithms(self) -> List[str]:
        """Get unique algorithms."""
        return sorted(set(r.algorithm for r in self.results))
    
    def get_sizes(self) -> List[str]:
        """Get unique puzzle sizes."""
        sizes = set(r.size for r in self.results if r.size != "?")
        return sorted(sizes, key=lambda x: int(x.split("x")[0]))
    
    def filter_by_algo(self, algo: str) -> List[ResultRow]:
        """Filter results by algorithm."""
        return [r for r in self.results if r.algorithm == algo]
    
    def filter_by_size(self, size: str) -> List[ResultRow]:
        """Filter results by puzzle size."""
        return [r for r in self.results if r.size == size]
    
    def get_stats(self, rows: List[ResultRow]) -> Dict:
        """Calculate statistics for a result set."""
        solved = [r for r in rows if r.status == "SOLVED"]
        errors = [r for r in rows if r.status == "ERROR"]
        
        if not solved:
            return {
                "total": len(rows),
                "solved": 0,
                "errors": len(errors),
                "avg_time_ms": 0,
                "min_time_ms": 0,
                "max_time_ms": 0,
                "avg_memory_mb": 0,
            }
        
        times = [r.time_ms for r in solved]
        mems = [r.memory_mb for r in solved]
        
        return {
            "total": len(rows),
            "solved": len(solved),
            "errors": len(errors),
            "avg_time_ms": statistics.mean(times),
            "min_time_ms": min(times),
            "max_time_ms": max(times),
            "avg_memory_mb": statistics.mean(mems),
            "max_memory_mb": max(mems),
        }

    def _get_algorithm_summary(self) -> List[Dict[str, float]]:
        summary = []
        for algo in self.get_algorithms():
            rows = self.filter_by_algo(algo)
            solved = [r for r in rows if r.status == "SOLVED"]
            if solved:
                summary.append(
                    {
                        "algorithm": algo,
                        "avg_time_ms": statistics.mean(r.time_ms for r in solved),
                        "avg_memory_mb": statistics.mean(r.memory_mb for r in solved),
                        "solved": float(len(solved)),
                        "total": float(len(rows)),
                    }
                )
            else:
                summary.append(
                    {
                        "algorithm": algo,
                        "avg_time_ms": 0.0,
                        "avg_memory_mb": 0.0,
                        "solved": 0.0,
                        "total": float(len(rows)),
                    }
                )
        return summary

    def _get_size_summary(self) -> Dict[str, Dict[str, float]]:
        summary: Dict[str, Dict[str, float]] = {}
        for size in self.get_sizes():
            summary[size] = {}
            for algo in self.get_algorithms():
                rows = [r for r in self.results if r.size == size and r.algorithm == algo and r.status == "SOLVED"]
                summary[size][algo] = statistics.mean(r.time_ms for r in rows) if rows else 0.0
        return summary

    def _get_size_memory_summary(self) -> Dict[str, Dict[str, float]]:
        summary: Dict[str, Dict[str, float]] = {}
        for size in self.get_sizes():
            summary[size] = {}
            for algo in self.get_algorithms():
                rows = [r for r in self.results if r.size == size and r.algorithm == algo and r.status == "SOLVED"]
                summary[size][algo] = statistics.mean(r.memory_mb for r in rows) if rows else 0.0
        return summary

    def _get_input_time_summary(self) -> Dict[str, Dict[str, float]]:
        summary: Dict[str, Dict[str, float]] = {}
        input_files = sorted(set(r.input_file for r in self.results))
        for input_file in input_files:
            summary[input_file] = {}
            for algo in self.get_algorithms():
                rows = [
                    r
                    for r in self.results
                    if r.input_file == input_file and r.algorithm == algo and r.status == "SOLVED"
                ]
                summary[input_file][algo] = statistics.mean(r.time_ms for r in rows) if rows else 0.0
        return summary

    def _get_solved_rate_summary(self) -> List[Dict[str, float]]:
        summary = []
        for algo in self.get_algorithms():
            rows = self.filter_by_algo(algo)
            total = len(rows)
            solved = sum(1 for r in rows if r.status == "SOLVED")
            summary.append(
                {
                    "algorithm": algo,
                    "solved_rate": (solved / total * 100.0) if total else 0.0,
                    "solved": float(solved),
                    "total": float(total),
                }
            )
        return summary

    def save_charts(self, output_dir: Path | None = None) -> List[Path]:
        """Generate report-ready PNG charts."""
        if output_dir is None:
            output_dir = self.csv_file.parent / "charts"

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        saved_files: List[Path] = []
        algo_summary = self._get_algorithm_summary()
        algorithms = [row["algorithm"] for row in algo_summary]
        avg_times = [row["avg_time_ms"] for row in algo_summary]
        avg_mems = [row["avg_memory_mb"] for row in algo_summary]

        # Chart 1: average time by algorithm
        fig, ax = plt.subplots(figsize=(10, 5))
        bars = ax.bar(algorithms, avg_times, color=["#4C78A8", "#F58518", "#54A24B", "#E45756", "#72B7B2"][: len(algorithms)])
        ax.set_title("Average Solve Time by Algorithm")
        ax.set_ylabel("Time (ms)")
        ax.set_xlabel("Algorithm")
        ax.grid(axis="y", linestyle="--", alpha=0.3)
        ax.bar_label(bars, fmt="%.2f", padding=3, fontsize=8)
        fig.tight_layout()
        time_chart = output_dir / "avg_time_by_algorithm.png"
        fig.savefig(time_chart, dpi=200, bbox_inches="tight")
        plt.close(fig)
        saved_files.append(time_chart)

        # Chart 2: average memory by algorithm
        fig, ax = plt.subplots(figsize=(10, 5))
        bars = ax.bar(algorithms, avg_mems, color=["#72B7B2", "#54A24B", "#E45756", "#F58518", "#4C78A8"][: len(algorithms)])
        ax.set_title("Average Peak Memory by Algorithm")
        ax.set_ylabel("Memory (MB)")
        ax.set_xlabel("Algorithm")
        ax.grid(axis="y", linestyle="--", alpha=0.3)
        ax.bar_label(bars, fmt="%.4f", padding=3, fontsize=8)
        fig.tight_layout()
        mem_chart = output_dir / "avg_memory_by_algorithm.png"
        fig.savefig(mem_chart, dpi=200, bbox_inches="tight")
        plt.close(fig)
        saved_files.append(mem_chart)

        # Chart 3: average time by size and algorithm
        size_summary = self._get_size_summary()
        sizes = list(size_summary.keys())
        if sizes:
            fig, ax = plt.subplots(figsize=(11, 6))
            x_positions = range(len(sizes))
            width = 0.8 / max(1, len(algorithms))

            for index, algo in enumerate(algorithms):
                offsets = [x + (index - (len(algorithms) - 1) / 2) * width for x in x_positions]
                values = [size_summary[size][algo] for size in sizes]
                ax.bar(offsets, values, width=width, label=algo)

            ax.set_title("Average Solve Time by Puzzle Size")
            ax.set_ylabel("Time (ms)")
            ax.set_xlabel("Puzzle Size")
            ax.set_xticks(list(x_positions))
            ax.set_xticklabels(sizes)
            ax.grid(axis="y", linestyle="--", alpha=0.3)
            ax.legend(loc="upper left", fontsize=8)
            fig.tight_layout()
            size_chart = output_dir / "avg_time_by_size.png"
            fig.savefig(size_chart, dpi=200, bbox_inches="tight")
            plt.close(fig)
            saved_files.append(size_chart)

        # Chart 4: solved rate by algorithm
        solved_summary = self._get_solved_rate_summary()
        solved_algorithms = [row["algorithm"] for row in solved_summary]
        solved_rates = [row["solved_rate"] for row in solved_summary]
        fig, ax = plt.subplots(figsize=(10, 5))
        bars = ax.bar(solved_algorithms, solved_rates, color="#59A14F")
        ax.set_title("Solved Rate by Algorithm")
        ax.set_ylabel("Solved Rate (%)")
        ax.set_xlabel("Algorithm")
        ax.set_ylim(0, 105)
        ax.grid(axis="y", linestyle="--", alpha=0.3)
        ax.bar_label(bars, fmt="%.1f%%", padding=3, fontsize=8)
        fig.tight_layout()
        solved_chart = output_dir / "solved_rate_by_algorithm.png"
        fig.savefig(solved_chart, dpi=200, bbox_inches="tight")
        plt.close(fig)
        saved_files.append(solved_chart)

        # Chart 5: average memory by size and algorithm
        size_memory_summary = self._get_size_memory_summary()
        if sizes:
            fig, ax = plt.subplots(figsize=(11, 6))
            x_positions = range(len(sizes))
            width = 0.8 / max(1, len(algorithms))

            for index, algo in enumerate(algorithms):
                offsets = [x + (index - (len(algorithms) - 1) / 2) * width for x in x_positions]
                values = [size_memory_summary[size][algo] for size in sizes]
                ax.bar(offsets, values, width=width, label=algo)

            ax.set_title("Average Peak Memory by Puzzle Size")
            ax.set_ylabel("Memory (MB)")
            ax.set_xlabel("Puzzle Size")
            ax.set_xticks(list(x_positions))
            ax.set_xticklabels(sizes)
            ax.grid(axis="y", linestyle="--", alpha=0.3)
            ax.legend(loc="upper left", fontsize=8)
            fig.tight_layout()
            memory_size_chart = output_dir / "avg_memory_by_size.png"
            fig.savefig(memory_size_chart, dpi=200, bbox_inches="tight")
            plt.close(fig)
            saved_files.append(memory_size_chart)

        # Chart 6: time vs memory scatter by algorithm
        fig, ax = plt.subplots(figsize=(10, 6))
        markers = ["o", "s", "^", "D", "P", "X"]
        for index, algo in enumerate(algorithms):
            rows = [r for r in self.results if r.algorithm == algo and r.status == "SOLVED"]
            if not rows:
                continue
            ax.scatter(
                [r.time_ms for r in rows],
                [r.memory_mb for r in rows],
                label=algo,
                alpha=0.8,
                s=45,
                marker=markers[index % len(markers)],
            )

        ax.set_title("Time vs Memory Tradeoff")
        ax.set_xlabel("Time (ms)")
        ax.set_ylabel("Memory (MB)")
        ax.grid(True, linestyle="--", alpha=0.3)
        ax.legend(fontsize=8)
        fig.tight_layout()
        scatter_chart = output_dir / "time_vs_memory_scatter.png"
        fig.savefig(scatter_chart, dpi=200, bbox_inches="tight")
        plt.close(fig)
        saved_files.append(scatter_chart)

        # Chart 7: grouped time by input file and algorithm
        input_time_summary = self._get_input_time_summary()
        input_files = list(input_time_summary.keys())
        if input_files:
            fig, ax = plt.subplots(figsize=(14, 6))
            x_positions = range(len(input_files))
            width = 0.8 / max(1, len(algorithms))

            for index, algo in enumerate(algorithms):
                offsets = [x + (index - (len(algorithms) - 1) / 2) * width for x in x_positions]
                values = [input_time_summary[input_file][algo] for input_file in input_files]
                ax.bar(offsets, values, width=width, label=algo)

            ax.set_title("Solve Time by Input File")
            ax.set_ylabel("Time (ms)")
            ax.set_xlabel("Input File")
            ax.set_xticks(list(x_positions))
            ax.set_xticklabels(input_files, rotation=35, ha="right")
            ax.grid(axis="y", linestyle="--", alpha=0.3)
            ax.legend(loc="upper left", fontsize=8)
            fig.tight_layout()
            by_input_chart = output_dir / "time_by_input_grouped.png"
            fig.savefig(by_input_chart, dpi=200, bbox_inches="tight")
            plt.close(fig)
            saved_files.append(by_input_chart)

        return saved_files
    
    def print_algorithm_comparison(self) -> None:
        """Print overall algorithm comparison."""
        print("\n" + "=" * 110)
        print("ALGORITHM COMPARISON (All Inputs)")
        print("=" * 110)
        print(f"{'Algorithm':<18} {'Total':<8} {'Solved':<8} {'Errors':<8} {'Avg Time':<12} {'Min Time':<12} {'Avg Mem':<12}")
        print("-" * 110)
        
        for algo in self.get_algorithms():
            results = self.filter_by_algo(algo)
            stats = self.get_stats(results)
            
            print(
                f"{algo:<18} {stats['total']:<8} {stats['solved']:<8} "
                f"{stats['errors']:<8} {stats['avg_time_ms']:>10.2f}ms {stats['min_time_ms']:>10.2f}ms "
                f"{stats['avg_memory_mb']:>10.4f}MB"
            )
    
    def print_size_comparison(self) -> None:
        """Print results broken down by puzzle size."""
        print("\n" + "=" * 110)
        print("PERFORMANCE BY PUZZLE SIZE")
        print("=" * 110)
        
        for size in self.get_sizes():
            print(f"\n{size.upper()}:")
            print(f"{'Algorithm':<18} {'Solved':<8} {'Time (ms)':<12} {'Memory (MB)':<12} {'Operations':<20}")
            print("-" * 80)
            
            results_for_size = self.filter_by_size(size)
            
            # Group by algorithm
            by_algo = {}
            for r in results_for_size:
                if r.algorithm not in by_algo:
                    by_algo[r.algorithm] = []
                by_algo[r.algorithm].append(r)
            
            for algo in sorted(by_algo.keys()):
                algo_results = by_algo[algo]
                solved = [r for r in algo_results if r.status == "SOLVED"]
                
                if solved:
                    avg_time = sum(r.time_ms for r in solved) / len(solved)
                    avg_mem = sum(r.memory_mb for r in solved) / len(solved)
                    
                    ops = []
                    for r in solved:
                        if r.iterations and r.iterations != "None":
                            ops.append(f"iter={r.iterations}")
                        if r.calls and r.calls != "None":
                            ops.append(f"calls={r.calls}")
                        if r.expansions and r.expansions != "None":
                            ops.append(f"exp={r.expansions}")
                    
                    ops_str = ", ".join(ops) if ops else "N/A"
                    
                    print(
                        f"{algo:<18} {len(solved):<8} {avg_time:>10.2f}ms {avg_mem:>10.4f}MB "
                        f"{ops_str:<20}"
                    )
                else:
                    print(f"{algo:<18} {'0':<8} {'N/A':<12} {'N/A':<12} {'ERROR/UNSOLVED':<20}")
    
    def print_fastest_slowest(self) -> None:
        """Print fastest and slowest configurations."""
        print("\n" + "=" * 80)
        print("FASTEST & SLOWEST SOLVERS")
        print("=" * 80)
        
        solved_results = [r for r in self.results if r.status == "SOLVED"]
        
        if solved_results:
            sorted_by_time = sorted(solved_results, key=lambda r: r.time_ms)
            
            print("\nFastest 5:")
            for r in sorted_by_time[:5]:
                print(f"  {r.input_file:20s} + {r.algorithm:15s} = {r.time_ms:10.2f}ms ({r.memory_mb:7.4f}MB)")
            
            print("\nSlowest 5:")
            for r in sorted_by_time[-5:]:
                print(f"  {r.input_file:20s} + {r.algorithm:15s} = {r.time_ms:10.2f}ms ({r.memory_mb:7.4f}MB)")
    
    def print_all_results_table(self) -> None:
        """Print full results as table."""
        print("\n" + "=" * 140)
        print("ALL RESULTS")
        print("=" * 140)
        print(
            f"{'Input':<20} {'Size':<8} {'Algorithm':<15} {'Status':<10} "
            f"{'Time (ms)':<12} {'Mem (MB)':<12} {'Operations':<30}"
        )
        print("-" * 140)
        
        for r in sorted(self.results, key=lambda x: (x.input_file, x.algorithm)):
            ops = []
            if r.iterations and r.iterations != "None":
                ops.append(f"it={r.iterations}")
            if r.calls and r.calls != "None":
                ops.append(f"c={r.calls}")
            if r.backtracks and r.backtracks != "None":
                ops.append(f"bt={r.backtracks}")
            if r.expansions and r.expansions != "None":
                ops.append(f"ex={r.expansions}")
            
            ops_str = ", ".join(ops) if ops else "—"
            error_suffix = f" ({r.error_msg[:20]}...)" if r.error_msg else ""
            
            print(
                f"{r.input_file:<20} {r.size:<8} {r.algorithm:<15} {r.status:<10} "
                f"{r.time_ms:>10.2f}ms {r.memory_mb:>10.4f}MB {ops_str:<30}{error_suffix}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze experiment results"
    )
    parser.add_argument(
        "results_csv",
        type=Path,
        help="Path to experiment_results.csv"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Print all detailed results"
    )
    parser.add_argument(
        "--charts-dir",
        type=Path,
        default=None,
        help="Directory to write PNG charts (default: experiments/charts)",
    )
    
    args = parser.parse_args()
    
    if not args.results_csv.exists():
        print(f"Error: {args.results_csv} not found")
        return
    
    analyzer = ExperimentAnalyzer(args.results_csv)
    
    analyzer.print_algorithm_comparison()
    analyzer.print_size_comparison()
    analyzer.print_fastest_slowest()
    chart_files = analyzer.save_charts(args.charts_dir)
    print("\nSaved charts:")
    for chart_file in chart_files:
        print(f"  {chart_file}")
    
    if args.all:
        analyzer.print_all_results_table()
    
    print("\n" + "=" * 110)


if __name__ == "__main__":
    main()
