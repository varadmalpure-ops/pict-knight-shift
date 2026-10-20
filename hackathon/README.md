# 🤖 PICT Knight Shift — Campus Chess Bot Derby ♟️⚡

Welcome to PICT's premier **Agentic Chess Bot Arena**! 

The challenge: Build, prompt, or tune a lightweight Python chess bot to battle other students' bots in an automated campus tournament and defense gauntlet.

---

## 📜 Key Tournament Information

- **Rulebook:** Read the comprehensive rules in [`RULES.md`](file:///Users/varadmalpure/foo/PICT%20Knight%20Shift/hackathon/RULES.md).
- **Audit & Engineering Changelog:** [`CHANGELOG.md`](file:///Users/varadmalpure/foo/PICT%20Knight%20Shift/CHANGELOG.md).

---

## ⚖️ The 4 Core Principles

1. **AI Agents / Vibe Coding are 100% Legal & Encouraged:**  
   Use Cursor, Claude 3.5 Sonnet, ChatGPT, Antigravity, or write pure Python by hand. The real skill is **prompt engineering, algorithmic critique, heuristic weighting, and empirical A/B benchmarking.**
2. **Runtime Constraints:**  
   - **Environment:** Pure Python 3 (`python-chess`).
   - **File Size:** Single file `<your_name>_bot.py` $\le$ **25 KB**.
   - **Time Budget:** 0.25 seconds per move (soft target: 0.18s, hard OS timeout: 0.35s).
   - **Memory Limit:** 256 MB per bot process.
   - **No Hardcoded Opening Books:** Embedded lookup tables banned; moves must be dynamically searched.
   - **No External Engines or Network:** Strictly offline execution.
3. **Persistent Process Architecture:**  
   Your bot process persists across moves within a match, meaning your Transposition Table (TT) and history heuristics retain state throughout the game.
4. **100% Automated Scoring (Zero Manual Grading, No Viva):**
   - 🏆 **70% Main Tournament Arena** (Swiss & Double Round-Robin with eval-balanced paired openings)
   - 🧩 **20% Hidden Challenge Suite** (Chess960, material odds, endgames, variable time controls)
   - ⚔️ **10% Calibrated Reference Gauntlet** (~1000, ~1500, ~2000 Elo tiers)

---

## 🚀 Quick Start (In 3 Minutes)

### 1. Install Requirements
```bash
pip install python-chess
```

### 2. Verify Security Compliance
```bash
python3 compliance_check.py hackathon/bot_template.py
```

### 3. Test Your Bot Locally
Run a 2-game paired match against the baseline bots:
```bash
python3 hackathon/arena_runner.py hackathon/bot_template.py hackathon/aggressive_bot.py --games 2
```

Play a local test with move-by-move terminal output:
```bash
python3 hackathon/test_local.py hackathon/bot_template.py hackathon/aggressive_bot.py --games 2 --verbose
```

---

## 🧠 Pro-Tips for Reaching ~2000 Elo Play

Generic AI code typically plateaus at **~1500 Elo**. To reach the expert tier (~2000 Elo) and compete for **The Giant Slayer** award:
- **Iterative Deepening & Time Abort:** Search depth 1, 2, 3... and abort cleanly when budget reaches ~0.75s, returning the best move from the last completed depth.
- **Move Ordering:** Evaluate hash moves first, then MVV-LVA (Most Valuable Victim - Least Valuable Attacker) captures, killer moves, and history heuristic.
- **Quiescence Search:** Search captures and promotions until the board is quiet to eliminate tactical horizon blunders.
- **Transposition Table:** Key board positions with Zobrist hashes (`chess.polyglot.zobrist_hash(board)`) to reuse previously searched subtrees.
- **Tapered PeSTO Evaluation:** Interpolate between middlegame and endgame piece-square tables to balance king safety early with king centralization in the endgame.
- **Mop-Up Endgame Vectoring:** In winning endgames, drive the opposing king toward board edges and corners to convert checkmates quickly.

---

## 🏆 Honors & Awards

- 👑 **The Campus Grandmaster:** Overall 1st Place champion across the 100-point matrix.
- ⚔️ **The Giant Slayer:** Highest points scored against the ~2000 Elo reference benchmark engine.
- 🛡️ **The Iron Bastion:** Lowest blunder/timeout forfeit rate under high-stress time controls and adversarial positions.
- ⚡ **Tactical Maestro Award:** Highest score on the Hidden Challenge Suite (Chess960 & complex puzzles).

---

## 📥 Submission Links

1. **Submit Bot File:** 👉 **[Official Google Form](https://forms.gle/4vuAAeGVSjJ5JzFV6)**
2. **Weekly Leaderboard Updates:** Every Sunday night at 9:00 PM.
3. **Hard Deadline:** **Diwali Eve (Saturday, November 7, 2026 @ 11:59 PM)**.
