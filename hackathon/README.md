# 🤖 PICT Knight Shift — Campus Chess Bot Derby ♟️⚡

Welcome to PICT's first **Agentic Chess Bot Arena**! 

The challenge: Build, prompt, or tune a lightweight Python chess bot to battle other students' bots in an automated round-robin tournament.

---

## 📜 The Rules (Simple & Fast)

1. **AI Agents / Vibe Coding are 100% Allowed:**
   Use Cursor, Claude, ChatGPT, Antigravity, or code it yourself from scratch. The real skill is **prompting, heuristic tuning, and optimization within constraints.**
2. **Runtime Constraints:**
   - **Environment:** Pure Python 3 using `python-chess`.
   - **Time Limit:** **1.0 second max per move**. If your bot hangs or exceeds 1.0s, it forfeits the match!
   - **No External Engines:** No calling Stockfish binaries or web APIs during the match. All logic must live inside your file.
3. **Format:**
   - A single Python file named: `<your_name>_bot.py` (e.g., `rohan_bot.py`).
   - Must define this exact function:
     ```python
     import chess

     def get_move(board: chess.Board, time_limit: float = 1.0) -> chess.Move:
         # Your bot logic / evaluation here
         return best_move
     ```

---

## 🚀 Quick Start (In 3 Minutes)

### 1. Install Requirements
```bash
pip install python-chess
```

### 2. Test Your Bot Locally
We provided two baseline bots for you to practice against:
- `random_bot.py` (Plays random moves)
- `aggressive_bot.py` (Greedy bot that aggressively hunts captures and checks)

Run a local 1v1 match on your terminal:
```bash
python3 test_local.py bot_template.py random_bot.py --games 2
```

Play against the aggressive bot with move logs:
```bash
python3 test_local.py bot_template.py aggressive_bot.py --games 2 --verbose
```

---

## 🧠 Pro-Tips for Tuning Your Bot (Vibe-Coding Prompts)

If you're using an AI agent (Cursor, Claude, ChatGPT), try prompting it with these ideas to crush the competition:
- *"Add Piece-Square Tables (PST) to evaluate piece placement (e.g. Knights in center, Pawns advanced, King castled safe)."*
- *"Implement Move Ordering: evaluate captures and checks first to trigger faster Alpha-Beta cutoffs."*
- *"Add an endgame detector: when Queens are traded, encourage the King to activate towards the center."*
- *"Make the minimax depth adaptive so it never exceeds 0.8 seconds per move."*

---

## 🏆 Submission & Tournament Day

1. **Submit:** Drop your `<yourname>_bot.py` file in the club Google Form or DM it to the admin before the deadline.
2. **The Arena:** We load all bots into `arena_runner.py` and run a full automated round-robin tournament.
3. **The Honors:**
   - 🥇 **Campus Grandmaster** (1st Place)
   - ⚡ **Executioner Award** (Most brutal checkmates)
   - 🏎️ **Speed Demon** (Fastest calculation time)

Good luck, and may the best prompt win! 👑
