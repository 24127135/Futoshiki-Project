# Overview

## **Project Overview: Futoshiki Logic Solver**

### **Problem Statement**

The challenge is to solve Futoshiki (meaning "inequality" in Japanese), a logic-based number placement puzzle originally popularized in Japan. The puzzle is played on an N x N grid where the player must fill in numbers from 1 to N. Unlike Sudoku, Futoshiki explicitly enforces inequality relations ("less than" or "greater than") between adjacent cells, making it a rich domain for First-Order Logic (FOL) reasoning. The rules are naturally expressed as universally quantified sentences over all cells, rows, and columns.

### **Goal**

The primary objective is to formalize the puzzle rules in First-Order Logic and implement several inference mechanisms from scratch to solve the puzzle. The solver must assign a number from 1 to N to every empty cell such that:

* **Row Uniqueness**: Every number appears exactly once in each row.  
* **Column Uniqueness**: Every number appears exactly once in each column.  
* **Inequality Satisfaction**: Each inequality sign must hold between the values of the corresponding adjacent cells.  
* **Clue Respect**: Pre-filled cells must keep their original values.

  ### **Approach**

The project follows a rigorous logical pipeline to move from abstract rules to a functional solver:

* **FOL Formalization**: Expressing the puzzle constraints as closed FOL sentences using predicates like Val(i, j, v) for cell values and LessH(i, j) for horizontal inequalities.  
* **Inference Strategies**:  
  * **Forward Chaining**: Starting from known facts (Given clues, Inequalities) and applying Modus Ponens exhaustively to derive new facts.  
  * **Backward Chaining**: Implementing a Prolog-style interpreter using SLD resolution to query individual cell values.  
  * **A-Star Search**: Designing an admissible heuristic for partial assignments to search the state space efficiently.  
* **Knowledge Base Grounding**: Instantiating FOL axioms over the concrete index domain to obtain a propositional theory for the solver to process.

  ### **Requirements**

The project must meet the following strict criteria for the Faculty of Information Technology, University of Science, VNU-HCM:

* **Implementation**: All source code must be written in Python (3.7 or later). Main inference algorithms (Forward/Backward chaining, A-Star) must be implemented manually without external solvers.  
* **Testing**: Students must design 10 different input files covering grid sizes 4x4, 5x5, 6x6, 7x7, and 9x9.  
* **Reporting**: A well-formatted PDF report including formal FOL axioms, step-by-step CNF derivations for three non-trivial axioms, and a comparative analysis of algorithms using charts and tables.  
* **Demonstration**: A video recording showing the program running on at least three test cases and walking through key algorithmic steps.

## **Project Planning and Task Distribution**

This project was executed over a 15-day period by a team of three members. Responsibilities were divided based on the core components of First-Order Logic formalization, inference engine implementation, and performance analysis.

### **Team Member Responsibilities**

| Member | Primary Responsibilities | Completion % |
| :---- | :---- | :---- |
| **MTri** | Input/Output Parser, Forward Chaining implementation, Heuristic design (MRV), and Performance data analysis . |  |
| **DKhai** | FOL Axiom formalization, step-by-step CNF derivation, Backward Chaining (SLD Resolution), and A-Star Search engine . |  |
| **THai** | Ground KB generation logic, Brute-force/Backtracking baselines, GUI development (Bonus), and Report assembly. |  |

### 

### **Detailed Task Distribution**

* **MTri**:  
  * Developed the system to parse input files and represent the grid state with variable domains .  
  * Implemented the Forward Chaining algorithm from scratch to propagate facts and detect contradictions.  
  * Designed and justified the admissible heuristic used to guide the A-Star search.  
  * Conducted experiments across 10 test cases and generated comparative charts for the final report .  
* **DKhai**:  
  * Formalized all Futoshiki rules into First-Order Logic sentences.  
  * Performed manual, step-by-step CNF conversions for three non-trivial axioms.  
  * Built the Prolog-style Backward Chaining interpreter to support individual cell queries.  
  * Developed the A-Star search algorithm using the priority queue and heuristic integration.  
* **THai**:  
  * Implemented the function to automatically generate a ground Knowledge Base for any grid size N.  
  * Developed the Brute-force and Backtracking solvers to provide performance baselines for comparison.  
  * Created a Graphical User Interface (GUI) to visualize the solving process for all grid sizes.  
  * Managed the final project structure, documentation, and demo video production.

# MTri

### **Phase 1: The Foundation (Days 1–3)**

**Objective:** Turn the project's text format into a programmable environment.

* **Day 1: The Parser**  
  * **Task:** Write a script to read input-XX.txt. You must handle the grid size N, the grid of values, horizontal constraints (1, 0, \-1), and vertical constraints .  
  * **Debug:** Print the loaded grid and constraints in a "pretty-print" format to ensure the index (i, j) matches the visual layout.  
  * **Checklist:** Can your code load both a 4x4 and a 9x9 grid without crashing?  
* **Day 2: State Representation**  
  * **Task:** Create a FutoshikiState class. Instead of just a single number, each cell should have a **domain** (a list of possible values from 1 to N).  
  * **Debug:** Initialize a 4x4 state. A cell with a given clue of '2' should have a domain of \[2\]. An empty cell should have \[1, 2, 3, 4\].  
  * **Checklist:** Does every cell have a domain initialized correctly based on N?  
* **Day 3: Test Case Generation**  
  * **Task:** Create 10 input files named input-01.txt to input-10.txt. Mix grid sizes: 4x4, 5x5, 6x6, 7x7, and 9x9.  
  * **Debug:** Cross-check your input-01.txt manually against the example grid provided in the project description.  
  * **Checklist:** Do you have all 10 files ready in the correct /Inputs directory?

  ---

  ### **Phase 2: Forward Chaining Implementation (Days 4–7)**

**Objective:** Implement the logic-based solver to propagate facts.

* **Day 4: Domain Pruning (Permutations)**  
  * **Task:** Write functions to remove values from domains based on row and column uniqueness (the permutation rule).  
  * **Debug:** If a row already contains '1' and '2', verify that '1' and '2' are removed from the domains of all other empty cells in that row.  
  * **Checklist:** Can your code automatically identify "naked singles" (cells with only one possible value)?  
* **Day 5: Inequality Propagation**  
  * **Task:** Implement logic for \< and \> constraints. For example, if cell A \< cell B, then A's domain cannot contain N, and B's domain cannot contain 1\.  
  * **Debug:** Use a small 2x1 grid with a \< sign. If A and B both start with domains \[1, 2, 3\], after propagation, A should be \[1, 2\] and B should be \[2, 3\].  
  * **Checklist:** Do horizontal and vertical inequality signs correctly shrink the domains of adjacent cells?  
* **Day 6: The Forward Chaining Loop**  
  * **Task:** Implement the exhaustive Modus Ponens loop. Keep propagating changes until no more domains can be shrunk.  
  * **Debug:** To avoid infinite loops, ensure the algorithm tracks if any change occurred during a full pass of the grid.  
  * **Checklist:** Does the loop terminate correctly when the grid is solved or no more inferences can be made?  
* **Day 7: Contradiction & Integration**  
  * **Task:** Add a "fail-fast" check: if any cell's domain becomes empty, return an "Inconsistent" signal. Create a clean API for the other team members to use.  
  * **Debug:** Pass an impossible puzzle (e.g., two identical clues in one row) and ensure it detects the contradiction immediately.  
  * **Checklist:** Does the solver successfully solve a simple 4x4 puzzle using logic alone?

  ---

  ### **Phase 3: Heuristics & Performance (Days 8–11)**

**Objective:** Make the search efficient and collect data for the report.

* **Day 8: Heuristic Design**  
  * **Task:** Design the heuristic function h(s). A common choice is **Minimum Remaining Values (MRV)**—selecting the cell with the smallest domain size.  
  * **Debug:** Manually calculate the heuristic value for a partial grid and ensure your code returns the exact same number.  
  * **Checklist:** Is the heuristic function returning a valid numerical value for any partial state?  
* **Day 9: Admissibility Proof**  
  * **Task:** Draft the report section proving that your h(s) is **admissible** (it never overestimates the cost to the goal).  
  * **Debug:** If using "number of empty cells," verify it is a lower bound on the remaining assignments needed.  
  * **Checklist:** Is the logical argument for admissibility clear and ready for the final PDF?  
* **Day 10: Performance Logger**  
  * **Task:** Add code to track execution time, memory usage, and the number of node expansions/inferences.  
  * **Debug:** Ensure the expansion count increases every time the solver makes a choice or branches.  
  * **Checklist:** Are all metrics being captured for both Forward Chaining and A\* search?  
* **Day 11: The Big Run**  
  * **Task:** Run your solvers on all 10 test cases.  
  * **Debug:** If a 9x9 grid takes too long (e.g., over 5 minutes), look for redundant domain checks in your propagation logic.  
  * **Checklist:** Do you have a complete set of raw data for all input sizes?

  ---

  ### **Phase 4: Analytics & Final Polish (Days 12–15)**

**Objective:** Turn raw data into a high-scoring report.

* **Day 12: Chart Generation**  
  * **Task:** Create professional charts comparing execution time vs. grid size and expansion counts vs. algorithm type.  
  * **Debug:** Ensure all Y-axis units are consistent (e.g., all times in seconds or milliseconds).  
  * **Checklist:** Are the charts clear, labeled, and high-resolution for the PDF?  
* **Day 13: Comparative Analysis**  
  * **Task:** Write the "Experiment Results" section. Discuss which algorithm performed best and why.  
  * **Debug:** Use your data to back up claims (e.g., "A\* reduced node expansions by 40% compared to backtracking on 9x9 grids").  
  * **Checklist:** Does the analysis directly reference the tables and charts created on Day 12?  
* **Day 14: Final Code Integration**  
  * **Task:** Clean up the main.py and ensure the output format matches the requirement (printing the solved grid with signs).  
  * **Debug:** Run the full pipeline once: python main.py input-01.txt and check the saved output-01.txt.  
  * **Checklist:** Is the README.md clear enough for a lab instructor to run your code?  
* **Day 15: Final Review**  
  * **Task:** Self-evaluate the project against the Assessment Criteria table. Assemble the final compressed file (.zip or .rar).  
  * **Debug:** Double-check that all student IDs are in the filename as required.  
  * **Checklist:** Is the report PDF complete and the demo video URLs included? 

# DKhai

### **Phase 1 Logic Formalization (Days 1 to 3\)**

**Objective** Define the rules of the grid for the solver.

* **Day 1 FOL Axiom Drafting**  
  * **Task** Write the complete list of closed FOL sentences for Futoshiki. Include cell uniqueness (one value per cell), row/column permutations, and vertical inequality constraints .  
  * **Debug** Check for index errors (i, j) to ensure coordinates stay within the range of 1 to N.  
  * **Checklist** Do you have a formal sentence for every rule mentioned in section 2.1? .  
* **Day 2 Step by Step CNF Derivation**  
  * **Task** Select three non-trivial axioms (such as Row Uniqueness or Vertical Inequality) and convert them to Conjunctive Normal Form (CNF).  
  * **Process** Show each step: Eliminate implications, move negations inward, Skolemize, drop universal quantifiers, and distribute OR over AND.  
  * **Debug** Ensure no existential quantifiers (exists) remain after Skolemization.  
  * **Checklist** Are the derivations clear enough for the report requirements?.  
* **Day 3 Grounding Strategy**  
  * **Task** Assist THai in designing the Automatic KB Generation. Define how to ground the FOL axioms into propositional logic for a specific N.  
  * **Checklist** Can you explain how a universal quantifier turns into a specific list of atoms for a 4x4 grid?.  
    ---

    ### **Phase 2 The Backward Chaining Engine (Days 4 to 7\)**

**Objective** Create the Prolog-style query system.

* **Day 4 Rule Base Setup**  
  * **Task** Convert your FOL axioms into a Python-friendly Horn Clause format that the interpreter can traverse.  
  * **Debug** Ensure rules do not cause circular logic loops where A depends on B and B depends on A.  
  * **Checklist** Is your rule base ready for the recursive interpreter?  
* **Day 5 SLD Resolution Logic**  
  * **Task** Implement the recursive depth-first backward chaining algorithm from scratch.  
  * **Debug** Add a trace print statement to see the recursion depth: "Searching for Val(1,1,2)... checking Row 1... checking Column 1..."  
  * **Checklist** Does the algorithm return True or False for a specific cell value assignment?.  
* **Day 6 Variable Substitution**  
  * **Task** Enable the system to solve for variables, such as querying Val(1, 2, ?) and having it return the correct digit.  
  * **Debug** Test on a small 3x3 grid to ensure the recursion does not hit a Maximum Recursion Depth error.  
  * **Checklist** Can you query an individual cell and get a valid answer?.  
* **Day 7 Performance Baseline**  
  * **Task** Run Backward Chaining on simple test cases and record how long it takes to solve a cell vs. the whole grid.  
  * **Checklist** Is the logic correct for both horizontal and vertical inequality signs?.  
    ---

    ### **Phase 3 The A\* Search Solver (Days 8 to 11\)**

**Objective** Build the most advanced solver in the project.

* **Day 8 State Space and Priority Queue**  
  * **Task** Define the Node for A\* search (a partial assignment state) and set up the Priority Queue.  
  * **Debug** Ensure the queue sorts by the total cost f(s) equals g(s) plus h(s).  
  * **Checklist** Does the search always expand the node with the lowest f(s) first?  
* **Day 9 Integrating the Heuristic**  
  * **Task** Plug the admissible heuristic h(s) designed by MTri into the A\* loop.  
  * **Debug** If A\* is slower than backtracking, optimize the heuristic calculation code.  
  * **Checklist** Does A\* find a valid solution for the 4x4 example provided in the PDF?.  
* **Day 10 Pruning and Optimizations**  
  * **Task** Implement pruning: if a partial assignment violates an FOL axiom, discard that branch immediately.  
  * **Debug** Verify that you are not accidentally pruning valid solutions.  
  * **Checklist** Does the solver stop as soon as it finds the first valid solution?  
* **Day 11 Scalability Testing**  
  * **Task** Attempt the 7x7 and 9x9 puzzles.  
  * **Debug** Use a profiler to find bottlenecks in the A\* loop during large grid searches.  
  * **Checklist** Record the node expansion count for every test case for the final report.  
    ---

    ### **Phase 4 Video and Final Reporting (Days 12 to 15\)**

**Objective** Document the work and prove the algorithm power.

* **Day 12 Video Recording Part 1**  
  * **Task** Record the demonstration of Backward Chaining and A\*. Start from the command line and show the input file .  
  * **Checklist** Did you explain key steps like nodes being expanded by A\*?.  
* **Day 13 Video Recording Part 2**  
  * **Task** Upload the video to YouTube or Google Drive and ensure the link is public.  
  * **Checklist** Does the link work in a private/incognito browser window?.  
* **Day 14 Heuristic Analysis**  
  * **Task** Write the section of the report that proves or argues for the admissibility of the A\* heuristic.  
  * **Checklist** Is the argument rigorous enough for the 10 percent score?.  
* **Day 15 Final Review**  
  * **Task** Review the Inference algorithm descriptions section of the report.  
  * **Checklist** Are the pseudocode and descriptions for both solvers included?.

# THai

### **Phase 1: Infrastructure and Baselines (Days 1 to 3\)**

**Objective:** Build the background knowledge base and the simplest solvers for comparison.

* **Day 1: Knowledge Base Generation Part 1**  
  * **Task:** Write a function that takes the grid size N as input and generates a list of all possible Cell coordinates (i, j) and possible Values (v).  
  * **Debug:** Print the list for N=3; you should see 9 cells and 3 possible values per cell.  
  * **Checklist:** Does the function generate the correct number of combinations for any given N?.  
* **Day 2: Knowledge Base Generation Part 2**  
  * **Task:** Create the logic to "ground" the rules. For a 4x4 grid, generate all specific permutation facts for Row 1, Row 2, etc .  
  * **Debug:** Ensure that for a 4x4 grid, you do not accidentally generate a value of 5\.  
  * **Checklist:** Does the KB generation correctly reflect the permutation rules for both rows and columns? .  
* **Day 3: Brute Force Solver**  
  * **Task:** Implement a simple Brute Force solver that tries every number in every cell to serve as a baseline.  
  * **Debug:** Test on a 3x3 grid; it will be slow, but it must find the correct answer eventually.  
  * **Checklist:** Does the brute force solver find a valid solution for very small grid sizes?

---

### **Phase 2: Backtracking and Integration (Days 4 to 7\)**

**Objective:** Improve the baseline and prepare the main project directory structure.

* **Day 4: Backtracking Solver**  
  * **Task:** Implement a standard Backtracking algorithm (Recursive Depth-First Search).  
  * **Debug:** Add a counter to track "backtracks"; if it remains 0 on a hard puzzle, your constraint checking is likely skipped.  
  * **Checklist:** Is the backtracking solver significantly faster than the brute force baseline?  
* **Day 5: Output Formatter**  
  * **Task:** Write the function to save the solved grid to output-XX.txt, ensuring original inequality signs are kept for readability .  
  * **Debug:** Compare your generated file against the example output format provided in the project brief .  
  * **Checklist:** Does the output file look exactly like the requirement specified in section 3.2? .  
* **Day 6: Main Controller (main.py)**  
  * **Task:** Create the main.py script that accepts command line arguments to choose the input file and the algorithm.  
  * **Debug:** Use sys.argv to handle the input file path and the algorithm choice (e.g., \--algo forward\_chaining).  
  * **Checklist:** Can you run python main.py input-01.txt \--algo backtracking from the terminal?  
* **Day 7: Integration Testing**  
  * **Task:** Combine MTri's Forward Chaining logic with your Backtracking framework.  
  * **Checklist:** Does the integrated solver pass the first 3 test cases correctly?

---

### **Phase 3: GUI and Final Polish (Days 8 to 11\)**

**Objective:** Earn the 10% bonus and finalize the submission package.

* **Day 8: GUI Design (Bonus)**  
  * **Task:** Use a library like Tkinter or Pygame to create a simple window that displays the Futoshiki grid.  
  * **Debug:** Ensure the window scaling adjusts correctly if the grid is 4x4 versus 9x9.  
  * **Checklist:** Can you display the initial puzzle clues and inequality signs on the screen?.  
* **Day 9: GUI Logic**  
  * **Task:** Make the GUI update in real-time as the algorithm attempts to solve the puzzle.  
  * **Debug:** Use a "delay" or "step" function so the user can actually see the numbers changing.  
  * **Checklist:** Does the GUI accurately show the final solved state?.  
* **Day 10: Requirements and README**  
  * **Task:** Create the requirements.txt file and a README.md explaining how to run the source code .  
  * **Debug:** Try installing your requirements in a fresh virtual environment to ensure no dependencies are missing.  
  * **Checklist:** Is the README.md clear enough for a lab instructor to follow?.  
* **Day 11: Bug Squashing**  
  * **Task:** Assist MTri and DKhai in fixing performance bottlenecks on the large 9x9 test cases.  
  * **Checklist:** Do all 10 test cases run and solve correctly without errors?.

---

### **Phase 4: Final Report and Packaging (Days 12 to 15\)**

**Objective:** Finalize all documentation for the 25% report grade.

* **Day 12: Self-Evaluation**  
  * **Task:** Fill out the self-evaluation section of the report against all project criteria.  
  * **Checklist:** Did you check every box in the Assessment table?.  
* **Day 13: Task Distribution Documentation**  
  * **Task:** Document the responsibilities and completion percentages for MTri, DKhai, and THai .  
  * **Checklist:** Are the percentages fair, accurate, and agreed upon by the whole team?.  
* **Day 14: Final Report Assembly**  
  * **Task:** Gather algorithm descriptions, charts from MTri, and logic derivations from DKhai into a single PDF .  
  * **Checklist:** Are the public URLs for the demo videos included in the report?.  
* **Day 15: Packaging and Submission**  
  * **Task:** Organize the folder structure: Source, Inputs, Outputs, and the final Report .  
  * **Debug:** Ensure the final compressed file name follows the required StudentID format.  
  * **Checklist:** Is the final zip file under 20MB? If not, host it on Google Drive.