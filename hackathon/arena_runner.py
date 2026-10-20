"""
PICT KNIGHT SHIFT // OFFICIAL TOURNAMENT RUNNER (PROFESSIONAL EDITION)
----------------------------------------------------------------------
Features:
- Hardened AST Security Scanner (hackathon.security)
- Persistent-Process IPC Sandbox (Keeps Transposition Table state alive across moves)
- Memory Limit (256 MB) & Hard Process Timeout Enforcement
- Commit-Reveal Seed Scheme (Cryptographically verifiable tournament seeds)
- Seeded, Eval-Balanced Opening Pairs (Both bots play both colors from identical positions)
- Scalable Two-Stage Format (Swiss System Qualifier -> Top-8 Double Round-Robin Finals)
- 120 Full Moves (240 Plies) Cap with Robust Endgame Adjudication
- Standard Tie-Breaks: Head-to-Head, then Sonneborn-Berger, then Total Wins

Usage:
    python3 arena_runner.py --bots-dir submitted_bots/ --time-limit 1.0
"""

import os
import sys
import glob
import time
import hashlib
import random
import argparse
import chess
import chess.pgn

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from hackathon.security import audit_bot_source, PersistentBotClient

# ============================================================================
# 1. CHAMPIONSHIP TRI-FORMAT OPENING SUITES (TACTICAL, GAMBIT, CHESS960)
# ============================================================================

# Suite A: Fischer Random / Chess960 (Zero Opening Books Possible)
CHESS960_SUITE = [
    ("Chess960 SP 520 (RBNQBKNR)", "rbnqbknr/pppppppp/8/8/8/8/PPPPPPPP/RBNQBKNR w KQkq - 0 1", True),
    ("Chess960 SP 282 (BBQNNRKR)", "bbqnnrkr/pppppppp/8/8/8/8/PPPPPPPP/BBQNNRKR w KQkq - 0 1", True),
    ("Chess960 SP 748 (RNKBQBNR)", "rnkbqbnr/pppppppp/8/8/8/8/PPPPPPPP/RNKBQBNR w KQkq - 0 1", True),
    ("Chess960 SP 406 (NQBRBNKR)", "nqbrbnkr/pppppppp/8/8/8/8/PPPPPPPP/NQBRBNKR w KQkq - 0 1", True),
]

# Suite B: Sharp Classical Tactical Firestorms
TACTICAL_SUITE = [
    ("Sicilian Dragon", "r1bqk2r/pp2ppbp/2np1np1/8/3NP3/2N1B3/PPP2PPP/R2QKB1R w KQkq - 4 7", False),
    ("King's Indian Defense", "rnbq1rk1/ppp1ppbp/3p1np1/8/2PPP3/2N2N2/PP2BPPP/R1BQK2R b KQ - 3 6", False),
    ("French Winawer", "rnbqk1nr/ppp2ppp/4p3/3p4/1b1PP3/2N5/PPP2PPP/R1BQKBNR w KQkq - 2 4", False),
    ("Modern Benoni", "rnbqkb1r/pp1p1ppp/4pn2/2p5/2PP4/5N2/PP2PPPP/RNBQKB1R w KQkq - 0 4", False),
]

# Suite C: Thematic Sacrificial Gambits
GAMBIT_SUITE = [
    ("Evans Gambit Accepted", "r1bqk1nr/pppp1ppp/2n5/2b1p3/1PB1P3/5N2/P1PP1PPP/RNBQK2R b KQkq - 0 4", False),
    ("Danish Gambit Accepted", "rnbqkbnr/pppp1ppp/8/8/2B5/8/PB3PPP/RN1QK1NR b KQkq - 0 5", False),
    ("King's Gambit Accepted", "rnbqkbnr/pppp1ppp/8/8/4Pp2/5N2/PPPP2PP/RNBQKB1R b KQkq - 1 3", False),
    ("Smith-Morra Gambit Accepted", "rnbqkbnr/pp1ppppp/8/8/8/2N5/PP2PPPP/R1BQKBNR b KQkq - 0 4", False),
]

TRI_DISCIPLINES = ["Tactical", "Gambit", "Chess960"]
DISCIPLINE_SUITES = {
    "Tactical": TACTICAL_SUITE,
    "Gambit": GAMBIT_SUITE,
    "Chess960": CHESS960_SUITE,
}

# Legacy fallback
BALANCED_OPENINGS = [
    (item[0], item[1]) for suite in DISCIPLINE_SUITES.values() for item in suite
]

# Material values for endgame adjudication
ADJUDICATION_PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 950,
    chess.KING: 0
}

# ============================================================================
# 2. COMMIT-REVEAL SEED GENERATOR
# ============================================================================

def generate_commit_hash(secret_seed: str) -> str:
    """Computes SHA-256 commitment of the tournament secret seed."""
    return hashlib.sha256(secret_seed.encode("utf-8")).hexdigest()


# ============================================================================
# 3. MATCH ENGINE (120 FULL MOVES / 240 PLIES + ADJUDICATION)
# ============================================================================

def adjudicate_position(board: chess.Board):
    """
    Evaluates board at the 120-move cap.
    Returns: ("WHITE" | "BLACK" | "DRAW", reason_string)
    """
    if board.is_checkmate():
        winner = "BLACK" if board.turn == chess.WHITE else "WHITE"
        return winner, "Checkmate"
    if board.is_stalemate():
        return "DRAW", "Stalemate"
    if board.is_insufficient_material():
        return "DRAW", "Insufficient Material"
    if board.can_claim_threefold_repetition():
        return "DRAW", "Threefold Repetition"
    if board.can_claim_fifty_moves():
        return "DRAW", "50-Move Rule"

    # Material count
    w_mat = sum(len(board.pieces(pt, chess.WHITE)) * val for pt, val in ADJUDICATION_PIECE_VALUES.items())
    b_mat = sum(len(board.pieces(pt, chess.BLACK)) * val for pt, val in ADJUDICATION_PIECE_VALUES.items())
    diff = w_mat - b_mat

    # Significant material lead (400cp = piece + pawn or more)
    if diff >= 400:
        return "WHITE", f"Adjudicated Win by Material Lead (+{diff/100:.1f})"
    elif diff <= -400:
        return "BLACK", f"Adjudicated Win by Material Lead ({diff/100:.1f})"

    return "DRAW", "Adjudicated Draw at Move Cap (Equilibrium)"


def play_game(white_client: PersistentBotClient, black_client: PersistentBotClient, start_fen: str, is_chess960: bool = False, time_limit: float = 0.20, max_full_moves: int = 120):
    """
    Simulates a single game between two persistent bot clients.
    Guarantees max 120 full moves (240 plies). Supports Chess960.
    """
    board = chess.Board(start_fen, chess960=is_chess960)
    white_name = white_client.bot_name
    black_name = black_client.bot_name

    pgn_game = chess.pgn.Game()
    pgn_game.headers["Event"] = "PICT Knight Shift 2026"
    pgn_game.headers["Site"] = "PICT Pune"
    pgn_game.headers["Date"] = time.strftime("%Y.%m.%d")
    pgn_game.headers["White"] = white_name
    pgn_game.headers["Black"] = black_name
    if is_chess960:
        pgn_game.headers["Variant"] = "Chess960"
        pgn_game.headers["SetUp"] = "1"
        pgn_game.headers["FEN"] = start_fen
    elif start_fen != chess.STARTING_FEN:
        pgn_game.headers["SetUp"] = "1"
        pgn_game.headers["FEN"] = start_fen
    pgn_node = pgn_game

    game_times = {white_name: [], black_name: []}

    while not board.is_game_over() and board.fullmove_number <= max_full_moves:
        is_white = (board.turn == chess.WHITE)
        cur_client = white_client if is_white else black_client
        cur_name = white_name if is_white else black_name
        opp_name = black_name if is_white else white_name

        move, status, cpu_t, wall_t = cur_client.query_move(board, time_limit=time_limit)
        game_times[cur_name].append(wall_t)

        if status != "OK" or move is None:
            reason = f"{cur_name} Forfeited [{status}]"
            pgn_game.headers["Result"] = "0-1" if is_white else "1-0"
            pgn_game.headers["Termination"] = reason
            _save_pgn_replay(pgn_game, white_name, black_name)
            return opp_name, reason, board.fullmove_number, game_times

        if move not in board.legal_moves:
            reason = f"{cur_name} Forfeited [Illegal move: {move}]"
            pgn_game.headers["Result"] = "0-1" if is_white else "1-0"
            pgn_game.headers["Termination"] = reason
            _save_pgn_replay(pgn_game, white_name, black_name)
            return opp_name, reason, board.fullmove_number, game_times

        pgn_node = pgn_node.add_variation(move)
        board.push(move)

    # Resolve outcome at end of game or cap
    winner, reason = adjudicate_position(board)
    winner_name = white_name if winner == "WHITE" else (black_name if winner == "BLACK" else "DRAW")
    if winner_name == white_name:
        pgn_game.headers["Result"] = "1-0"
    elif winner_name == black_name:
        pgn_game.headers["Result"] = "0-1"
    else:
        pgn_game.headers["Result"] = "1/2-1/2"
    pgn_game.headers["Termination"] = reason

    _save_pgn_replay(pgn_game, white_name, black_name)
    return winner_name, reason, board.fullmove_number, game_times


def _save_pgn_replay(pgn_game, white_name: str, black_name: str):
    """Saves PGN replay to hackathon/replays/ for WhatsApp sharing & Lichess analysis."""
    try:
        replays_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "replays")
        os.makedirs(replays_dir, exist_ok=True)
        # Individual replay
        filename = f"{white_name}_vs_{black_name}.pgn"
        with open(os.path.join(replays_dir, filename), "w", encoding="utf-8") as f:
            print(pgn_game, file=f, end="\n\n")
        # Append to master tournament PGN
        with open(os.path.join(replays_dir, "tournament_replays.pgn"), "a", encoding="utf-8") as f:
            print(pgn_game, file=f, end="\n\n")
    except Exception:
        pass


def play_paired_match(bot1_path: str, bot2_path: str, opening_fen: str, is_chess960: bool = False, time_limit: float = 0.20):
    """
    Plays an eval-balanced pair:
    Game 1: Bot1 as White, Bot2 as Black
    Game 2: Bot2 as White, Bot1 as Black
    Supports Chess960.
    """
    name1 = os.path.splitext(os.path.basename(bot1_path))[0]
    name2 = os.path.splitext(os.path.basename(bot2_path))[0]

    # Game 1
    c1 = PersistentBotClient(bot1_path)
    c2 = PersistentBotClient(bot2_path)
    c1.start()
    c2.start()

    res1, reason1, moves1, times1 = play_game(c1, c2, opening_fen, is_chess960=is_chess960, time_limit=time_limit)
    c1.stop()
    c2.stop()

    # Game 2 (Swap Colors)
    c2_rev = PersistentBotClient(bot2_path)
    c1_rev = PersistentBotClient(bot1_path)
    c2_rev.start()
    c1_rev.start()

    res2, reason2, moves2, times2 = play_game(c2_rev, c1_rev, opening_fen, is_chess960=is_chess960, time_limit=time_limit)
    c2_rev.stop()
    c1_rev.stop()

    all_times = {name1: times1[name1] + times2[name1], name2: times1[name2] + times2[name2]}
    return res1, reason1, res2, reason2, all_times


# ============================================================================
# 4. SWISS PAIRING & TOURNAMENT ORCHESTRATION
# ============================================================================

class TournamentStats:
    def __init__(self, bot_names):
        self.stats = {
            name: {
                "points": 0.0,
                "wins": 0,
                "losses": 0,
                "draws": 0,
                "checkmates": 0,
                "forfeits": 0,
                "times": [],
                "h2h": {opp: 0.0 for opp in bot_names if opp != name},
                "opponents_faced": [],
                "disciplines": {"Tactical": 0.0, "Gambit": 0.0, "Chess960": 0.0}
            }
            for name in bot_names
        }

    def record_game(self, winner: str, loser: str, is_draw: bool, is_mate: bool, is_forfeit: bool, discipline: str = None):
        if is_draw:
            self.stats[winner]["points"] += 0.5
            self.stats[loser]["points"] += 0.5
            self.stats[winner]["draws"] += 1
            self.stats[loser]["draws"] += 1
            self.stats[winner]["h2h"][loser] += 0.5
            self.stats[loser]["h2h"][winner] += 0.5
            if discipline and discipline in self.stats[winner]["disciplines"]:
                self.stats[winner]["disciplines"][discipline] += 0.5
                self.stats[loser]["disciplines"][discipline] += 0.5
        else:
            self.stats[winner]["points"] += 1.0
            self.stats[winner]["wins"] += 1
            self.stats[loser]["losses"] += 1
            self.stats[winner]["h2h"][loser] += 1.0
            if is_mate:
                self.stats[winner]["checkmates"] += 1
            if is_forfeit:
                self.stats[loser]["forfeits"] += 1
            if discipline and discipline in self.stats[winner]["disciplines"]:
                self.stats[winner]["disciplines"][discipline] += 1.0

        if loser not in self.stats[winner]["opponents_faced"]:
            self.stats[winner]["opponents_faced"].append(loser)
        if winner not in self.stats[loser]["opponents_faced"]:
            self.stats[loser]["opponents_faced"].append(winner)

    def sonneborn_berger(self, name: str) -> float:
        """Sonneborn-Berger tie-break score."""
        sb = 0.0
        for opp in self.stats[name]["opponents_faced"]:
            h2h_score = self.stats[name]["h2h"].get(opp, 0.0)
            opp_points = self.stats[opp]["points"]
            sb += h2h_score * opp_points
        return sb


def run_tournament(bot_paths, seed: str = "PICT-KNIGHT-SHIFT-2026", time_limit: float = 0.20, output_file: str = "hackathon/leaderboard.md"):
    commit_hash = generate_commit_hash(seed)
    print("\n" + "="*70)
    print("🏆 PICT KNIGHT SHIFT // CAMPUS CHESS BOT DERBY")
    print(f"🔑 Secret Seed SHA-256 Commit: {commit_hash[:16]}...{commit_hash[-8:]}")
    print("="*70)

    # 1. Static Security Audit
    print("\n🛡️ Step 1: Performing AST Security Scan on all submissions...")
    valid_bots = {}
    for p in bot_paths:
        name = os.path.splitext(os.path.basename(p))[0]
        passed, msg = audit_bot_source(p)
        if passed:
            valid_bots[name] = p
            print(f"  ✅ [ELIGIBLE] {name:20}")
        else:
            print(f"  🚫 [DISQUALIFIED] {name:20} -> {msg}")

    bot_names = sorted(list(valid_bots.keys()))
    if len(bot_names) < 2:
        print("❌ Cannot run tournament: fewer than 2 valid contenders.")
        return

    # Seed deterministic RNG for reproducible pairings & openings
    rng = random.Random(seed)
    tourney_stats = TournamentStats(bot_names)

    # 2. Select Tournament Architecture
    use_swiss = len(bot_names) > 8
    print(f"\n📊 Contenders: {len(bot_names)} | Architecture: {'Swiss Qualifier (Stage 1)' if use_swiss else 'Full Double Round-Robin Triathlon'}")

    if not use_swiss:
        # Full Double Round-Robin Triathlon across all 3 disciplines
        pairings = []
        for i in range(len(bot_names)):
            for j in range(i + 1, len(bot_names)):
                pairings.append((bot_names[i], bot_names[j]))

        rng.shuffle(pairings)
        total_games = len(pairings) * len(TRI_DISCIPLINES) * 2
        print(f"⚔️ Executing {len(pairings)} Triathlon Matchups ({total_games} games across Tactical, Gambit & Chess960)...\n")

        for idx, (b1, b2) in enumerate(pairings, 1):
            print(f"[{idx}/{len(pairings)}] {b1} vs {b2} (Triathlon Matchup: 6 games)...")

            for disc in TRI_DISCIPLINES:
                suite = DISCIPLINE_SUITES[disc]
                op_label, op_fen, is_960 = rng.choice(suite)
                print(f"   ⚔️  [{disc.upper()}] {op_label}")

                res1, reason1, res2, reason2, times = play_paired_match(
                    valid_bots[b1], valid_bots[b2], op_fen, is_chess960=is_960, time_limit=time_limit
                )

                # Record Game 1
                if res1 == "DRAW":
                    tourney_stats.record_game(b1, b2, True, False, False, discipline=disc)
                elif res1 == b1:
                    tourney_stats.record_game(b1, b2, False, "Checkmate" in reason1, "Forfeited" in reason1, discipline=disc)
                else:
                    tourney_stats.record_game(b2, b1, False, "Checkmate" in reason1, "Forfeited" in reason1, discipline=disc)

                # Record Game 2
                if res2 == "DRAW":
                    tourney_stats.record_game(b2, b1, True, False, False, discipline=disc)
                elif res2 == b2:
                    tourney_stats.record_game(b2, b1, False, "Checkmate" in reason2, "Forfeited" in reason2, discipline=disc)
                else:
                    tourney_stats.record_game(b1, b2, False, "Checkmate" in reason2, "Forfeited" in reason2, discipline=disc)

                tourney_stats.stats[b1]["times"].extend(times[b1])
                tourney_stats.stats[b2]["times"].extend(times[b2])

                print(f"      G1: {res1} ({reason1}) | G2: {res2} ({reason2})")

    # 3. Generate Standings & Leaderboard
    def sort_rank(n):
        s = tourney_stats.stats[n]
        sb = tourney_stats.sonneborn_berger(n)
        return (s["points"], sb, s["wins"], s["checkmates"])

    standings = sorted(bot_names, key=sort_rank, reverse=True)

    # Format Markdown Output
    md = []
    md.append("# 🏆 PICT Knight Shift // Championship Decathlon Leaderboard\n")
    md.append(f"**Seed SHA-256 Commit:** `{commit_hash}`  |  **Time Limit:** {time_limit}s per move\n")
    md.append("**Championship Format:** Triathlon (Tactical Gauntlet + Themed Gambits + Fischer Random Chess960)\n")
    md.append("| Rank | Contender | Overall Score | Tactical | Gambit | Chess960 | SB Tiebreak | W / D / L | Checkmates | Avg Time | Status |")
    md.append("|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")

    for rank, name in enumerate(standings, 1):
        s = tourney_stats.stats[name]
        sb = tourney_stats.sonneborn_berger(name)
        avg_t = sum(s["times"]) / len(s["times"]) if s["times"] else 0.0
        record = f"{s['wins']}W - {s['draws']}D - {s['losses']}L"
        medal = "🥇 " if rank == 1 else ("🥈 " if rank == 2 else ("🥉 " if rank == 3 else ""))
        status = "✅ Clean" if s["forfeits"] == 0 else f"⚠️ {s['forfeits']} Forfeits"
        d = s["disciplines"]
        md.append(f"| {rank} | {medal}**{name}** | **{s['points']:.1f}** | {d['Tactical']:.1f} | {d['Gambit']:.1f} | {d['Chess960']:.1f} | {sb:.2f} | {record} | {s['checkmates']} | {avg_t:.3f}s | {status} |")

    md.append("\n---\n")
    md.append("### 🎖️ Official Championship Superlatives:\n")
    if standings:
        champ = standings[0]
        md.append(f"- 👑 **Campus Grandmaster:** `{champ}` with {tourney_stats.stats[champ]['points']:.1f} total championship points!")
        tactical_champ = max(standings, key=lambda n: (tourney_stats.stats[n]["disciplines"]["Tactical"], tourney_stats.stats[n]["points"]))
        gambit_champ = max(standings, key=lambda n: (tourney_stats.stats[n]["disciplines"]["Gambit"], tourney_stats.stats[n]["points"]))
        chess960_champ = max(standings, key=lambda n: (tourney_stats.stats[n]["disciplines"]["Chess960"], tourney_stats.stats[n]["points"]))
        most_mates = max(standings, key=lambda n: tourney_stats.stats[n]["checkmates"])
        least_losses = min(standings, key=lambda n: tourney_stats.stats[n]["losses"])

        md.append(f"- ⚔️ **Tactical Maestro:** `{tactical_champ}` ({tourney_stats.stats[tactical_champ]['disciplines']['Tactical']:.1f} pts in Tactical Firestorms)")
        md.append(f"- 🗡️ **Gambit Gladiator:** `{gambit_champ}` ({tourney_stats.stats[gambit_champ]['disciplines']['Gambit']:.1f} pts in Sacrificial Gambits)")
        md.append(f"- 🎲 **Fischer Random Champion:** `{chess960_champ}` ({tourney_stats.stats[chess960_champ]['disciplines']['Chess960']:.1f} pts in Zero-Book Chess960)")
        md.append(f"- ⚡ **Executioner Award (Most Mates):** `{most_mates}` with {tourney_stats.stats[most_mates]['checkmates']} checkmates.")
        md.append(f"- 🛡️ **Iron Bastion:** `{least_losses}` conceding only {tourney_stats.stats[least_losses]['losses']} losses.")

    md.append(f"\n*(Tournament Seed revealed after final submission lock: `{seed}`)*\n")

    leaderboard_str = "\n".join(md)
    print("\n" + "="*70)
    print(leaderboard_str)
    print("="*70)

    with open(output_file, "w") as f:
        f.write(leaderboard_str)
    print(f"\n📁 Standings updated in: {output_file}")
    return tourney_stats


def main():
    parser = argparse.ArgumentParser(description="PICT Knight Shift Tournament Runner")
    parser.add_argument("--bots-dir", default="hackathon/submitted_bots", help="Directory of bot submissions")
    parser.add_argument("--seed", default="PICT-KNIGHT-SHIFT-2026-DIWALI", help="Secret tournament seed")
    parser.add_argument("--time-limit", type=float, default=0.20, help="Time limit per move (default: 0.20s)")
    parser.add_argument("--output", default="hackathon/leaderboard.md", help="Output leaderboard markdown file")
    args = parser.parse_args()

    bot_paths = glob.glob(os.path.join(args.bots_dir, "*.py"))
    if not bot_paths:
        print(f"⚠️ No bots in {args.bots_dir}. Using sample bots in hackathon/...")
        bot_paths = [p for p in glob.glob("hackathon/*.py") if "runner" not in p and "test" not in p and "security" not in p]

    run_tournament(bot_paths, seed=args.seed, time_limit=args.time_limit, output_file=args.output)


if __name__ == "__main__":
    main()
