# ♟️ PICT KNIGHT SHIFT ⚡
### *The Unofficial Chess & Tactical Calculation Hub of PICT Pune*

[![GitHub repo](https://img.shields.io/badge/PICT-Knight%20Shift-orange?style=for-the-badge&logo=chess.com)](https://www.chess.com/club/pict-knight-shift)
[![WhatsApp Community](https://img.shields.io/badge/Join-WhatsApp%20Community-25D366?style=for-the-badge&logo=whatsapp)](https://chat.whatsapp.com/H3DDsOt2kl91HmhcXBozbj)
[![Python-Chess](https://img.shields.io/badge/python--chess-1.11.2-blue?style=for-the-badge&logo=python)](https://python-chess.readthedocs.io/)
[![Campus](https://img.shields.io/badge/Campus-3%20Acres%2C%20Infinite%20Tactics-purple?style=for-the-badge)]()

---

> *"AI can vibe-code your project. ChatGPT can write your lab assignment. Cursor can fix your compiler errors.*  
> *But when your clock has 14 seconds left and someone is hunting your King — **no LLM on earth can save you.**"*

Welcome to **PICT Knight Shift** — where engineering logic meets blitz adrenaline. Whether you are an unrated beginner who only knows how the knight moves in an `L` shape, or an 1800-rated tryhard grinding bullet at 1:00 AM, this community and automated bot arena is built for you.

---

## 🏆 Current Featured Event: The Campus Chess Bot Derby 🤖
> **3-Week Diwali Season Sprint | Beginners, Coders & Vibe-Coders Welcome**  
> **Final Submissions Close:** Diwali Eve (Saturday, November 7, 2026 @ 11:59 PM IST)

Think you know how to prompt AI agents, optimize algorithms, and tune heuristics? Put your code to the test in an automated campus battle.

* 🛠️ **Rules:** Single Python file (`<your_name>_bot.py`), **10 KB max file size**, **0.20s max per move** (with progressive time squeezes to 0.10s super-bullet in playoffs), pure `python-chess`.
* 🤖 **AI Policy:** **100% Legal & Encouraged.** Use Cursor, Claude, ChatGPT, Antigravity, or your own bare hands. The winning edge lies in heuristic weighting, quiescence search, and empirical A/B benchmarking.
* ⚔️ **The Arena:** An automated Championship Triathlon running **Sharp Tactical Firestorms**, **Sacrificial Gambits**, and **Fischer Random / Chess960** with paired openings and commit-reveal cryptographic seeding (`SHA-256`).
* 📊 **100% Objective Scoring (No subjective grading / No viva):**
  - 🏆 **60% Main Tournament Arena:** Dynamic Swiss + Round-Robin Triathlon with Progressive Time Controls.
  - 🧩 **20% Hidden Challenge Suite:** 18 stress puzzles (Chess960, material odds, endgame conversion, variable time budgets).
  - ⚔️ **20% Calibrated Reference Gauntlet:** 3-tier Stockfish benchmark ladder (~1000, ~1500, and ~2000 Elo).

👉 **[Read the Full Official Rulebook (hackathon/RULES.md)](./hackathon/RULES.md)**  
👉 **[Enter the Bot Derby & Grab Starter Code (hackathon/README.md)](./hackathon/README.md)**

```bash
# Clone the repository:
git clone https://github.com/varadmalpure-ops/pict-knight-shift.git
cd pict-knight-shift

# Install required dependencies:
pip install python-chess

# Verify your bot passes AST security compliance:
python3 compliance_check.py hackathon/bot_template.py

# Test your bot locally in a 2-game paired match against baseline bots:
python3 hackathon/arena_runner.py hackathon/bot_template.py hackathon/aggressive_bot.py --games 2

# Test move-by-move in terminal:
python3 hackathon/test_local.py hackathon/bot_template.py hackathon/aggressive_bot.py --games 2 --verbose
```

---

## 📂 Repository Anatomy

```text
PICT Knight Shift/
├── hackathon/
│   ├── ai_sparring_bots/        # 7 AI sparring contenders (Alice, Bob, Charlie, Boris, Valkyrie, Victor, Varad)
│   ├── submitted_bots/          # Contender submissions directory
│   ├── replays/                 # Generated PGN tournament match replays
│   ├── arena_runner.py          # Official tournament runner (Triathlon, Swiss, Progressive time squeeze)
│   ├── bot_template.py          # Official starter bot template (<10 KB)
│   ├── aggressive_bot.py        # Baseline aggressive sparring bot
│   ├── random_bot.py            # Baseline random move sparring bot
│   ├── test_local.py            # Local 1v1 match tester with visual board output
│   ├── security.py              # Hardened AST security analyzer & persistent IPC sandbox
│   ├── create_poster.py         # Cybernetic knight poster compositor
│   ├── leaderboard.md           # Live updated championship standings & superlatives
│   └── RULES.md                 # Comprehensive official hackathon rulebook
├── organizer_tools/
│   ├── challenge_generator.py   # 18-test hidden puzzle & edge-case stress generator
│   ├── reference_bots.py        # Calibrated Stockfish UCI reference bot wrappers (1000, 1500, 2000 Elo)
│   ├── run_full_championship.py # Solo-organizer master tournament runner with WhatsApp summary exporter
│   └── run_gauntlet.py          # Reference gauntlet calibration runner
├── tests/
│   └── test_security.py         # 11 adversarial attack-vector test suite (dunders, shell escape, memory leaks)
├── compliance_check.py          # Single-command AST static validator for participant submissions
├── test_bot.py                  # Standalone bot validation suite
├── varad_bot.py                 # Flagship compact engine (Iterative deepening, TT, PeSTO, Mop-up)
├── AUDIT.md                     # Deep engineering audit report & vulnerability fixes
├── CHANGELOG.md                 # Full tournament infrastructure engineering changelog
└── README.md                    # This document
```

---

## 📅 Weekly Campus Schedule

| Day & Time | Ritual | What Happens |
|:---|:---|:---|
| **Daily (8:30 AM)** | 🌅 **Morning Drop** | Quick 30-sec breakdown: Opening Trap / Blunder Punishment / Endgame Rule |
| **Daily (7:30 PM)** | 🧩 **Daily Tactical Bug** | 1-minute puzzle in WhatsApp. React with `1️⃣`, `2️⃣`, `3️⃣`, or `4️⃣` to vote! |
| **Sunday (9:30 PM)** | ⚔️ **Weekly Blitz Arena** | 30-min fast-paced sprint on Chess.com + Superlative Awards recap |
| **Rolling Sundays** | 🤖 **Bot Derby Leaderboard** | Early-bird bot tournament runs; updated rankings posted in the group |

---

## 🎭 The Knight Shift Superlatives & Hall of Fame

Every week and tournament cycle, we track the chaos from our arenas and award official campus honors:

* 👑 **The Campus Grandmaster (MVP):** Overall 1st Place champion across the 100-point matrix.
* ⚔️ **The Giant Slayer:** Highest points scored against the calibrated ~2000 Elo reference benchmark engine.
* 🛡️ **The Iron Bastion:** Lowest blunder/timeout forfeit rate under high-stress time controls and adversarial positions.
* ⚡ **Tactical Maestro:** Highest score on the Hidden Challenge Suite (Chess960 & complex puzzles).
* 🗡️ **The 8-Move Executioner:** Fastest checkmate of the week.
* 👀 **The *"What Was Bro Cooking?"* Award:** Most tragic, unprovoked Queen blunder.
* 🚫 **The Shadow Realm:** Anyone caught running Stockfish in a friendly college tournament. *(Fair Play caught in 4K).*

---

## 🚀 How to Get Involved in 60 Seconds

1. **Join the WhatsApp Community:**  
   👉 [Click to Join WhatsApp](https://chat.whatsapp.com/H3DDsOt2kl91HmhcXBozbj) *(Daily puzzles, trash talk, room challenge link drops)*
2. **Join the Chess.com Club:**  
   👉 [chess.com/club/pict-knight-shift](https://www.chess.com/club/pict-knight-shift) *(Free entry to weekly arenas)*
3. **Submit a Bot to the Derby:**  
   👉 [Submit your `<name>_bot.py` via Google Form](https://forms.gle/4vuAAeGVSjJ5JzFV6) *(Read [`hackathon/RULES.md`](./hackathon/RULES.md) for starter code, constraints, and scoring)*

---
*Maintained with ❤️ by the students of PICT Pune.*
