"""
PICT KNIGHT SHIFT — CAMPUS BOT TOURNAMENT RUNNER
------------------------------------------------
Automatically loads all submitted bots from a folder, runs a round-robin tournament,
enforces the time limit per move, and generates a formatted Markdown leaderboard.

Usage:
    python3 arena_runner.py
    python3 arena_runner.py --bots-dir submitted_bots/ --time-limit 1.0
"""

import os
import sys
import time
import glob
import importlib.util
import argparse
import chess

def load_bot_from_path(file_path):
    """Loads a bot module and returns (get_move_fn, bot_name)."""
    module_name = os.path.splitext(os.path.basename(file_path))[0]
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "get_move"):
        raise ValueError(f"Module {file_path} is missing 'get_move(board, time_limit)'")

    return module.get_move, module_name

def play_match(white_fn, white_name, black_fn, black_name, time_limit=1.0, max_moves=100):
    """
    Plays a single game between two bots.
    Returns: (winner_name_or_DRAW, reason, moves_played, avg_time_dict)
    """
    board = chess.Board()
    moves_played = 0
    times = {white_name: [], black_name: []}

    while not board.is_game_over() and moves_played < max_moves:
        is_white = (board.turn == chess.WHITE)
        cur_fn = white_fn if is_white else black_fn
        cur_name = white_name if is_white else black_name
        opp_name = black_name if is_white else white_name

        t0 = time.time()
        try:
            move = cur_fn(board.copy(), time_limit)
        except Exception as e:
            return opp_name, f"Crash ({e})", moves_played, times

        elapsed = time.time() - t0
        times[cur_name].append(elapsed)

        if elapsed > time_limit:
            return opp_name, f"Timeout ({elapsed:.2f}s > {time_limit}s)", moves_played, times

        if move not in board.legal_moves:
            return opp_name, f"Illegal move ({move})", moves_played, times

        board.push(move)
        moves_played += 1

    # End conditions
    if board.is_checkmate():
        winner = black_name if board.turn == chess.WHITE else white_name
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
        reason = "Max moves limit reached"

    return winner, reason, moves_played, times

def run_tournament(bot_paths, time_limit=1.0, output_file="leaderboard.md"):
    print(f"\n🚀 Initializing PICT Knight Shift Arena with {len(bot_paths)} bots...")
    bots = {}
    for p in bot_paths:
        try:
            fn, name = load_bot_from_path(p)
            bots[name] = fn
            print(f"  ✅ Loaded: {name}")
        except Exception as e:
            print(f"  ❌ Skipping {p}: {e}")

    bot_names = list(bots.keys())
    if len(bot_names) < 2:
        print("❌ Need at least 2 valid bots to run a tournament!")
        return

    # Stats Tracker
    stats = {
        name: {
            "points": 0.0,
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "checkmates": 0,
            "times": [],
            "disqualifications": 0,
        }
        for name in bot_names
    }

    total_pairings = len(bot_names) * (len(bot_names) - 1)
    game_num = 1

    print(f"\n⚔️  Starting Round-Robin ({total_pairings} total games)...\n")

    for i in range(len(bot_names)):
        for j in range(len(bot_names)):
            if i == j:
                continue

            white_name = bot_names[i]
            black_name = bot_names[j]

            print(f"[{game_num}/{total_pairings}] {white_name} (W) vs {black_name} (B)...", end=" ", flush=True)

            winner, reason, moves, game_times = play_match(
                bots[white_name], white_name,
                bots[black_name], black_name,
                time_limit=time_limit
            )

            # Record move times
            stats[white_name]["times"].extend(game_times[white_name])
            stats[black_name]["times"].extend(game_times[black_name])

            if winner == white_name:
                stats[white_name]["points"] += 1.0
                stats[white_name]["wins"] += 1
                stats[black_name]["losses"] += 1
                if reason == "Checkmate":
                    stats[white_name]["checkmates"] += 1
                print(f"🏆 {white_name} won! ({reason}, {moves} moves)")
            elif winner == black_name:
                stats[black_name]["points"] += 1.0
                stats[black_name]["wins"] += 1
                stats[white_name]["losses"] += 1
                if reason == "Checkmate":
                    stats[black_name]["checkmates"] += 1
                print(f"🏆 {black_name} won! ({reason}, {moves} moves)")
            else:
                stats[white_name]["points"] += 0.5
                stats[black_name]["points"] += 0.5
                stats[white_name]["draws"] += 1
                stats[black_name]["draws"] += 1
                print(f"🤝 Draw ({reason}, {moves} moves)")

            if "Crash" in reason or "Timeout" in reason or "Illegal" in reason:
                loser = white_name if winner == black_name else black_name
                stats[loser]["disqualifications"] += 1

            game_num += 1

    # Generate Standings (Sorted by Points, then Wins, then Checkmates)
    standings = sorted(
        bot_names,
        key=lambda n: (stats[n]["points"], stats[n]["wins"], stats[n]["checkmates"]),
        reverse=True
    )

    # Markdown Table Generation
    md_output = []
    md_output.append("# 🏆 PICT Knight Shift // Bot Derby Standings\n")
    md_output.append(f"**Total Contenders:** {len(bot_names)}  |  **Time Limit:** {time_limit}s per move\n")
    md_output.append("| Rank | Bot Name | Score | W / D / L | Checkmates | Avg Move Time |")
    md_output.append("|:---:|:---|:---:|:---:|:---:|:---:|")

    for rank, name in enumerate(standings, 1):
        s = stats[name]
        avg_time = (sum(s["times"]) / len(s["times"])) if s["times"] else 0.0
        record = f"{s['wins']}W - {s['draws']}D - {s['losses']}L"
        medal = "🥇 " if rank == 1 else ("🥈 " if rank == 2 else ("🥉 " if rank == 3 else ""))
        md_output.append(f"| {rank} | {medal}**{name}** | **{s['points']}** | {record} | {s['checkmates']} | {avg_time:.3f}s |")

    md_output.append("\n---\n")
    md_output.append("### 🎖️ Special Superlatives:\n")
    if standings:
        champion = standings[0]
        md_output.append(f"- 👑 **The Campus Grandmaster:** `{champion}` ({stats[champion]['points']} pts)")
        
        # Most lethal
        most_mates = max(standings, key=lambda n: stats[n]["checkmates"])
        md_output.append(f"- ⚡ **Executioner Award (Most Mates):** `{most_mates}` ({stats[most_mates]['checkmates']} checkmates)")

        # Fastest bot
        fastest = min(standings, key=lambda n: (sum(stats[n]["times"]) / len(stats[n]["times"])) if stats[n]["times"] else 999)
        fastest_time = (sum(stats[fastest]["times"]) / len(stats[fastest]["times"])) if stats[fastest]["times"] else 0.0
        md_output.append(f"- 🏎️ **Speed Demon:** `{fastest}` ({fastest_time*1000:.1f}ms average calculation time)")

    leaderboard_text = "\n".join(md_output)

    # Print to console
    print("\n" + "="*50)
    print(leaderboard_text)
    print("="*50)

    # Save to file
    with open(output_file, "w") as f:
        f.write(leaderboard_text)
    print(f"\n📁 Standings saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Run the PICT Knight Shift Bot Tournament.")
    parser.add_argument("--bots-dir", default="submitted_bots", help="Directory containing bot .py files")
    parser.add_argument("--time-limit", type=float, default=1.0, help="Max time per move in seconds")
    parser.add_argument("--output", default="leaderboard.md", help="Path to save the Markdown leaderboard")
    args = parser.parse_args()

    # Search for bots in bots-dir
    bot_paths = glob.glob(os.path.join(args.bots_dir, "*.py"))

    # If no bots in submitted_bots, default to testing the sample bots in the current folder
    if not bot_paths:
        print(f"⚠️  No bots found in '{args.bots_dir}'. Testing with sample bots...")
        bot_paths = glob.glob("*.py")
        # Filter out runner and test scripts
        bot_paths = [p for p in bot_paths if "runner" not in p and "test" not in p]

    run_tournament(bot_paths, time_limit=args.time_limit, output_file=args.output)

if __name__ == "__main__":
    main()
