"""
PICT KNIGHT SHIFT — LOCAL BOT TESTER
-----------------------------------
Run a quick test match between two bots on your local machine.

Usage:
    python3 test_local.py bot_template.py random_bot.py
    python3 test_local.py my_bot.py aggressive_bot.py --games 4
"""

import sys
import os
import time
import importlib.util
import argparse
import chess

def load_bot(file_path):
    """Dynamically imports a bot module given its file path."""
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found: {file_path}")
        sys.exit(1)

    module_name = os.path.splitext(os.path.basename(file_path))[0]
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "get_move"):
        print(f"❌ Error: {file_path} does not define 'get_move(board, time_limit)'")
        sys.exit(1)

    return module.get_move, module_name

def play_single_game(white_fn, white_name, black_fn, black_name, time_limit=1.0, max_moves=100, verbose=False):
    board = chess.Board()
    move_count = 0
    total_time = {white_name: 0.0, black_name: 0.0}

    print(f"\n⚔️  {white_name} (WHITE) vs {black_name} (BLACK)")

    while not board.is_game_over() and move_count < max_moves:
        is_white = (board.turn == chess.WHITE)
        current_fn = white_fn if is_white else black_fn
        current_name = white_name if is_white else black_name

        start_time = time.time()
        try:
            move = current_fn(board.copy(), time_limit)
        except Exception as e:
            print(f"💥 {current_name} threw an unhandled exception: {e}")
            return ("BLACK" if is_white else "WHITE"), f"{current_name} crashed"

        elapsed = time.time() - start_time
        total_time[current_name] += elapsed

        if elapsed > time_limit:
            print(f"⏳ {current_name} TIMED OUT ({elapsed:.2f}s > {time_limit}s)")
            return ("BLACK" if is_white else "WHITE"), f"{current_name} timed out"

        if move not in board.legal_moves:
            print(f"🚫 {current_name} made an ILLEGAL move: {move}")
            return ("BLACK" if is_white else "WHITE"), f"{current_name} illegal move"

        board.push(move)
        move_count += 1

        if verbose:
            print(f"Move {move_count}: {current_name} played {move.uci()} ({elapsed:.3f}s)")

    # Game Over Evaluation
    if board.is_checkmate():
        winner = "BLACK" if board.turn == chess.WHITE else "WHITE"
        reason = "Checkmate"
    elif board.is_stalemate():
        winner = "DRAW"
        reason = "Stalemate"
    elif board.is_insufficient_material():
        winner = "DRAW"
        reason = "Insufficient Material"
    elif board.can_claim_threefold_repetition():
        winner = "DRAW"
        reason = "Threefold Repetition"
    elif board.can_claim_fifty_moves():
        winner = "DRAW"
        reason = "50-Move Rule"
    else:
        winner = "DRAW"
        reason = "Max moves reached"

    print(f"🏁 Result: {winner} wins ({reason}) in {move_count} moves.")
    return winner, reason

def main():
    parser = argparse.ArgumentParser(description="Test two chess bots locally.")
    parser.add_argument("bot1", help="Path to bot 1 (.py file)")
    parser.add_argument("bot2", help="Path to bot 2 (.py file)")
    parser.add_argument("--games", type=int, default=2, help="Number of games to play (alternating colors)")
    parser.add_argument("--time-limit", type=float, default=1.0, help="Time limit per move in seconds")
    parser.add_argument("--verbose", action="store_true", help="Print every move")
    args = parser.parse_args()

    fn1, name1 = load_bot(args.bot1)
    fn2, name2 = load_bot(args.bot2)

    scores = {name1: 0.0, name2: 0.0}

    for game_idx in range(args.games):
        if game_idx % 2 == 0:
            winner, _ = play_single_game(fn1, name1, fn2, name2, args.time_limit, verbose=args.verbose)
            if winner == "WHITE":
                scores[name1] += 1.0
            elif winner == "BLACK":
                scores[name2] += 1.0
            else:
                scores[name1] += 0.5
                scores[name2] += 0.5
        else:
            winner, _ = play_single_game(fn2, name2, fn1, name1, args.time_limit, verbose=args.verbose)
            if winner == "WHITE":
                scores[name2] += 1.0
            elif winner == "BLACK":
                scores[name1] += 1.0
            else:
                scores[name1] += 0.5
                scores[name2] += 0.5

    print("\n" + "="*40)
    print(f"🏆 FINAL MATCH SCORE ({args.games} Games):")
    print(f"  {name1}: {scores[name1]} pts")
    print(f"  {name2}: {scores[name2]} pts")
    print("="*40)

if __name__ == "__main__":
    main()
