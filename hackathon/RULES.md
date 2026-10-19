# 📜 PICT KNIGHT SHIFT // OFFICIAL BOT DERBY RULEBOOK ♟️⚡
### *Campus Chess Bot Hackathon (Diwali Season Edition)*

---

## 🎯 1. Objective
Design, prompt, or code a standalone Python chess bot to compete in an automated campus-wide round-robin tournament against other students' bots.

---

## 🤖 2. The AI & Vibe-Coding Policy
* **100% Legal & Encouraged:** You are fully allowed to use AI coding agents (Cursor, Claude, ChatGPT, Antigravity, GitHub Copilot) or code from scratch.
* **The Real Skill:** Prompt engineering, heuristic weighting, minimax depth optimization, and time-budget management within strict constraints.

---

## 🛠️ 3. Technical Constraints & Submission Specifications

| Parameter | Specification | Penalty / Action |
|:---|:---|:---|
| **Format** | Single Python file: `<your_name>_bot.py` | Rejected if not `.py` |
| **Max File Size** | **150 KB** | Auto-disqualified by AST scanner |
| **Required Interface** | Must implement `get_move(board: chess.Board, time_limit: float = 1.0) -> chess.Move` | Game forfeited if missing |
| **Max Time per Move** | **1.0 second** (Hard deadline enforced by OS subprocess) | Match forfeited on timeout |
| **Allowed Libraries** | `chess`, `chess.polyglot`, `math`, `random`, `time`, `copy`, `collections`, `itertools`, `functools`, `typing`, `dataclasses`, `enum` | Auto-disqualified if unlisted module imported |
| **Network Access** | **Strictly Offline** (0 KB bandwidth) | Network imports blocked by AST scanner |

---

## 🚫 4. Disqualification & Fair Play Criteria (Automated Scanner)

Every submission undergoes an automated static AST (Abstract Syntax Tree) security check before running. A bot is **instantly disqualified** if it contains:

1. **External Chess Engines / UCI Wrappers:** Any import of `chess.engine` or use of Stockfish/Komodo/Leela binaries.
2. **System & Shell Calls:** Use of `subprocess`, `os.system`, `os.popen`, `ctypes`, or `shutil`.
3. **Network APIs:** Use of `urllib`, `requests`, `socket`, `http` to fetch moves online.
4. **Dynamic Code Execution:** Calling `eval()`, `exec()`, `compile()`, or `open()`.
5. **Infinite Loops & Memory Hangs:** Any move taking longer than `1.25s` will be forcibly terminated by the process manager, and the opponent will receive a forfeit win.

---

## ⚔️ 5. Tournament Format & Scoring

* **Structure:** Full Round-Robin. Every bot plays every other bot **twice** (once as White, once as Black).
* **Time Control:** 1.0 second per move, maximum 120 moves per game.
* **Scoring (Standard FIDE):**
  - **Win:** 1.0 point
  - **Draw:** 0.5 points
  - **Loss:** 0.0 points
* **Tie-Break Hierarchy:**
  1. Total Points
  2. Total Wins
  3. Total Checkmates Delivered
  4. Lowest Average Calculation Time per Move

---

## 📅 6. Timeline & Milestones (3-Week Schedule)

* **Kickoff:** Monday, 19th October
* **Week 1 Provisional Run:** Sunday, 25th October @ 9:00 PM *(Early-bird leaderboard)*
* **Week 2 Provisional Run:** Sunday, 1st November @ 9:00 PM *(Version 2.0 leaderboard)*
* **Final Submissions Close:** Diwali Eve *(Submissions locked)*
* **Grand Finale & Awards:** Full round-robin execution & campus titles awarded!

> 💡 **Pro-Tip:** **Unlimited resubmissions are allowed!** You can submit early, see where your bot ranks on Sunday night, refine your heuristics, and submit an updated version.

---

## 🏆 7. Official Campus Honors & Awards

* 👑 **The Campus Grandmaster:** 1st Place overall in points.
* ⚡ **The Executioner Award:** Bot with the highest number of brutal checkmates.
* 🏎️ **The Speed Demon:** Fastest bot with an average calculation time under 10ms that maintains a positive win rate.
* 🛡️ **The Iron Bastion:** Bot that concedes the fewest checkmates across the entire tournament.

---

## 📥 8. Submission & Resources

* **Starter Kit & Local Testing:** [github.com/varadmalpure-ops/pict-knight-shift/tree/main/hackathon](https://github.com/varadmalpure-ops/pict-knight-shift/tree/main/hackathon)
* **Official Submission Form:** [forms.gle/4vuAAeGVSjJ5JzFV6](https://forms.gle/4vuAAeGVSjJ5JzFV6)
* **Campus Chess WhatsApp Community:** [chat.whatsapp.com/H3DDsOt2kl91HmhcXBozbj](https://chat.whatsapp.com/H3DDsOt2kl91HmhcXBozbj)
