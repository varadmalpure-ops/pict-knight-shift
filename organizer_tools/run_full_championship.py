"""
PICT KNIGHT SHIFT // SOLO-ORGANIZER MASTER TOURNAMENT RUNNER
File: organizer_tools/run_full_championship.py

One-click automated evaluation for the entire hackathon:
  1. Audits every submission in `hackathon/submitted_bots/` with the AST Security Scanner.
  2. Runs the Hidden Challenge Suite (Chess960, endgames, tactics, bullet) -> 20 Pts.
  3. Runs the Calibrated Reference Gauntlet (1000, 1500, 2000 Elo) -> 10 Pts.
  4. Runs the Main Arena Tournament (Paired balanced openings) -> 70 Pts.
  5. Computes final 100-Point standings and awards (Grandmaster, Giant Slayer, Iron Bastion, Tactical Maestro).
  6. Exports the final formatted Markdown leaderboard.
"""

import sys
import os
import glob
import time
import argparse
import chess

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from hackathon.security import audit_bot_source
from organizer_tools.challenge_generator import ChallengeSuite
from organizer_tools.run_gauntlet import run_gauntlet
from hackathon.arena_runner import run_arena, ArenaManager


def run_full_championship(bots_dir: str = "hackathon/submitted_bots", secret_seed: str = "PICT-FINALE-2026-SECRET"):
    print("=" * 76)
    print("🏆 PICT KNIGHT SHIFT // MASTER AUTOMATED CHAMPIONSHIP RUNNER")
    print("=" * 76)
    print(f"Target Bot Directory: {bots_dir}")
    print(f"Cryptographic Seed:   {secret_seed}\n")

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
        print("\n⚠️ Need at least 2 eligible bots to run championship. Add more bots to submitted_bots/.")
        return

    scores = {os.path.splitext(os.path.basename(b))[0]: {"challenge": 0.0, "gauntlet": 0.0, "arena": 0.0, "total": 0.0, "path": b} for b in eligible_bots}

    # 2. Run Hidden Challenge Suite (20 Points)
    print("\n" + "=" * 76)
    print("🧩 STAGE 1: HIDDEN CHALLENGE SUITE (20 POINTS)")
    print("=" * 76)
    suite = ChallengeSuite(master_seed=secret_seed)
    for b_path in eligible_bots:
        name = os.path.splitext(os.path.basename(b_path))[0]
        print(f"Evaluating {name} on 18 challenge puzzles...")
        raw_score, _ = suite.evaluate_bot(b_path)
        # Scale 100-pt challenge suite to 20 points
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
        est_elo, tier_results = run_gauntlet(b_path, pairs_per_tier=1, time_limit=0.5)
        if tier_results:
            # 6 games total (2 vs 1000, 2 vs 1500, 2 vs 2000). Max pts = 6.0
            tot_raw = sum(t["score"] for t in tier_results.values())
            # Scale 6.0 to 10 points
            pts_10 = (tot_raw / 6.0) * 10.0
            scores[name]["gauntlet"] = round(pts_10, 2)
            scores[name]["est_elo"] = est_elo
            scores[name]["vs_2000"] = tier_results[2000]["score"]
        else:
            scores[name]["gauntlet"] = 0.0
            scores[name]["est_elo"] = 0
            scores[name]["vs_2000"] = 0.0

    # 4. Run Main Arena Tournament (70 Points)
    print("\n" + "=" * 76)
    print("🥊 STAGE 3: MAIN TOURNAMENT ARENA (70 POINTS)")
    print("=" * 76)
    mgr = ArenaManager(eligible_bots, games_per_pair=2, time_limit=0.5, secret_seed=secret_seed)
    mgr.run_round_robin()

    # Scale arena points to 70
    max_possible_arena_pts = (len(eligible_bots) - 1) * 2.0
    for name in scores:
        rec = mgr.results.get(name, {"points": 0.0})
        arena_raw = rec["points"]
        pts_70 = (arena_raw / max_possible_arena_pts) * 70.0 if max_possible_arena_pts > 0 else 0.0
        scores[name]["arena"] = round(pts_70, 2)
        scores[name]["wins"] = rec.get("wins", 0)
        scores[name]["forfeits"] = rec.get("forfeits", 0)
        scores[name]["total"] = round(scores[name]["challenge"] + scores[name]["gauntlet"] + scores[name]["arena"], 2)

    # 5. Final Standings
    ranked = sorted(scores.items(), key=lambda item: (item[1]["total"], item[1]["arena"], item[1]["wins"]), reverse=True)

    print("\n" + "=" * 76)
    print("🏆 FINAL CHAMPIONSHIP LEADERBOARD (100-POINT MATRIX)")
    print("=" * 76)
    print(f"{'Rank':<5} | {'Bot Name':<20} | {'Arena (70)':<10} | {'Suite (20)':<10} | {'Gaunt (10)':<10} | {'Total':<8} | {'Est. Elo'}")
    print("-" * 76)

    for rank, (name, d) in enumerate(ranked, start=1):
        print(f"#{rank:<4} | {name:<20} | {d['arena']:<10.2f} | {d['challenge']:<10.2f} | {d['gauntlet']:<10.2f} | {d['total']:<8.2f} | ~{d.get('est_elo', 'N/A')}")

    champion = ranked[0][0]
    print("\n" + "=" * 76)
    print(f"👑 CAMPUS GRANDMASTER: {champion} ({ranked[0][1]['total']:.2f} pts)!")

    # Check Giant Slayer
    giant_slayers = [name for name, d in scores.items() if d.get("vs_2000", 0) > 0]
    if giant_slayers:
        print(f"⚔️ GIANT SLAYER WINNER(S): {', '.join(giant_slayers)} (Scored vs 2000 Elo reference!)")
    else:
        print("⚔️ GIANT SLAYER: None qualified (The 2000 Elo reference remains undefeated)")

    # Check Iron Bastion
    iron_bastion = min(scores.items(), key=lambda item: item[1].get("forfeits", 0))[0]
    print(f"🛡️ IRON BASTION: {iron_bastion} (Lowest blunder/timeout forfeit rate)")

    # Check Tactical Maestro
    maestro = max(scores.items(), key=lambda item: item[1]["challenge"])[0]
    print(f"⚡ TACTICAL MAESTRO: {maestro} ({scores[maestro]['challenge']:.2f}/20 pts on challenge puzzles)")
    print("=" * 76)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PICT Knight Shift Solo-Organizer Tournament Runner")
    parser.add_argument("--bots-dir", default="hackathon/submitted_bots", help="Directory of submitted bots")
    parser.add_argument("--seed", default="PICT-FINALE-2026-SECRET", help="Tournament secret seed")
    args = parser.parse_args()

    run_full_championship(bots_dir=args.bots_dir, secret_seed=args.seed)
