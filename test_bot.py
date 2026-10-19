"""
PICT KNIGHT SHIFT // TEST SUITE FOR BOT COMPLIANCE & PERFORMANCE
File: test_bot.py
"""

import time
import random
import chess
import varad_bot

# Baseline 1: Random Bot
def random_bot_move(board: chess.Board) -> chess.Move:
    moves = list(board.legal_moves)
    return random.choice(moves) if moves else None

# Baseline 2: 1-ply Greedy Bot
GREEDY_PIECE_VALS = {
    chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
    chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0
}

def greedy_bot_move(board: chess.Board) -> chess.Move:
    moves = list(board.legal_moves)
    if not moves:
        return None
    best_move = random.choice(moves)
    best_score = -999999
    for m in moves:
        score = 0
        board.push(m)
        if board.is_checkmate():
            board.pop()
            return m
        if board.is_check():
            score += 40
        board.pop()

        if board.is_capture(m):
            v = board.piece_at(m.to_square)
            score += (GREEDY_PIECE_VALS.get(v.piece_type, 100) if v else 100) * 10
        if m.promotion:
            score += 800
        score += random.randint(0, 10)

        if score > best_score:
            best_score = score
            best_move = m
    return best_move

# ============================================================================
# TEST 1: POSITION BENCHMARKS (Speed & Legality)
# ============================================================================

def test_position_benchmarks():
    print("\n" + "="*60)
    print("🧪 TEST 1: POSITION BENCHMARKS (Speed & Legality)")
    print("="*60)

    test_positions = [
        ("Start Position", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
        ("Tactical Middlegame (Italian)", "r1bqk2r/pppp1ppp/2n5/4p3/2B1n3/2P2N2/PPP2PPP/R1BQK2R w KQkq - 0 6"),
        ("Complex Middlegame (Sicilian)", "r1bq1rk1/pp2ppbp/2np1np1/8/3NP3/2N1BP2/PPP3PP/2KR1B1R b - - 0 9"),
        ("Endgame K+Q vs K", "8/8/8/4k3/8/8/4K3/4Q3 w - - 0 1"),
        ("Endgame K+R vs K", "8/8/8/4k3/8/8/4K3/4R3 w - - 0 1"),
        ("Endgame K+P vs K", "8/8/8/4k3/4P3/8/4K3/8 w - - 0 1"),
        ("Single Legal Move", "8/8/8/8/8/8/r7/k6K w - - 0 1"),  # Only Kh2 is legal
        ("Mate-in-1 Position", "r1bqkb1r/pppp1ppp/2n5/4p3/2B1n3/5Q2/PPPP1PPP/RNB1K1NR w KQkq - 0 5"),  # Qxf7#
        ("Stalemate-adjacent Position", "7k/8/5KQ1/8/8/8/8/8 w - - 0 1"),  # Must play Qg7# / Qh7# and avoid stalemate (Qf7/Kf7)
    ]

    all_passed = True
    for label, fen in test_positions:
        board = chess.Board(fen)
        t0 = time.time()
        move = varad_bot.get_move(board, time_limit=1.0)
        elapsed = time.time() - t0

        is_legal = (move in board.legal_moves)
        within_time = (elapsed <= 0.90)

        status = "✅ PASS" if (is_legal and within_time) else "❌ FAIL"
        if not (is_legal and within_time):
            all_passed = False

        print(f"[{status}] {label:30} -> Move: {str(move):6} ({elapsed:.3f}s) | Legal: {is_legal}")

    return all_passed

# ============================================================================
# TEST 2: ENDGAME MATE CONVERSION (KQ vs K & KR vs K)
# ============================================================================

def test_endgame_mates():
    print("\n" + "="*60)
    print("👑 TEST 2: ENDGAME CHECKMATE CONVERSIONS")
    print("="*60)

    scenarios = [
        ("K+Q vs K", "8/8/8/4k3/8/8/4K3/4Q3 w - - 0 1"),
        ("K+R vs K", "8/8/8/4k3/8/8/4K3/4R3 w - - 0 1"),
    ]

    all_mated = True
    for label, fen in scenarios:
        board = chess.Board(fen)
        moves_played = 0
        max_moves = 120

        while not board.is_game_over() and moves_played < max_moves:
            if board.turn == chess.WHITE:
                m = varad_bot.get_move(board, time_limit=0.5)
            else:
                m = random_bot_move(board)

            if m not in board.legal_moves:
                print(f"❌ Illegal move in {label}: {m}")
                all_mated = False
                break

            board.push(m)
            moves_played += 1

        if board.is_checkmate() and board.turn == chess.BLACK:
            print(f"✅ {label}: Successfully delivered CHECKMATE in {moves_played} moves!")
        else:
            print(f"❌ {label}: Failed to deliver mate within {max_moves} moves. Result: {board.result()}")
            all_mated = False

    return all_mated

# ============================================================================
# TEST 3: MATCH PLAY AGAINST BASELINES (20 GAMES)
# ============================================================================

def play_match(bot_name, bot_fn, num_games=10, max_moves=120):
    print(f"\n⚔️ Playing {num_games}-game match vs {bot_name}...")
    wins = 0
    draws = 0
    losses = 0
    varad_times = []

    for game_idx in range(num_games):
        board = chess.Board()
        varad_is_white = (game_idx % 2 == 0)
        moves_count = 0

        while not board.is_game_over() and moves_count < max_moves:
            if (board.turn == chess.WHITE) == varad_is_white:
                t0 = time.time()
                m = varad_bot.get_move(board, time_limit=0.5)
                elapsed = time.time() - t0
                varad_times.append(elapsed)
            else:
                m = bot_fn(board)

            if m not in board.legal_moves:
                # Forfeit
                break

            board.push(m)
            moves_count += 1

        # Evaluate outcome
        if board.is_checkmate():
            if (board.turn == chess.BLACK) == varad_is_white:
                wins += 1
            else:
                losses += 1
        elif board.is_game_over() or moves_count >= max_moves:
            draws += 1
        else:
            losses += 1

    avg_time = sum(varad_times) / len(varad_times) if varad_times else 0.0
    max_time = max(varad_times) if varad_times else 0.0

    print(f"📊 vs {bot_name} ({num_games} Games):")
    print(f"   Record: {wins} Wins / {draws} Draws / {losses} Losses")
    print(f"   Win Rate: {wins/num_games*100:.1f}%")
    print(f"   Avg Time per move: {avg_time:.3f}s | Max Time: {max_time:.3f}s")

    return wins, draws, losses, avg_time, max_time

def test_baseline_matches():
    print("\n" + "="*60)
    print("🏆 TEST 3: 20-GAME TOURNAMENT EVALUATION")
    print("="*60)

    # 10 games vs Random Bot
    w1, d1, l1, avg1, max1 = play_match("Random Bot", random_bot_move, num_games=10)
    # 10 games vs Greedy Bot
    w2, d2, l2, avg2, max2 = play_match("Greedy 1-Ply Bot", greedy_bot_move, num_games=10)

    total_wins = w1 + w2
    total_draws = d1 + d2
    total_losses = l1 + l2

    print("\n" + "="*60)
    print("🎯 OVERALL 20-GAME SUMMARY:")
    print(f"   Total Record: {total_wins}W - {total_draws}D - {total_losses}L")
    print(f"   Overall Win Rate: {total_wins/20*100:.1f}%")
    print(f"   Max Move Time Recorded: {max(max1, max2):.3f}s (Budget: 0.90s)")
    print("="*60)

    return total_losses == 0 and total_wins >= 18

if __name__ == "__main__":
    t_start = time.time()
    p1 = test_position_benchmarks()
    p2 = test_endgame_mates()
    p3 = test_baseline_matches()

    print(f"\nAll tests completed in {time.time() - t_start:.1f}s")
    if p1 and p2 and p3:
        print("🎉 ALL TESTS PASSED WITH 100% SUCCESS!")
    else:
        print("⚠️ Some tests encountered issues. Review logs above.")
