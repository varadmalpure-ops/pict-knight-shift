# 📥 Hackathon Submissions Directory (`hackathon/submitted_bots/`)
### *Drop your `<your_name>_bot.py` here to enter the official arena!*

1. **Submission File:** Single Python file named `<your_name>_bot.py` (e.g., `pranav_bot.py`, `riya_bot.py`).
2. **File Size Limit:** $\le$ **10 KB** (10,240 bytes). Verified by static AST scanner.
3. **Execution Interface:** Must implement:
   ```python
   import chess
   def get_move(board: chess.Board, time_limit: float = 0.20) -> chess.Move:
       ...
   ```
4. **Offline Sparring:**
   Before submitting, test your bot against the 7 AI sparring baselines in `hackathon/ai_sparring_bots/`:
   ```bash
   python3 hackathon/arena_runner.py hackathon/submitted_bots/your_name_bot.py hackathon/ai_sparring_bots/boris_bastion_bot.py
   ```
5. **Stockfish Multi-Tier Benchmark:**
   Benchmark your engine directly against the official 7-Tier Stockfish Ladder:
   ```bash
   python3 organizer_tools/run_gauntlet.py hackathon/submitted_bots/your_name_bot.py
   ```
