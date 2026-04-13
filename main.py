import sys
import os
# Chỉ đường cho Python biết thư mục 'src' nằm ở đâu
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

import argparse
import time
from pathlib import Path

# Import hàm đọc file của bạn
from futoshiki.io_parser import parse_puzzle_file
# Import thuật toán suy diễn (đảm bảo file solver_deductive.py đã được bạn bỏ vào folder src/futoshiki/)
from futoshiki.solver_deductive import solve_deductive

def print_solution(N, solution, h_con, v_con):
    """Hàm in bảng console đã được căn lề chuẩn"""
    for i in range(N):
        row_str = ""
        for j in range(N):
            val = solution[i][j]
            row_str += str(val) if val != 0 else "_"
            if j < N - 1:
                if h_con[i][j] == 1:
                    row_str += " < "
                elif h_con[i][j] == -1:
                    row_str += " > "
                else:
                    row_str += "   "
        print("  " + row_str)

        if i < N - 1:
            vc_str = ""
            for j in range(N):
                if v_con[i][j] == 1:
                    vc_str += "^"
                elif v_con[i][j] == -1:
                    vc_str += "v"
                else:
                    vc_str += " "
                if j < N - 1: vc_str += "   "
            print("  " + vc_str)


def main() -> None:
    # 1. Thiết lập đọc Argument từ Terminal (Giống parse_checker.py)
    parser = argparse.ArgumentParser(description="Run Deductive Solver on a Futoshiki puzzle file")
    parser.add_argument("input_file", type=Path, help="Path to input-XX.txt")
    parser.add_argument("--debug", action="store_true", help="Print step-by-step reasoning")
    args = parser.parse_args()

    # 2. Dùng io_parser của bạn để đọc file txt
    try:
        puzzle = parse_puzzle_file(args.input_file)
    except Exception as e:
        print(f"Lỗi khi đọc file: {e}")
        return

    N = puzzle.n
    grid = puzzle.grid
    h_con = puzzle.horizontal
    v_con = puzzle.vertical

    print("=" * 65)
    print(f"  TEST: DEDUCTIVE SOLVER (BC + UNIQUENESS) ON {args.input_file.name}")
    print("=" * 65)

    print("\n[Input Grid]:")
    print_solution(N, grid, h_con, v_con)

    # 3. Chạy thuật toán Backward Chaining
    start = time.time()
    res, stats = solve_deductive(N, grid, h_con, v_con, debug=args.debug)
    elapsed = (time.time() - start) * 1000

    print("\n[Result]:")
    print_solution(N, res, h_con, v_con)

    # 4. Đánh giá kết quả
    unsolved = sum(1 for i in range(N) for j in range(N) if res[i][j] == 0)

    print("\n" + "=" * 65)
    if unsolved > 0:
        print(f"⚠️ STUCK! Left {unsolved} empty cells.")
        print("Conclusion: Pure Deduction is insufficient for this puzzle's complexity.")
        print("It requires Backtracking (guessing) to explore multiple branches.")
    else:
        print(f"✅ SUCCESS! The puzzle was fully solved by Pure Deduction!")

    print(f"Stats -> BC Calls: {stats['bc_calls']} | Inference Loops: {stats['loops']}")
    print(f"Time: {elapsed:.2f} ms")
    print("=" * 65)


if __name__ == "__main__":
    main()