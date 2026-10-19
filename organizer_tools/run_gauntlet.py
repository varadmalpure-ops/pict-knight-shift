"""
PICT KNIGHT SHIFT // ORGANIZER-ONLY REFERENCE GAUNTLET
File: organizer_tools/run_gauntlet.py

Evaluates a submitted bot against calibrated reference tiers:
  - Tier 1: ~1000 Elo (Novice Benchmark)
  - Tier 2: ~1500 Elo (Club Player Benchmark)
  - Tier 3: ~2000 Elo (Expert Campus Benchmark)

Uses paired openings from identical balanced positions (swapping colors)
to ensure fair, non-color-biased testing.
Detects eligibility for the "Giant Slayer" award.
"""

import sys
import os
import argparse
import time
import random
import chess

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from hackathon.security import PersistentBotClient, audit_bot_source
from organizer_tools.reference_bots import create_reference_bot, find_stockfish_binary

# Standard balanced opening positions for paired testing
BALANCED_OPENINGS = [
    # Standard start
    ("Standard Start", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
    # Italian Game (Giuoco Piano)
    ("Italian Game", "r1bqk1nr/pppp1ppp/2n5/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"),
    # Queen's Gambit Declined
    ("QGD", "rnbqkb1r/ppp2ppp/4pn2/3p4/2PP4/2N5/PP2PPPP/R1BQKBNR w KQkq - 2 4"),
    # Sicilian Defense (Classical)
    ("Sicilian Classical", "r1bqkb1r/pp2pppp/2np1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 2 5"),
]


def play_game(candidate_client: PersistentBotClient, ref_bot, candidate_is_white: bool, candidate_name: str, ref_name: str, start_fen: str, time_limit: float = 1.0, max_full_moves: int = 120):
    board = chess.Board(start_fen)
    moves_history = []

    for ply in range(max_full_moves * 2):
        if board.is_game_over():
            outcome = board.outcome()
            if outcome.winner is chess.WHITE:
                pts = 1.0 if candidate_is_white else 0.0
                winner = candidate_name if candidate_is_white else ref_name
                return pts, f"Checkmate ({winner} wins)", moves_history
            elif outcome.winner is chess.BLACK:
                pts = 0.0 if candidate_is_white else 1.0
                winner = ref_name if candidate_is_white else candidate_name
                return pts, f"Checkmate ({winner} wins)", moves_history
            else:
                return 0.5, f"Draw ({outcome.termination.name})", moves_history

        is_white_turn = (board.turn == chess.WHITE)
        candidate_turn = (candidate_is_white == is_white_turn)

        if candidate_turn:
            move, status, cpu_t, wall_t = candidate_client.query_move(board, time_limit=time_limit)
            if status != "OK" or not move:
                return 0.0, f"Candidate Forfeited [{status}]", moves_history
            if move not in board.legal_moves:
                return 0.0, f"Candidate Forfeited [Illegal move: {move}]", moves_history
        else:
            try:
                move = ref_bot.get_move(board, time_limit=time_limit)
            except Exception as e:
                return 1.0, f"Reference Error ({e})", moves_history
            if not move or move not in board.legal_moves:
                return 1.0, f"Reference Illegal Move ({move})", moves_history

        board.push(move)
        moves_history.append(move.uci())

    # Adjudication at move cap
    val = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}
    w_mat = sum(len(board.pieces(pt, chess.WHITE)) * val[pt] for pt in val)
    b_mat = sum(len(board.pieces(pt, chess.BLACK)) * val[pt] for pt in val)

    cand_mat = w_mat if candidate_is_white else b_mat
    ref_mat = b_mat if candidate_is_white else w_mat

    if cand_mat >= ref_mat + 3:
        return 1.0, f"Adjudicated ({candidate_name} +{cand_mat - ref_mat} material)", moves_history
    elif ref_mat >= cand_mat + 3:
        return 0.0, f"Adjudicated ({ref_name} +{ref_mat - cand_mat} material)", moves_history
    else:
        return 0.5, "Adjudicated Draw (Material balanced)", moves_history


def run_gauntlet(bot_file: str, pairs_per_tier: int = 1, time_limit: float = 1.0):
    print("=" * 72)
    print("⚔️  PICT KNIGHT SHIFT // REFERENCE CALIBRATION GAUNTLET")
    print("=" * 72)

    abs_path = os.path.abspath(bot_file)
    bot_name = os.path.basename(bot_file).replace(".py", "")

    # Security check before entering arena
    clean, issues = audit_bot_source(abs_path)
    if not clean:
        print(f"❌ Bot failed security audit: {issues}")
        return None, None

    print(f"Candidate Bot: {bot_name} ({abs_path})")
    stockfish = find_stockfish_binary()
    print(f"Backend Engine: {'Stockfish UCI (' + stockfish + ')' if stockfish else 'Pure Python Fallback'}")
    print(f"Match Format: Paired openings (swapping colors), 120 full moves cap, time_limit={time_limit}s\n")

    tiers = [
        (1000, "Novice Benchmark"),
        (1500, "Club Player Benchmark"),
        (2000, "Expert Campus Benchmark"),
    ]

    tier_results = {}
    total_score = 0.0
    total_games = 0

    # Initialize candidate client in sandbox
    candidate_client = PersistentBotClient(abs_path)
    ok, msg = candidate_client.start()
    if not ok:
        print(f"❌ Failed to start candidate bot sandbox: {msg}")
        return None, None

    try:
        for elo, label in tiers:
            print(f"🥊 Testing vs Tier ~{elo} Elo ({label})...")
            ref_bot = create_reference_bot(elo)
            tier_score = 0.0
            tier_games = 0

            for p_idx in range(pairs_per_tier):
                op_name, op_fen = BALANCED_OPENINGS[p_idx % len(BALANCED_OPENINGS)]

                # Leg 1: Candidate is White
                cand_pts_w, reason_w, _ = play_game(
                    candidate_client, ref_bot, candidate_is_white=True,
                    candidate_name=bot_name, ref_name=ref_bot.name,
                    start_fen=op_fen, time_limit=time_limit
                )
                tier_score += cand_pts_w
                tier_games += 1
                res_w_str = "WIN" if cand_pts_w == 1.0 else ("DRAW" if cand_pts_w == 0.5 else "LOSS")
                print(f"   Game {tier_games} [WHITE] vs {ref_bot.name} ({op_name}): {res_w_str} ({reason_w})")

                # Leg 2: Candidate is Black
                cand_pts_b, reason_b, _ = play_game(
                    candidate_client, ref_bot, candidate_is_white=False,
                    candidate_name=bot_name, ref_name=ref_bot.name,
                    start_fen=op_fen, time_limit=time_limit
                )
                tier_score += cand_pts_b
                tier_games += 1
                res_b_str = "WIN" if cand_pts_b == 1.0 else ("DRAW" if cand_pts_b == 0.5 else "LOSS")
                print(f"   Game {tier_games} [BLACK] vs {ref_bot.name} ({op_name}): {res_b_str} ({reason_b})")

            tier_results[elo] = {
                "score": tier_score,
                "total": tier_games,
                "pct": (tier_score / tier_games) * 100.0,
            }
            total_score += tier_score
            total_games += tier_games
            ref_bot.close()
            print(f"   -> Tier {elo} Subtotal: {tier_score}/{tier_games} ({tier_results[elo]['pct']:.1f}%)\n")

    finally:
        candidate_client.stop()

    # Summary & Approximate Calibration Estimation
    print("=" * 72)
    print("📊 GAUNTLET CALIBRATION SUMMARY")
    print("=" * 72)
    for elo, data in tier_results.items():
        print(f"  Tier ~{elo:4d} Elo:  {data['score']:.1f} / {data['total']} points ({data['pct']:5.1f}%)")

    # Estimated Elo Band Calculation
    s1000 = tier_results[1000]["score"] / tier_results[1000]["total"]
    s1500 = tier_results[1500]["score"] / tier_results[1500]["total"]
    s2000 = tier_results[2000]["score"] / tier_results[2000]["total"]

    if s2000 >= 0.5:
        est_elo = 2000 + int((s2000 - 0.5) * 400)
    elif s1500 >= 0.5:
        est_elo = 1500 + int(s2000 * 500)
    elif s1000 >= 0.5:
        est_elo = 1000 + int(s1500 * 500)
    else:
        est_elo = max(600, int(s1000 * 1000))

    print(f"\n🎯 Estimated Calibrated Rating: ~{est_elo} Elo (Approximate)")
    print("   * Disclaimer: Elo figures are approximate calibrated estimates based on")
    print("     Stockfish UCI reference anchors and do not represent official FIDE/USCF ratings.")

    # Giant Slayer Check
    if s2000 > 0.0:
        if s2000 >= 1.0:
            print("\n🏆 GIANT SLAYER STATUS: SUPREME CONQUEROR (Defeated the 2000 Elo reference!)")
        elif s2000 >= 0.5:
            print("\n🏆 GIANT SLAYER STATUS: QUALIFIED (Secured a win or draw vs 2000 Elo reference!)")
        else:
            print("\n🏆 GIANT SLAYER STATUS: CONTENDER (Scored points vs 2000 Elo reference!)")
    else:
        print("\n🏆 GIANT SLAYER STATUS: Not qualified (0 points vs 2000 Elo reference)")
    print("=" * 72)

    return est_elo, tier_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PICT Knight Shift Reference Gauntlet")
    parser.add_argument("bot_file", help="Path to Python bot file")
    parser.add_argument("--pairs", type=int, default=1, help="Paired openings per tier (default: 1 pair = 2 games)")
    parser.add_argument("--time-limit", type=float, default=1.0, help="Time limit per move (default: 1.0s)")
    args = parser.parse_args()

    run_gauntlet(args.bot_file, pairs_per_tier=args.pairs, time_limit=args.time_limit)
