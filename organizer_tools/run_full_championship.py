"""
PICT KNIGHT SHIFT // SOLO-ORGANIZER MASTER TOURNAMENT RUNNER
File: organizer_tools/run_full_championship.py

One-click automated evaluation for the entire hackathon:
  1. Audits every submission in `hackathon/submitted_bots/` with the AST Security Scanner.
  2. Bounded Scaling Architecture:
     - If <= 8 bots: Direct Double Round-Robin (Paired balanced openings).
     - If > 8 bots: 5-Round Swiss Qualifier -> Top-8 Double Round-Robin Finals.
  3. Runs the Hidden Challenge Suite (Chess960, endgames, tactics, bullet) -> 20 Pts.
  4. Runs the Calibrated Reference Gauntlet (1000, 1500, 2000 Elo) -> 10 Pts.
  5. Computes final 100-Point standings and awards (Grandmaster, Giant Slayer, Iron Bastion, Tactical Maestro).
  6. Exports PGN game replays for WhatsApp and Lichess move-by-move analysis.
  7. Optional `--provisional` mode: Formats and copies a weekly leaderboard directly to your clipboard!
"""

import sys
import os
import glob
import time
import argparse
import subprocess
import chess

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from hackathon.security import audit_bot_source
from organizer_tools.challenge_generator import ChallengeSuite
from organizer_tools.run_gauntlet import run_gauntlet
from hackathon.arena_runner import run_tournament


def copy_to_clipboard(text: str):
    """Copies text to macOS clipboard via pbcopy if available."""
    try:
        p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
        p.communicate(text.encode("utf-8"))
        print("\n📋 [✓] WhatsApp update copied to your clipboard! Press Cmd+V to paste.")
    except Exception:
        pass


def run_full_championship(bots_dir: str = "hackathon/submitted_bots", secret_seed: str = "PICT-FINALE-2026-SECRET", provisional: bool = False):
    mode_title = "WEEKLY PROVISIONAL LADDER RUN" if provisional else "MASTER CHAMPIONSHIP FINALE"
    print("=" * 76)
    print(f"🏆 PICT KNIGHT SHIFT // {mode_title}")
    print("=" * 76)
    print(f"Target Bot Directory: {bots_dir}")
    print(f"Cryptographic Seed:   {secret_seed}")
    print(f"Evaluation Mode:      {'Provisional Fast Ladder' if provisional else 'Full 100-Point Finale'}\n")

    # 1. Discover and Audit Submissions
    bot_files = sorted(glob.glob(os.path.join(bots_dir, "*_bot.py")))
    if not bot_files:
        print(f"❌ No bot files found matching '*_bot.py' in {bots_dir}!")
        return

    print(f"🔍 Discovered {len(bot_files)} submission(s). Running AST security audits...")
    eligible_bots = []
    disqualified_bots = []

    for bf in bot_files:
        name = os.path.splitext(os.path.basename(bf))[0]
        clean, issues = audit_bot_source(bf)
        if clean:
            print(f"  ✅ [ELIGIBLE] {name}")
            eligible_bots.append(bf)
        else:
            print(f"  ❌ [DISQUALIFIED] {name} -> {issues}")
            disqualified_bots.append((name, issues))

    if len(eligible_bots) < 2:
        print("\n⚠️ Need at least 2 eligible bots to run matches. Add bots to submitted_bots/.")
        return

    scores = {os.path.splitext(os.path.basename(b))[0]: {
        "challenge": 0.0, "gauntlet": 0.0, "arena": 0.0, "total": 0.0, "path": b,
        "wins": 0, "losses": 0, "draws": 0, "forfeits": 0, "est_elo": 0
    } for b in eligible_bots}

    # 2. Run Hidden Challenge Suite (20 Points)
    print("\n" + "=" * 76)
    print("🧩 STAGE 1: HIDDEN CHALLENGE SUITE (20 POINTS)")
    print("=" * 76)
    suite = ChallengeSuite(master_seed=secret_seed)
    for b_path in eligible_bots:
        name = os.path.splitext(os.path.basename(b_path))[0]
        print(f"Evaluating {name} on 18 challenge puzzles...")
        raw_score, _ = suite.evaluate_bot(b_path)
        pts_20 = (raw_score / 100.0) * 20.0
        scores[name]["challenge"] = round(pts_20, 2)
        print(f"-> {name} Challenge Score: {pts_20:.2f} / 20.0 pts\n")

    # 3. Run Reference Gauntlet (10 Points)
    print("=" * 76)
    print("⚔️ STAGE 2: CALIBRATED REFERENCE GAUNTLET (10 POINTS)")
    print("=" * 76)
    for b_path in eligible_bots:
        name = os.path.splitext(os.path.basename(b_path))[0]
        print(f"Running gauntlet ladder for {name}...")
        est_elo, tier_results = run_gauntlet(b_path, pairs_per_tier=1 if provisional else 2, time_limit=0.20)
        if tier_results:
            tot_raw = sum(t["score"] for t in tier_results.values())
            max_gaunt_pts = sum(t["total"] for t in tier_results.values())
            pts_10 = (tot_raw / max_gaunt_pts) * 10.0 if max_gaunt_pts > 0 else 0.0
            scores[name]["gauntlet"] = round(pts_10, 2)
            scores[name]["est_elo"] = est_elo
            scores[name]["vs_2000"] = tier_results[2000]["score"]
        else:
            scores[name]["gauntlet"] = 0.0
            scores[name]["est_elo"] = 0
            scores[name]["vs_2000"] = 0.0

    # 4. Run Main Arena Tournament (70 Points) with Bounded Scaling
    print("\n" + "=" * 76)
    print("🥊 STAGE 3: MAIN TOURNAMENT ARENA (70 POINTS)")
    print("=" * 76)

    # Run tournament (handles both Swiss Qualifier for >8 bots and Double Round-Robin for <=8 bots)
    tourney_stats = run_tournament(eligible_bots, seed=secret_seed, time_limit=0.20)
    if tourney_stats:
        max_possible_arena_pts = (len(eligible_bots) - 1) * 6.0
        for name in scores:
            if name in tourney_stats.stats:
                rec = tourney_stats.stats[name]
                arena_raw = rec["points"]
                pts_70 = (arena_raw / max_possible_arena_pts) * 70.0 if max_possible_arena_pts > 0 else 0.0
                scores[name]["arena"] = round(pts_70, 2)
                scores[name]["wins"] = rec.get("wins", 0)
                scores[name]["losses"] = rec.get("losses", 0)
                scores[name]["draws"] = rec.get("draws", 0)
                scores[name]["forfeits"] = rec.get("forfeits", 0)

    for name in scores:
        scores[name]["total"] = round(scores[name]["challenge"] + scores[name]["gauntlet"] + scores[name]["arena"], 2)

    # 5. Final Standings
    ranked = sorted(scores.items(), key=lambda item: (item[1]["total"], item[1]["arena"], item[1]["wins"]), reverse=True)

    print("\n" + "=" * 76)
    print(f"🏆 {mode_title} LEADERBOARD (100-POINT MATRIX)")
    print("=" * 76)
    print(f"{'Rank':<5} | {'Bot Name':<20} | {'Arena (70)':<10} | {'Suite (20)':<10} | {'Gaunt (10)':<10} | {'Total':<8} | {'Est. Elo'}")
    print("-" * 76)

    for rank, (name, d) in enumerate(ranked, start=1):
        print(f"#{rank:<4} | {name:<20} | {d['arena']:<10.2f} | {d['challenge']:<10.2f} | {d['gauntlet']:<10.2f} | {d['total']:<8.2f} | ~{d.get('est_elo', 'N/A')}")

    champion = ranked[0][0]
    print("\n" + "=" * 76)
    print(f"👑 TOP CONTENDER / GRANDMASTER: {champion} ({ranked[0][1]['total']:.2f} pts)!")

    # Check Giant Slayer
    giant_slayers = [name for name, d in scores.items() if d.get("vs_2000", 0) > 0]
    if giant_slayers:
        print(f"⚔️ GIANT SLAYER QUALIFIER(S): {', '.join(giant_slayers)} (Scored vs 2000 Elo reference!)")
    else:
        print("⚔️ GIANT SLAYER: None qualified (The 2000 Elo reference remains undefeated)")

    # Check Iron Bastion
    iron_bastion = min(scores.items(), key=lambda item: item[1].get("forfeits", 0))[0]
    print(f"🛡️ IRON BASTION: {iron_bastion} (Lowest blunder/timeout forfeit rate)")

    # Check Tactical Maestro
    maestro = max(scores.items(), key=lambda item: item[1]["challenge"])[0]
    print(f"⚡ TACTICAL MAESTRO: {maestro} ({scores[maestro]['challenge']:.2f}/20 pts on challenge puzzles)")
    print("=" * 76)

    # Export PGN notification
    print("\n📦 REPLAY EXPORTS:")
    print("  • Match replays saved to: hackathon/replays/tournament_replays.pgn")
    print("  • Upload to https://lichess.org/paste to view moves with live Stockfish analysis.")

    # 6. Format WhatsApp Announcement Snippet
    whatsapp_msg = f"📊 *PICT KNIGHT SHIFT // {mode_title}* ♟️⚡\n"
    whatsapp_msg += f"_Updated: {time.strftime('%A, %d %B %Y')}_\n\n"
    whatsapp_msg += "🏆 *CURRENT STANDINGS:*\n"
    for rank, (name, d) in enumerate(ranked, start=1):
        medal = "🥇" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else f"#{rank}"))
        whatsapp_msg += f"{medal} *{name}* — {d['total']:.1f} pts (Arena: {d['arena']:.1f} | Puzzles: {d['challenge']:.1f} | Elo: ~{d.get('est_elo', 'N/A')})\n"

    whatsapp_msg += f"\n👑 *Current Leader:* {champion}\n"
    if giant_slayers:
        whatsapp_msg += f"⚔️ *Giant Slayer Contenders:* {', '.join(giant_slayers)}\n"
    whatsapp_msg += "\n💡 _Submit your updated bot anytime before Sunday night to climb the ladder!_\n"
    whatsapp_msg += "👉 Form: https://forms.gle/4vuAAeGVSjJ5JzFV6"

    copy_to_clipboard(whatsapp_msg)

    # Update leaderboard.md
    with open("hackathon/leaderboard.md", "w", encoding="utf-8") as f:
        f.write(f"# 🏆 PICT Knight Shift // {mode_title}\n\n")
        f.write(f"*Last Updated: {time.strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        f.write("| Rank | Bot Contender | Arena (70) | Challenge Suite (20) | Ref Gauntlet (10) | Total Score | Calibrated Elo |\n")
        f.write("| :---: | :--- | :---: | :---: | :---: | :---: | :---: |\n")
        for rank, (name, d) in enumerate(ranked, start=1):
            f.write(f"| **#{rank}** | `{name}` | {d['arena']:.2f} | {d['challenge']:.2f} | {d['gauntlet']:.2f} | **{d['total']:.2f}** | ~{d.get('est_elo', 'N/A')} |\n")
        f.write(f"\n**Replays:** All games recorded in [`hackathon/replays/tournament_replays.pgn`](replays/tournament_replays.pgn).\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PICT Knight Shift Master Tournament Runner")
    parser.add_argument("--bots-dir", default="hackathon/submitted_bots", help="Directory of submitted bots")
    parser.add_argument("--seed", default="PICT-FINALE-2026-SECRET", help="Tournament secret seed")
    parser.add_argument("--provisional", action="store_true", help="Run weekly provisional leaderboard mode")
    args = parser.parse_args()

    run_full_championship(bots_dir=args.bots_dir, secret_seed=args.seed, provisional=args.provisional)
