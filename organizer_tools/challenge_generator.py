"""
PICT KNIGHT SHIFT // ORGANIZER-ONLY HIDDEN CHALLENGE SUITE GENERATOR
File: organizer_tools/challenge_generator.py
Generates reproducible, seed-derived challenge positions to force genuine engineering:
1. Chess960 Starting Setups
2. Material Odds & Imbalances
3. Critical Endgame Conversions & Holds
4. Deep Tactical Puzzles
5. Multi-Time-Control Stress Tests (0.2s / 1.0s / 2.0s)
"""

import sys
import os
import random
import hashlib
import time
import chess

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from hackathon.security import PersistentBotClient

# ============================================================================
# CURATED BENCHMARK SEED POSITIONS
# ============================================================================

ENDGAME_POOL = [
    # K+R vs K (White to move)
    ("KR_vs_K", "8/8/8/4k3/8/8/4K3/4R3 w - - 0 1", True),
    # K+Q vs K (White to move)
    ("KQ_vs_K", "8/8/8/4k3/8/8/4K3/4Q3 w - - 0 1", True),
    # K+P vs K (Key square opposition)
    ("KP_vs_K", "8/8/8/4k3/4P3/8/4K3/8 w - - 0 1", True),
    # Opposite-colored bishops (Drawn tendency)
    ("Opp_Bishops", "8/4b3/5k2/8/4P3/5K2/4B3/8 w - - 0 1", False),
]

TACTICAL_POOL = [
    # Opera Box mate-in-2 (Morfy classic: Rd8#)
    ("Opera_Mate", "4kb1r/p2rqppp/5n2/1B2p1B1/4P3/1Q6/PPP2PPP/2KR4 w k - 0 1", "d1d7"),
    # Smothered mate setup (Philidor legacy)
    ("Smothered_Fork", "6k1/5ppp/8/8/8/8/4QPPP/2r1R1K1 w - - 0 1", "e2e8"),
    # Back rank mate deflection
    ("Back_Rank_Deflection", "3r2k1/5ppp/8/8/8/1Q6/5PPP/3R2K1 w - - 0 1", "d1d8"),
    # Queen sacrifice into mate
    ("Greek_Gift", "r1bq1rk1/ppp2ppp/2n5/3pP3/1b1Pn3/2N2N2/PPP2PPP/R1BQKB1R w KQ - 0 8", "f1d3"),
]

ODDS_POOL = [
    # White Knight Odds (White starts without Nb1)
    ("White_Knight_Odds", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/R1BQKBNR w KQkq - 0 1", False),
    # Black Knight Odds (Black starts without Nb8)
    ("Black_Knight_Odds", "r1bqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", False),
    # Pawn Storm with Open Center (Tactical pressure)
    ("Pawn_Storm_Imbalance", "rnbqkbnr/pp3ppp/8/2ppP3/3P1p2/8/PPP3PP/RNBQKBNR w KQkq - 0 5", False),
]


class ChallengeSuite:
    def __init__(self, master_seed: str = "PICT-CHALLENGE-2026-SECRET"):
        self.master_seed = master_seed
        self.rng = random.Random(master_seed)
        self.suite = self._generate_suite()

    def _generate_suite(self):
        challenges = []

        # 1. Chess960 Positions (4 items)
        for i in range(4):
            schach_idx = self.rng.randint(1, 959)
            b = chess.Board.from_chess960_pos(schach_idx)
            challenges.append({
                "category": "Chess960",
                "name": f"Chess960_Pos_{schach_idx}",
                "fen": b.fen(),
                "chess960": True,
                "time_limit": 1.0,
                "max_moves": 20,
                "eval_type": "no_crash_and_progress"
            })

        # 2. Material Odds Positions (3 items)
        for name, fen, is_960 in ODDS_POOL:
            challenges.append({
                "category": "Material_Odds",
                "name": name,
                "fen": fen,
                "chess960": is_960,
                "time_limit": 1.0,
                "max_moves": 25,
                "eval_type": "odds_survival"
            })

        # 3. Endgame Conversions (4 items)
        for name, fen, is_960 in ENDGAME_POOL:
            challenges.append({
                "category": "Endgames",
                "name": name,
                "fen": fen,
                "chess960": is_960,
                "time_limit": 0.8,
                "max_moves": 40,
                "eval_type": "mate_or_hold"
            })

        # 4. Tactical Puzzles (4 items)
        for name, fen, best_move_uci in TACTICAL_POOL:
            challenges.append({
                "category": "Tactics",
                "name": name,
                "fen": fen,
                "chess960": False,
                "time_limit": 1.0,
                "best_move": best_move_uci,
                "max_moves": 1,
                "eval_type": "exact_tactical_move"
            })

        # 5. Variable Time Control Stress (3 items: 0.2s, 1.0s, 2.0s)
        time_controls = [0.2, 1.0, 2.0]
        for tc in time_controls:
            challenges.append({
                "category": "Time_Stress",
                "name": f"Speed_Stress_{tc}s",
                "fen": "r1bqk2r/pppp1ppp/2n5/4p3/2B1n3/2P2N2/PPP2PPP/R1BQK2R w KQkq - 0 6",
                "chess960": False,
                "time_limit": tc,
                "max_moves": 10,
                "eval_type": "time_safety"
            })

        return challenges


def run_challenge_suite_on_bot(bot_path: str, master_seed: str = "PICT-CHALLENGE-2026-SECRET"):
    """
    Evaluates a single bot against the hidden challenge suite.
    Returns: (score_out_of_100, detailed_log)
    """
    suite_mgr = ChallengeSuite(master_seed)
    challenges = suite_mgr.suite
    bot_name = os.path.splitext(os.path.basename(bot_path))[0]

    print(f"\n🧩 Evaluating '{bot_name}' on Hidden Challenge Suite ({len(challenges)} items)...")
    total_score = 0.0
    max_score = float(len(challenges)) * 5.0  # 5 points per challenge = 90 total, scaled to 100

    client = PersistentBotClient(bot_path)
    ok, msg = client.start()
    if not ok:
        print(f"❌ Bot failed to launch in sandbox: {msg}")
        return 0.0

    for idx, ch in enumerate(challenges, 1):
        board = chess.Board(ch["fen"], chess960=ch["chess960"])
        tc = ch["time_limit"]
        category = ch["category"]
        c_name = ch["name"]

        earned_pts = 0.0

        if ch["eval_type"] == "exact_tactical_move":
            move, status, _, _ = client.query_move(board, time_limit=tc)
            if move and move.uci() == ch["best_move"]:
                earned_pts = 5.0
                status_str = f"Found optimal {move.uci()} (+5 pts)"
            elif move in board.legal_moves:
                earned_pts = 2.0
                status_str = f"Found legal move {move.uci()} but missed optimal (+2 pts)"
            else:
                earned_pts = 0.0
                status_str = f"Failed move: {status} (0 pts)"

        elif ch["eval_type"] == "mate_or_hold":
            # Play 30 plies or until mate
            moves_count = 0
            while not board.is_game_over() and moves_count < ch["max_moves"]:
                move, status, _, _ = client.query_move(board, time_limit=tc)
                if not move or move not in board.legal_moves:
                    break
                board.push(move)
                moves_count += 1
                if not board.is_game_over():
                    # Dumb evasive opponent
                    board.push(random.choice(list(board.legal_moves)))
                    moves_count += 1

            if board.is_checkmate():
                earned_pts = 5.0
                status_str = f"Delivered checkmate in {moves_count} plies (+5 pts)"
            elif moves_count >= 15:
                earned_pts = 3.0
                status_str = f"Progressed position cleanly for {moves_count} plies (+3 pts)"
            else:
                earned_pts = 1.0
                status_str = "Stalled early (+1 pt)"

        else:
            # General survival / time safety
            moves_count = 0
            timed_out = False
            for step in range(min(ch["max_moves"], 10)):
                if board.is_game_over():
                    break
                move, status, _, _ = client.query_move(board, time_limit=tc)
                if not move or move not in board.legal_moves:
                    timed_out = True
                    break
                board.push(move)
                moves_count += 1
                if not board.is_game_over():
                    board.push(random.choice(list(board.legal_moves)))
                    moves_count += 1

            if not timed_out:
                earned_pts = 5.0
                status_str = f"Clean execution across {moves_count} moves (+5 pts)"
            else:
                earned_pts = 1.0
                status_str = "Forfeited on illegal move or timeout (+1 pt)"

        total_score += earned_pts
        print(f"  [{idx:2d}/{len(challenges)}] {category:15} | {c_name:22} -> {status_str}")

    client.stop()

    final_percentage = (total_score / max_score) * 100.0
    print(f"\n🎯 '{bot_name}' Challenge Suite Final Score: {final_percentage:.1f} / 100.0\n")
    return final_percentage


if __name__ == "__main__":
    target_bot = sys.argv[1] if len(sys.argv) > 1 else "varad_bot.py"
    run_challenge_suite_on_bot(target_bot)
