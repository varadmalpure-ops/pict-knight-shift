# PICT KNIGHT SHIFT // 3-MINUTE ORAL VIVA & CODE DEFENSE RUBRIC
> **Format:** 3-Minute Live Interactive Code Defense before a 2-judge panel.  
> **Weightage:** 10% of total hackathon score (paired with 10% Design Dossier = 20% total).  
> **Scoring Scale:** 5 Core Criteria &times; 0–4 Points = **20 Points Maximum**.

---

## Evaluation Grid

| Score | Performance Band | Description |
| :---: | :--- | :--- |
| **0** | **Non-Functional / Fraudulent** | Cannot explain code structure; copied uninspected LLM output; freezes or crashes on basic questions. |
| **1** | **Surface-Level / Memorized** | Recites textbook definitions without understanding implementation; cannot explain failure modes. |
| **2** | **Competent Implementation** | Understands standard algorithms (alpha-beta, MVV-LVA); can explain code mechanics but lacks deep calibration insight. |
| **3** | **Strong Engineering Mastery** | Conceived clear design hypotheses; identified and fixed AI blunders; rigorously benchmarked tradeoffs. |
| **4** | **Exceptional Systems Insight** | Masterful command of Python performance limits, tree pruning nuances, adversarial edge cases, and algorithmic tradeoffs. |

---

## Detailed Criteria & Scoring Anchors

### Criterion 1: Search Dynamics & Pruning Depth (Max 4 Points)
*Assesses understanding of tree search, iterative deepening, time budgeting, and cutoff mechanics.*

- **0 Points:** Cannot explain minimax or alpha-beta; doesn't know what pruning does or why tree search is necessary.
- **1 Point:** Recites abstract definition of alpha-beta, but cannot explain how $\alpha$ and $\beta$ bounds update or how time aborts are triggered.
- **2 Points:** Clearly explains negamax and basic alpha-beta pruning. Understands how iterative deepening allows progressive move returns.
- **3 Points:** Explains move ordering mechanics (hash move first, MVV-LVA, killer moves), quiescence search for tactical stabilization, and why check evasions cannot be pruned.
- **4 Points (Mastery):** Explains transposition table cutoff types (EXACT, LOWERBOUND, UPPERBOUND), Zobrist collision mitigations, quiescence delta pruning, and check extension dynamics. Accurately predicts search behavior under extreme branch pruning.

---

### Criterion 2: Evaluation Function Design & Calibrated Tradeoffs (Max 4 Points)
*Assesses understanding of evaluation terms, positional vs. tactical balance, and computational efficiency.*

- **0 Points:** Copied arbitrary tables from the web without knowing unit values (centipawns) or what values represent.
- **1 Point:** Knows piece values (1, 3, 3, 5, 9) but cannot explain positional tables or why Python evaluation speed constrains complexity.
- **2 Points:** Explains piece-square tables and simple positional terms (passed pawns, mobility, king position).
- **3 Points:** Explains tapered evaluation (smooth interpolation between middlegame and endgame phase scores), king safety vs. king centralization tradeoffs, and computational cost vs. depth tradeoffs.
- **4 Points (Mastery):** Deep architectural insight: Quantifies nodes-per-second (NPS) impact of each eval term, explains endgame mop-up vectoring, draw detection avoidance (stalemate/repetition), and variant generalization (Chess960).

---

### Criterion 3: Scientific Rigor & Empirical Testing (Max 4 Points)
*Assesses the student's experimental methodology, A/B testing discipline, and evidence-driven development.*

- **0 Points:** No recorded test data; claims Elo improvements based on intuition or fewer than 5 casual games.
- **1 Point:** Tested only against random bots or played anecdotal games without statistical controls.
- **2 Points:** Conducted self-play games (30–50 games), but biased by fixed colors or lack of standardized opening positions.
- **3 Points:** Conducted controlled A/B testing with balanced paired openings (minimum 50–100 games), tracking Win/Draw/Loss and error margins. Made keep/revert decisions based on data.
- **4 Points (Mastery):** Flawless scientific methodology: Statistically significant A/B test logs, ablation studies isolating individual heuristics, seed variance control, and regression avoidance.

---

### Criterion 4: Code Attribution & Original Engineering vs. Raw LLM Output (Max 4 Points)
*Assesses whether the participant was an active software architect or a passive consumer of AI output.*

- **0 Points:** 100% uninspected LLM dump; cannot explain variable names, control flow, or design decisions.
- **1 Point:** Minor prompt modifications; heavily relies on raw LLM output and struggles when asked why specific structures were chosen.
- **2 Points:** Understands the LLM code and can navigate it, but made few independent architectural alterations.
- **3 Points:** Demonstrates critical critique of AI output: identified AI blunders (e.g., inefficient per-node allocations, broken check evasions, unhandled draws), refactored bottlenecks, and implemented custom logic.
- **4 Points (Mastery):** Exemplary engineering partnership: Used AI purely as a high-velocity drafting assistant; conceived original hypotheses, rejected flawed LLM suggestions with benchmarked proof, and authored custom algorithmic optimizations.

---

### Criterion 5: Live Debugging & Adversarial Edge Case Handling (Max 4 Points)
*Assesses poise, problem-solving ability, and resilience when presented with an unexpected or adversarial scenario.*

- **0 Points:** Freezes or crashes when presented with an edge-case board state (Chess960, stalemate trap, underpromotion).
- **1 Point:** Recognizes problem only after it crashes or hangs.
- **2 Points:** Diagnoses edge case with guidance from judges, but struggles to propose an efficient fix.
- **3 Points:** Confidently diagnoses tactical traps, repetition loops, or variant edge cases; explains exact algorithmic cause within 60 seconds.
- **4 Points (Mastery):** Instant live mastery: Immediately identifies root cause, walks through search tree traversal, explains exact state pruning or evaluation failure, and dictates precise fix adhering to CPU budget.

---

## Score Summary Sheet (Judge Panel)

| Criterion | Max | Score | Notes & Specific Questions Asked |
| :--- | :---: | :---: | :--- |
| **1. Search Dynamics & Pruning Depth** | 4 | | |
| **2. Evaluation & Calibrated Tradeoffs** | 4 | | |
| **3. Scientific Rigor & Empirical Testing** | 4 | | |
| **4. Code Attribution vs. LLM Critique** | 4 | | |
| **5. Live Debugging & Edge Cases** | 4 | | |
| **TOTAL SCORE** | **20** | | |

**Judge 1 Signature:** ___________________________ &nbsp;&nbsp;&nbsp;&nbsp; **Judge 2 Signature:** ___________________________
