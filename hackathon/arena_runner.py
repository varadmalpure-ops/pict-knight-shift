"""
PICT KNIGHT SHIFT — CAMPUS BOT TOURNAMENT RUNNER (BULLETPROOF EDITION)
---------------------------------------------------------------------
Features:
- Anti-Cheat & Security Scanner (Blocks Stockfish, subprocess, network APIs, eval/exec)
- Hard Process-Level Timeout (Immune to infinite loops and hangs)
- Full Round-Robin Tournament (Every bot plays as White & Black)
- Formatted Markdown Leaderboard with Special Awards

Usage:
    python3 arena_runner.py --bots-dir submitted_bots/ --time-limit 1.0
"""

import os
import sys
import time
import glob
import ast
import argparse
import multiprocessing as mp
import importlib.util
import chess

# ============================================================================
# 1. ANTI-CHEAT & STATIC SECURITY AUDITOR
# ============================================================================

ALLOWED_MODULES = {
    "chess", "chess.polyglot", "math", "random", "time", "copy",
    "collections", "itertools", "functools", "typing", "dataclasses", "enum"
}

FORBIDDEN_CALLS = {"eval", "exec", "compile", "__import__", "open"}


def audit_bot_security(file_path: str):
    """
    Statically audits the bot's source code before running it.
    Blocks Stockfish wrappers, network API requests, and system execution.
    """
    # 1. File size check (Max 150KB: Prevents embedding neural network weights or binaries)
    size_kb = os.path.getsize(file_path) / 1024
    if size_kb > 150:
        return False, f"File too large ({size_kb:.1f}KB > 150KB limit). Embedded binaries are prohibited."

    # 2. AST Syntax Tree Inspection
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        tree = ast.parse(code, filename=file_path)
    except Exception as e:
        return False, f"Syntax Error: {e}"

    for node in ast.walk(tree):
        # Check Imports (import foo)
        if isinstance(node, ast.Import):
            for alias in node.names:
                base_pkg = alias.name.split('.')[0]
                full_pkg = alias.name
                if full_pkg == "chess.engine":
                    return False, "FORBIDDEN: 'chess.engine' detected! Using Stockfish / external engines is cheating."
                if base_pkg not in ALLOWED_MODULES:
                    return False, f"FORBIDDEN: Import '{alias.name}' is not allowed. Only pure python + python-chess allowed."

        # Check From Imports (from foo import bar)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                base_pkg = node.module.split('.')[0]
                if node.module == "chess.engine" or "engine" in node.module:
                    return False, "FORBIDDEN: 'chess.engine' detected! Stockfish is strictly prohibited."
                if base_pkg not in ALLOWED_MODULES:
                    return False, f"FORBIDDEN: Import from '{node.module}' is not allowed."

        # Check Dangerous Function Calls (eval, exec, open)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
                return False, f"FORBIDDEN: Call to '{node.func.id}()' is prohibited for sandbox security."

    return True, "Security verification passed"


# ============================================================================
# 2. SAFE PROCESS-LEVEL MOVE EXECUTOR (HARD TIMEOUT)
# ============================================================================

def _worker_wrapper(file_path: str, fen: str, time_limit: float, queue: mp.Queue):
    """Executes get_move inside an isolated sub-process."""
    try:
        module_name = f"bot_{os.path.splitext(os.path.basename(file_path))[0]}"
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if not hasattr(module, "get_move"):
            queue.put(("ERROR", "Missing 'get_move(board, time_limit)'"))
            return

        board = chess.Board(fen)
        move = module.get_move(board, time_limit)
        queue.put(("OK", move.uci() if move else None))
    except Exception as e:
        queue.put(("ERROR", str(e)))


def execute_move_with_hard_timeout(file_path: str, board: chess.Board, time_limit: float):
    """
    Runs the bot in a separate OS process with a hard deadline.
    Immune to infinite while loops (while True: pass), memory leaks, and hangs.
    """
    queue = mp.Queue()
    fen = board.fen()
    proc = mp.Process(target=_worker_wrapper, args=(file_path, fen, time_limit, queue))

    start_time = time.time()
    proc.start()

    # Hard cutoff: time_limit + 0.25s grace period for process spawning
    hard_limit = time_limit + 0.25
    proc.join(timeout=hard_limit)

    elapsed = time.time() - start_time

    if proc.is_alive():
        proc.terminate()
        proc.join()
        return None, f"Hard Timeout ({elapsed:.2f}s > {time_limit}s limit)", elapsed

    if queue.empty():
        return None, "Subprocess terminated unexpectedly without returning a move", elapsed

    status, payload = queue.get()
    if status == "ERROR":
        return None, f"Crash: {payload}", elapsed

    if not payload:
        return None, "Bot returned None instead of a legal move", elapsed

    try:
        move = chess.Move.from_uci(payload)
        return move, "OK", elapsed
    except Exception as e:
        return None, f"Invalid UCI format: {payload}", elapsed


# ============================================================================
# 3. MATCH ENGINE
# ============================================================================

def play_match(white_path, white_name, black_path, black_name, time_limit=1.0, max_moves=120):
    board = chess.Board()
    moves_played = 0
    times = {white_name: [], black_name: []}

    while not board.is_game_over() and moves_played < max_moves:
        is_white = (board.turn == chess.WHITE)
        cur_name = white_name if is_white else black_name
        opp_name = black_name if is_white else white_name
        cur_path = white_path if is_white else black_path

        move, status, elapsed = execute_move_with_hard_timeout(cur_path, board, time_limit)
        times[cur_name].append(elapsed)

        if status != "OK":
            return opp_name, f"{cur_name} Forfeited [{status}]", moves_played, times

        if move not in board.legal_moves:
            return opp_name, f"{cur_name} Forfeited [Illegal move: {move}]", moves_played, times

        board.push(move)
        moves_played += 1

    # End Evaluation
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
        reason = "Max moves limit reached (Draw)"

    return winner, reason, moves_played, times


# ============================================================================
# 4. TOURNAMENT RUNNER & LEADERBOARD GENERATION
# ============================================================================

def run_tournament(bot_paths, time_limit=1.0, output_file="leaderboard.md"):
    print(f"\n🛡️ Running Anti-Cheat & Security Scan on {len(bot_paths)} submissions...")
    valid_bots = {}

    for p in bot_paths:
        name = os.path.splitext(os.path.basename(p))[0]
        passed, msg = audit_bot_security(p)
        if passed:
            valid_bots[name] = p
            print(f"  ✅ [PASSED] {name}")
        else:
            print(f"  🚫 [DISQUALIFIED - CHEAT/SECURITY] {name}: {msg}")

    bot_names = sorted(list(valid_bots.keys()))
    if len(bot_names) < 2:
        print("❌ Need at least 2 valid, un-disqualified bots to run a tournament!")
        return

    stats = {
        name: {
            "points": 0.0,
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "checkmates": 0,
            "times": [],
            "forfeits_caused": 0,
            "forfeits_suffered": 0
        }
        for name in bot_names
    }

    total_pairings = len(bot_names) * (len(bot_names) - 1)
    game_num = 1

    print(f"\n⚔️ Starting Full Round-Robin ({total_pairings} total games, {time_limit}s limit)...\n")

    for i in range(len(bot_names)):
        for j in range(len(bot_names)):
            if i == j:
                continue

            white_name = bot_names[i]
            black_name = bot_names[j]

            print(f"[{game_num}/{total_pairings}] {white_name} (W) vs {black_name} (B)...", end=" ", flush=True)

            winner, reason, moves, game_times = play_match(
                valid_bots[white_name], white_name,
                valid_bots[black_name], black_name,
                time_limit=time_limit
            )

            stats[white_name]["times"].extend(game_times[white_name])
            stats[black_name]["times"].extend(game_times[black_name])

            if winner == white_name:
                stats[white_name]["points"] += 1.0
                stats[white_name]["wins"] += 1
                stats[black_name]["losses"] += 1
                if "Checkmate" in reason:
                    stats[white_name]["checkmates"] += 1
                print(f"🏆 {white_name} won! ({reason}, {moves} moves)")
            elif winner == black_name:
                stats[black_name]["points"] += 1.0
                stats[black_name]["wins"] += 1
                stats[white_name]["losses"] += 1
                if "Checkmate" in reason:
                    stats[black_name]["checkmates"] += 1
                print(f"🏆 {black_name} won! ({reason}, {moves} moves)")
            else:
                stats[white_name]["points"] += 0.5
                stats[black_name]["points"] += 0.5
                stats[white_name]["draws"] += 1
                stats[black_name]["draws"] += 1
                print(f"🤝 Draw ({reason}, {moves} moves)")

            if "Forfeited" in reason:
                if winner == white_name:
                    stats[black_name]["forfeits_suffered"] += 1
                    stats[white_name]["forfeits_caused"] += 1
                else:
                    stats[white_name]["forfeits_suffered"] += 1
                    stats[black_name]["forfeits_caused"] += 1

            game_num += 1

    # Sort standings: Points -> Wins -> Checkmates -> Lowest Avg Move Time
    def rank_key(n):
        s = stats[n]
        avg_t = sum(s["times"]) / len(s["times"]) if s["times"] else 999.0
        return (s["points"], s["wins"], s["checkmates"], -avg_t)

    standings = sorted(bot_names, key=rank_key, reverse=True)

    # Markdown Generation
    md_output = []
    md_output.append("# 🏆 PICT Knight Shift // Campus Bot Derby Official Standings\n")
    md_output.append(f"**Total Contenders:** {len(bot_names)}  |  **Time Limit:** {time_limit}s per move\n")
    md_output.append("| Rank | Bot Handle | Points | W - D - L | Mates | Avg Move Time | Status |")
    md_output.append("|:---:|:---|:---:|:---:|:---:|:---:|:---:|")

    for rank, name in enumerate(standings, 1):
        s = stats[name]
        avg_time = (sum(s["times"]) / len(s["times"])) if s["times"] else 0.0
        record = f"{s['wins']}W - {s['draws']}D - {s['losses']}L"
        medal = "🥇 " if rank == 1 else ("🥈 " if rank == 2 else ("🥉 " if rank == 3 else ""))
        status = "✅ Clean" if s["forfeits_suffered"] == 0 else f"⚠️ {s['forfeits_suffered']} Forfeits"
        md_output.append(f"| {rank} | {medal}**{name}** | **{s['points']}** | {record} | {s['checkmates']} | {avg_time:.3f}s | {status} |")

    md_output.append("\n---\n")
    md_output.append("### 🎖️ Official Superlatives:\n")
    if standings:
        champion = standings[0]
        md_output.append(f"- 👑 **Campus Grandmaster:** `{champion}` with **{stats[champion]['points']}** total points!")
        
        most_mates = max(standings, key=lambda n: stats[n]["checkmates"])
        md_output.append(f"- ⚡ **Executioner Award (Most Mates):** `{most_mates}` with {stats[most_mates]['checkmates']} checkmates.")

        fastest = min(standings, key=lambda n: (sum(stats[n]["times"]) / len(stats[n]["times"])) if stats[n]["times"] else 999)
        fastest_t = (sum(stats[fastest]["times"]) / len(stats[fastest]["times"])) if stats[fastest]["times"] else 0.0
        md_output.append(f"- 🏎️ **Speed Demon:** `{fastest}` calculating in {fastest_t*1000:.1f}ms average.")

    leaderboard_text = "\n".join(md_output)

    print("\n" + "="*50)
    print(leaderboard_text)
    print("="*50)

    with open(output_file, "w") as f:
        f.write(leaderboard_text)
    print(f"\n📁 Standings updated in: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Run the PICT Knight Shift Bot Tournament.")
    parser.add_argument("--bots-dir", default="hackathon/submitted_bots", help="Directory containing bot .py files")
    parser.add_argument("--time-limit", type=float, default=1.0, help="Max time per move in seconds")
    parser.add_argument("--output", default="hackathon/leaderboard.md", help="Path to save the Markdown leaderboard")
    args = parser.parse_args()

    bot_paths = glob.glob(os.path.join(args.bots_dir, "*.py"))

    if not bot_paths:
        print(f"⚠️ No bots in '{args.bots_dir}'. Testing sample bots in hackathon/...")
        bot_paths = glob.glob("hackathon/*.py")
        bot_paths = [p for p in bot_paths if "runner" not in p and "test" not in p]

    run_tournament(bot_paths, time_limit=args.time_limit, output_file=args.output)


if __name__ == "__main__":
    main()
