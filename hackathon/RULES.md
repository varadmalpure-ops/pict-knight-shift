# 📜 PICT KNIGHT SHIFT // OFFICIAL BOT DERBY RULEBOOK ♟️⚡
### *Campus Chess Bot Hackathon — Engineering & Grand Finale Edition*

---

## 🎯 1. Mission & Philosophy
PICT Knight Shift is a campus-wide tournament and software engineering hackathon designed to reward **rigorous algorithmic thinking, scientific experimentation, and empirical performance engineering**.

You will design, prompt, iterate, and benchmark a standalone Python chess bot capable of competing under strict time, memory, and security constraints.

> 🤖 **The AI & Vibe-Coding Policy:**  
> AI coding agents (Cursor, Claude 3.5 Sonnet, Antigravity, ChatGPT, GitHub Copilot) are **100% legal, welcomed, and encouraged**.  
> However, raw LLM chess code is notoriously prone to shallow traps, timeout forfeits, and illegal move bugs. The winning teams will not be those who blindly copy LLM outputs, but those who **critique, profile, test, and iterate** their bot into an optimized competitive engine.

---

## 📅 2. Official Timeline & Milestones

| Event / Milestone | Date & Time | Notes |
| :--- | :--- | :--- |
| **Hackathon Kickoff** | Monday, October 19, 2026 | Starter kit released & submission form opens |
| **Provisional Leaderboard Run 1** | Sunday, October 25, 2026 @ 9:00 PM | Early-bird benchmark & baseline Swiss run |
| **Provisional Leaderboard Run 2** | Sunday, November 1, 2026 @ 9:00 PM | Mid-point tournament ladder update |
| **Final Submissions Close** | **Diwali Eve (Saturday, Nov 7, 2026 @ 11:59 PM)** | Submissions hard-locked; SHA-256 seed published |
| **Grand Finale & Oral Viva** | Sunday, November 8, 2026 | Live tournament stream, gauntlet run, viva defense |

*Unlimited resubmissions are permitted up until the Diwali Eve deadline!*

---

## 🛠️ 3. Submission Specifications & Constraints

Every submission must be submitted as a single Python file named `<your_name>_bot.py`.

```python
# Required Interface (Exact Signature)
import chess

def get_move(board: chess.Board, time_limit: float = 1.0) -> chess.Move:
    """
    Given a python-chess Board and a move time budget in seconds,
    return a legal chess.Move. Must NEVER return None or raise uncaught exceptions.
    """
    ...
```

### Constraints Checklist

| Specification | Limit | Action on Violation |
| :--- | :--- | :--- |
| **File Format** | Single `.py` source file (`<name>_bot.py`) | Disqualified if not valid Python |
| **File Size Cap** | Maximum **100 KB** | Disqualified by static AST scanner |
| **Move Time Budget** | Soft: `0.75s` | Hard cutoff: `1.25s` (process killed) | Current game forfeited on timeout |
| **Memory Limit** | Maximum **256 MB** per bot process | Process terminated on OOM |
| **Data Literals Cap** | Max **4 KB** single literal, **20 KB** cumulative | Disqualified (prevents giant embedded opening books) |
| **Network & Disk I/O** | **Zero I/O** (Fully offline execution) | Disqualified by security sandbox |
| **Process Model** | **Persistent Subprocess per Match** | Memory/Transposition tables persist across moves |

---

## 🔒 4. Security Sandbox & Banned Operations

To guarantee 100% fair play, reproducibility, and safety on host tournament hardware, every submission is audited by an automated AST (Abstract Syntax Tree) analyzer and executed inside a strict IPC sandbox.

### Allowed Imports Whitelist ONLY
```python
chess, chess.polyglot, math, random, time, copy,
collections, itertools, functools, typing, dataclasses, enum
```
*No other libraries may be imported. Third-party packages such as `numpy`, `scipy`, `torch`, etc., are strictly disallowed.*

### Strictly Banned Operations (Instant Disqualification)
1. **Engine UCI Wrappers & Stockfish:** Any use of `chess.engine`, external binaries, or UCI interfaces.
2. **System & Process Access:** `os`, `sys`, `subprocess`, `shutil`, `ctypes`, `threading`, `multiprocessing`.
3. **Network & Sockets:** `urllib`, `requests`, `socket`, `http`, `ftplib`.
4. **Dynamic Code Execution & File Access:** `eval()`, `exec()`, `compile()`, `open()`, `__import__()`.
5. **Dunder Reflection & Attribute Tricks:** Accessing `__class__`, `__base__`, `__subclasses__`, `__globals__`, `__builtins__`, or string-based `getattr()` / `setattr()`.
6. **Console Printing:** Any calling of `print()` inside move search (pollutes IPC buffers).

---

## 🏆 5. Aggregate 100-Point Scoring Breakdown

The champion is determined by a comprehensive **100-Point Evaluation Matrix** covering four competitive pillars:

```
┌────────────────────────────────────────────────────────────────────────┐
│                      PICT KNIGHT SHIFT SCORING MATRIX                   │
├───────────────────┬────────────────────────────────────────────────────┤
│ 1. Tournament     │ 50 Points (Swiss + Double Round-Robin Finals)      │
│ 2. Challenge Suite│ 20 Points (Hidden 18-Test Variant & Tactics Suite) │
│ 3. Ref Gauntlet   │ 10 Points (1000, 1500, 2000 Elo Reference Ladder)  │
│ 4. Dossier & Viva │ 20 Points (10% Design Dossier + 10% 3-Min Viva)    │
└───────────────────┴────────────────────────────────────────────────────┘
```

### 1. Main Tournament (50 Points)
- **Format:** Qualifying Swiss rounds leading into an 8-bot Double Round-Robin Final.
- **Fair Openings:** Matches are played in **eval-balanced pairs** (each pair of bots plays both White and Black from identical opening setups) to eliminate color bias.
- **Scoring:** Win = 1.0 pt, Draw = 0.5 pt, Loss = 0.0 pt.
- **Game Cap:** 120 full moves (240 plies). If neither side mates or claims a draw, games are adjudicated based on material delta ($\ge 3$ points).
- **Tie-Breaks:** Direct Head-to-Head &rarr; Sonneborn-Berger Score &rarr; Total Wins.

### 2. Hidden Challenge Suite (20 Points)
- An organizer-only evaluation suite generated from a secret commit-reveal SHA-256 seed.
- 18 standardized stress tests evaluating:
  - **Chess960 (Fischer Random):** Testing generic piece dynamics without hardcoded castling squares.
  - **Material Odds:** Evaluates play from asymmetric imbalances (missing knight, pawn storms).
  - **Endgame Conversion:** Autonomous conversion of KR vs K, KQ vs K, KP vs K oppositions.
  - **Tactical Deflections:** Mate-in-two patterns and tactical combinations.
  - **Variable Time Controls:** Flawless legal move execution under 0.2s, 1.0s, and 2.0s budgets.

### 3. Calibrated Reference Gauntlet (10 Points)
- Every bot runs through a 3-tier calibrated benchmark ladder:
  - **Tier 1 (~1000 Elo):** Novice human benchmark.
  - **Tier 2 (~1500 Elo):** Solid club player benchmark.
  - **Tier 3 (~2000 Elo):** Expert campus benchmark.
- Points are awarded proportionally to match score across tiers.

### 4. Design Dossier & Oral Viva Defense (20 Points)
- **One-Page Dossier (10 Points):** Submit a 1-page document using [`DOSSIER_TEMPLATE.md`](file:///Users/varadmalpure/foo/PICT%20Knight%20Shift/hackathon/DOSSIER_TEMPLATE.md) detailing your core hypothesis, AI adaptations, and empirical A/B experiment logs (min. 50 games per change).
- **3-Minute Live Viva (10 Points):** Present and defend your code before a panel of 2 judges evaluated on the 5 criteria in [`VIVA_RUBRIC.md`](file:///Users/varadmalpure/foo/PICT%20Knight%20Shift/hackathon/VIVA_RUBRIC.md).

---

## 🎖️ 6. Official Campus Honors & Awards

- 👑 **The Campus Grandmaster:** Awarded to the 1st Place overall finisher across the combined 100-point matrix.
- ⚔️ **The Giant Slayer:** Awarded to the bot that scores the highest points against the ~2000 Elo reference benchmark engine.
- 🛡️ **The Iron Bastion:** Awarded to the bot with the lowest blunder/timeout forfeit rate across the entire tournament and challenge suite.
- 🔬 **Engineering Excellence Award:** Awarded to the team with the highest combined score on the Design Dossier and Oral Viva defense.

---

## 🔍 7. Worked Examples: Legal vs. Illegal Bots

### ✅ Example A: A Fully Compliant Bot
```python
# alice_bot.py
import chess
import time
import random

# Fast piece values
PIECE_VALUES = {
    chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
    chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 20000
}

def evaluate_board(board: chess.Board) -> int:
    score = 0
    for sq, piece in board.piece_map().items():
        val = PIECE_VALUES[piece.piece_type]
        score += val if piece.color == chess.WHITE else -val
    return score if board.turn == chess.WHITE else -score

def get_move(board: chess.Board, time_limit: float = 1.0) -> chess.Move:
    search_board = board.copy()
    start_time = time.perf_counter()
    safe_deadline = start_time + min(time_limit * 0.75, 0.8)
    
    legal_moves = list(search_board.legal_moves)
    if not legal_moves:
        return chess.Move.null()
    
    best_move = legal_moves[0]
    
    try:
        # Simple 1-ply search with time check
        best_eval = -999999
        for move in legal_moves:
            if time.perf_counter() > safe_deadline:
                break
            search_board.push(move)
            try:
                score = -evaluate_board(search_board)
                if score > best_eval:
                    best_eval = score
                    best_move = move
            finally:
                search_board.pop()
    except Exception:
        # Failsafe fallback
        return random.choice(legal_moves)
        
    return best_move if best_move in board.legal_moves else random.choice(legal_moves)
```
*Why it passes:* Whitelisted imports only, zero dunders/reflection, wraps board manipulation in `try...finally: pop()`, honors time budget, and provides foolproof legal fallback.

---

### ❌ Example B: Disqualified Violations
```python
# cheater_bot.py
import chess
import numpy as np          # ❌ DISQUALIFIED: 'numpy' is not on whitelist
import subprocess           # ❌ DISQUALIFIED: System module banned
import chess.engine         # ❌ DISQUALIFIED: External engine wrapper banned

def get_move(board: chess.Board, time_limit: float = 1.0) -> chess.Move:
    # ❌ DISQUALIFIED: Dunder reflection bypass
    sub = ().__class__.__base__.__subclasses__()
    
    # ❌ DISQUALIFIED: File access / eval
    eval("open('secret.txt', 'w')")
    
    # ❌ DISQUALIFIED: print statement in move loop
    print("Thinking...")
    
    # ❌ DISQUALIFIED: No timeout protection (infinite sleep)
    time.sleep(2.0)
    
    return None             # ❌ DISQUALIFIED: Returned None
```

---

## ❓ 8. Frequently Asked Questions (FAQ)

**Q: Can I use Claude, Cursor, or ChatGPT to generate my bot?**  
A: **Yes!** You can use any AI model. However, you are personally responsible for the code. You will need to defend every algorithm, data structure, and heuristic during the live 3-minute oral viva.

**Q: Can I embed a large opening book or endgame table?**  
A: No giant books. To prevent bots from simply being wrappers around 5 MB text dumps, static constants are capped at **4 KB per literal** and **20 KB cumulative**. In addition, the tournament uses paired balanced openings, meaning standard book lines provide minimal advantage.

**Q: Does my bot restart every move, or does memory persist?**  
A: The tournament runner uses a **persistent subprocess** for each game. Your module remains in memory throughout the match, meaning your Transposition Table and history heuristics persist between moves. The process is cleanly recycled between different matches.

**Q: What happens if my bot raises an unhandled exception or times out?**  
A: If your bot throws an unhandled error, returns `None`, returns an illegal move, or exceeds 1.25s of wall time, the game is immediately forfeited as a loss. Always wrap your search in a `try...except` block with a random legal move fallback!

**Q: Can I hardcode standard castling moves like `e1g1`?**  
A: **No.** In Chess960 (which is part of the challenge suite and final rounds), king and rook starting squares vary. Always use the generic `board.legal_moves` or `board.has_kingside_castling_rights()` methods rather than hardcoded coordinate strings.

---

## 🚀 9. Getting Started & Verification

1. **Clone the repository:**
   ```bash
   git clone https://github.com/varadmalpure-ops/pict-knight-shift.git
   cd pict-knight-shift
   pip install chess
   ```
2. **Verify your bot against the AST scanner:**
   ```bash
   python3 compliance_check.py yourname_bot.py
   ```
3. **Run local simulation matches:**
   ```bash
   python3 hackathon/arena_runner.py yourname_bot.py hackathon/bot_template.py --games 2
   ```
4. **Submit your bot:**
   Submit your `<your_name>_bot.py` via the [Official Google Form](https://forms.gle/4vuAAeGVSjJ5JzFV6).
