# PICT Knight Shift - 1-Year Progressive Chess Mastery Curriculum (500 to 1700 Elo)

This document outlines the **1-Year Progressive Chess Mastery Curriculum** for the PICT Knight Shift Chess Club. It starts at **500 Elo** (beginner-friendly) and increases by **+100 Elo each month** over 52 weeks without looping.

---

## 1. The 12-Month Progression Roadmap

| Month | Elo Rating Range | Target Stage | Key Tactical Focus & Skills |
| :---: | :---: | :---: | :--- |
| **Month 1** | **500 – 600** | Novice Fundamentals | Free piece captures, hanging queens, basic mate-in-1, two-rook ladder mate |
| **Month 2** | **600 – 700** | Beginner Tactics | Knight forks, basic pins, back-rank checkmates, Scholar's mate punishment |
| **Month 3** | **700 – 800** | Developing Tactical | Queen forks, diagonal skewers, kiss of death mate, rule of the square |
| **Month 4** | **800 – 900** | Intermediate- | Mate-in-2, double checks, deflection, rook box method, pre-move blunders |
| **Month 5** | **900 – 1000** | High 3-Digit | Smothered checkmates, Greek gift intro, removing defenders, pawn breaks |
| **Month 6** | **1000 – 1100** | **4-Digit Breakthrough!** | Tactical combinations, clearance sacrifices, Lucena bridge, opening traps |
| **Month 7** | **1100 – 1200** | Intermediate | Interference, overloaded pieces, knight endgames, master blindspots |
| **Month 8** | **1200 – 1300** | Intermediate+ | Deep multi-step forks, Philidor defense, rook activity, tactical gambits |
| **Month 9** | **1300 – 1400** | Advanced Interm. | Rook sacrifices, quiet king moves, advanced pins, Sicilian/French traps |
| **Month 10** | **1400 – 1500** | Club Player | Complex mating nets, positional blunders, queen vs pawn defenses |
| **Month 11** | **1500 – 1600** | Strong Club Player | Master combinations, zugzwang, theoretical rook endings, GM blunders |
| **Month 12** | **1600 – 1700** | Club Champion | Advanced calculation, endgame wizardry, coronation into tournament master! |

---

## 2. Weekly Assigned Timetable

| Day | Primary Event | Specialized Daily Community Feature |
| :--- | :--- | :--- |
| **Monday** | Daily Puzzle (WhatsApp Poll) | 🪤 **Opening Trap Monday** (Progressive traps for blitz & rapid) |
| **Tuesday** | Daily Puzzle (WhatsApp Poll) | 🤦 **Blunder Tuesday** (Find the blunder & punish it!) |
| **Wednesday** | Daily Puzzle (WhatsApp Poll) | ♟️ **Endgame Skills Wednesday** (Practical techniques to convert games) |
| **Thursday** | Daily Puzzle (WhatsApp Poll) | 🤦 **Blunder Thursday** (Reverse Puzzles — punish the mistake!) |
| **Friday** | Daily Puzzle (WhatsApp Poll) | 🪤 **Opening Trap Friday** (Sneaky opening traps matching month Elo) |
| **Saturday** | 🏆 **Weekly Lichess Arena** | *Puzzles paused (Tournament Day)* |
| **Sunday** | 🏅 **Tournament Recap & Awards** | *Puzzles paused (Winners Podium & Rating Awards)* |

---

## 3. Total 1-Year Content Budget (524 Items, Zero Loops)

All content is pre-verified and stored locally in [`curriculum/`](file:///Users/varadmalpure/foo/PICT%20Knight%20Shift/curriculum):
- **Daily Tactical Puzzles:** **264 puzzles** (22 per month × 12 months, Mon–Fri).
- **Opening Traps:** **104 traps** (8–9 per month × 12 months, Mon & Fri).
- **Blunder of the Day:** **104 blunders** (8–9 per month × 12 months, Tue & Thu).
- **Endgame Skills:** **52 endgames** (4–5 per month × 12 months, Wednesday).
- **Total:** **524 unique challenges**, perfectly matching 52 full weeks!

---

## 4. One-Click Daily Dispatch

To run today's exact scheduled events:
```bash
python3 send_daily_puzzle.py today
# or simply:
python3 send_daily_puzzle.py
```
- Automatically fetches today's puzzle for the **active curriculum month** with a 4-choice WhatsApp poll **PLUS** today's assigned feature (Trap on Mon/Fri, Blunder on Tue/Thu, Endgame on Wed).
- Copies the board PNG and formatted caption to your Mac clipboard!
- Generates `whatsapp_*_poll.txt` ready to paste into WhatsApp's native Poll feature.

---

## 5. Curriculum & Progress Commands

### View 1-Year Roadmap Anytime
```bash
python3 send_daily_puzzle.py curriculum
```
Displays the complete 12-month syllabus, active month, and rating range.

### View Active Dispatch Progress & History
```bash
python3 send_daily_puzzle.py history
```
Displays:
```text
• Current Month Puzzles: 0/22 dispatched in Month 1
• Total Year Puzzles:    0/264 dispatched (264 remaining)
• Total Year Traps:      0/104 dispatched (104 remaining)
• Total Year Blunders:   0/104 dispatched (104 remaining)
• Total Year Endgames:   0/52 dispatched (52 remaining)
```

### Change or Fast-Forward Month Manually
```bash
python3 send_daily_puzzle.py set-month 2   # Switches to Month 2 (600–700 Elo)
python3 send_daily_puzzle.py set-month 6   # Switches to Month 6 (1000–1100 Elo)
```

### Change Poll Option Style
```bash
python3 send_daily_puzzle.py set-style numbers   # 1️⃣ 2️⃣ 3️⃣ 4️⃣ (Numbers inside emoji buttons — default, instant WhatsApp reactions)
python3 send_daily_puzzle.py set-style letters   # 🅐 🅑 🅒 🅓 (Letters inside solid circular badges)
python3 send_daily_puzzle.py set-style red       # 🟥 A) 🟥 B) 🟥 C) 🟥 D) (Red square badges)
```

### Reset Curriculum to Month 1
```bash
python3 send_daily_puzzle.py history-reset
```

---

## 6. Manual Feature Commands

- **Daily Puzzle:** `python3 send_daily_puzzle.py puzzle` (list: `python3 send_daily_puzzle.py puzzle list`)
- **Reveal Solution:** `python3 send_daily_puzzle.py solution` (renders animated GIF + winning poll answer)
- **Opening Trap:** `python3 send_daily_puzzle.py trap` (list: `python3 send_daily_puzzle.py trap list`)
- **Blunder of the Day:** `python3 send_daily_puzzle.py blunder` (list: `python3 send_daily_puzzle.py blunder list`)
- **Endgame Study:** `python3 send_daily_puzzle.py endgame` (list: `python3 send_daily_puzzle.py endgame list`)
- **View Weekly Timetable:** `python3 send_daily_puzzle.py timetable`
- **Set Badge Style:** `python3 send_daily_puzzle.py set-style <letters|keycaps|red>`

---

## 7. Exported Curriculum & Animated GIF Solutions

The complete 1-Year Curriculum is saved inside [`PICT Knight Shift Curriculum/`](file:///Users/varadmalpure/foo/PICT%20Knight%20Shift/PICT%20Knight%20Shift%20Curriculum) organized by Month (Months 01–12) and category.

Every challenge includes 5 coordinated files ready for WhatsApp and Google Drive:
- `*_board.png`: Annotated board position with coordinates, side to play banner, and club pill tag.
- `*_caption.txt`: Challenge prompt text ready for WhatsApp.
- `*_poll.txt`: 4-option poll questions formatted for WhatsApp's native Poll feature.
- `*_solution.txt`: Solution reveal breakdown with winning poll answer.
- `*_solution.gif`: **Move-by-move animated solution GIF** showing piece moves and the final solved status!

### Curriculum Export Commands
```bash
# Export or refresh all 12 months with animated solution GIFs:
python3 export_curriculum.py

# Export a specific month (e.g. Month 1):
python3 export_curriculum.py 1

# Generate only missing solution GIFs across all months:
python3 export_curriculum.py gifs

# Re-format all 1,048 curriculum text files with WhatsApp markdown:
python3 format_curriculum_text.py

# Upload entire 1-Year Curriculum to Google Drive:
python3 gdrive_sync.py all
```
