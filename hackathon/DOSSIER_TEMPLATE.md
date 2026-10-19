# PICT KNIGHT SHIFT // ENGINEERING DESIGN DOSSIER
> **Format Requirement:** Must fit strictly on **ONE PAGE** (Markdown or single-sheet PDF printout).  
> **Weightage:** 10% of total hackathon score (paired with 10% Oral Viva Defense = 20% total).  
> **Participant Name:** [Your Name / Team Name]  
> **Bot File:** `[yourname]_bot.py` | **File Size:** `[e.g., 28.4 KB]` | **Final Benchmark NPS:** `[e.g., 2,800 nodes/sec]`

---

### 1. Bot Architecture & Original Engineering Hypothesis
*State your core design thesis in 2–3 sentences. What makes your engine competitively distinct? Why did you prioritize specific search/eval tradeoffs given Python's speed constraints?*

> **Hypothesis:** ______________________________________________________________________________________  
> ____________________________________________________________________________________________________

---

### 2. Human vs. AI Engineering Audit
*AI coding assistants (Claude, Cursor, Copilot, ChatGPT) are 100% permitted. However, raw LLM chess code is notoriously bug-prone and slow. Document where you exercised critical human engineering over raw AI output.*

| Component | What the AI Initially Suggested | Why It Failed / Was Inadequate | Human Architectural Adaptation |
| :--- | :--- | :--- | :--- |
| **Search Tree** | *e.g., Minimax with `copy.deepcopy` & recursion* | *Burns 20ms/node; hits Python recursion limit* | *Flattened loops, in-place `push/pop`, bitwise ops* |
| **Move Ordering** | *e.g., Full sorting of all legal moves* | *High overhead per node; slows search depth* | *MVV-LVA for captures + killer heuristic array* |
| **Evaluation** | *e.g., Expensive mobility calculation per node* | *Dropped depth from 5 plies to 2 plies* | *PeSTO piece-square tables + phase interpolation* |
| **Endgames** | *e.g., Standard material eval only* | *Stalemate blunders and endless king shuffles* | *Mop-up king vectoring (driving king to corner)* |

---

### 3. Empirical Experimentation Log (A/B Ablation Testing)
*Log at least 3 controlled experiments conducted during development. Every feature in your bot must justify its inclusion with empirical data over balanced paired games.*

| # | Hypothesis Tested | Code Change Applied | Match Setup (Min 50 games) | Win / Draw / Loss | Result & Decision |
| :-: | :--- | :--- | :--- | :-: | :--- |
| **Exp 1** | *Transposition table will increase search depth by 1 ply* | *Added 256K-entry Zobrist TT cache* | *50 games vs v0.1 (balanced openings)* | `34 - 10 - 6` | **KEPT** (+1.2 plies avg depth) |
| **Exp 2** | *Mobility eval term improves positional grip* | *Added legal move count to eval* | *50 games vs v0.2* | `14 - 12 - 24` | **REVERTED** (Cost 45% NPS) |
| **Exp 3** | *Quiescence delta pruning eliminates horizon blunders* | *Added 900cp margin cutoff in Q-search* | *60 games vs v0.3* | `41 - 14 - 5` | **KEPT** (Zero tactical blunders) |

---

### 4. Technical Benchmark & Performance Profile

- **Average Search Depth:** Middlegame: `[ e.g., 4–5 plies ]` | Endgame: `[ e.g., 6–8 plies ]`
- **Time Management Safety Margin:** Targets `0.75s` per move; hard abort trigger at `0.85s` (guarantees zero forfeit risk under the 1.0s limit).
- **Variant & Stress Readiness:** Verified legal execution on Chess960, material odds, and 0.2s ultra-bullet time controls.
- **Top Known Vulnerability / Limitation:** ___________________________________________________________

---

### 5. Signature & Defense Pledge
*I hereby verify that all benchmark data recorded above represents actual empirical games played, and I am prepared to explain, modify, and defend every line of code during the live 3-minute oral viva.*

**Signature:** ___________________________ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; **Date:** _______________
