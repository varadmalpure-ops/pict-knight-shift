#!/usr/bin/env python3
"""
format_curriculum_text.py

Formats all 1048 text files in 'PICT Knight Shift Curriculum' with clean WhatsApp markdown
(*bold*, _italics_) without adding extra text, mentioning Elo, or mentioning club branding,
and adds a '_React with number_' instruction line after each question.
"""

import os
import re
import json
import glob
import send_daily_puzzle as sdp

BASE_DIR = "/Users/varadmalpure/foo/PICT Knight Shift"
CURRICULUM_DIR = os.path.join(BASE_DIR, "PICT Knight Shift Curriculum")
JSON_DIR = os.path.join(BASE_DIR, "curriculum")

OPT_PAT = re.compile(r'^([1-4]️⃣|🅐|🅑|🅒|🅓|🟥 [A-D]\))\s*(.*)$', re.MULTILINE)

# Load curriculum databases
with open(os.path.join(JSON_DIR, "puzzles_curriculum.json"), "r", encoding="utf-8") as f:
    puzzles_db = {it["id"]: it for items in json.load(f).values() for it in items}
with open(os.path.join(JSON_DIR, "traps_curriculum.json"), "r", encoding="utf-8") as f:
    traps_db = {it["id"]: it for items in json.load(f).values() for it in items}
with open(os.path.join(JSON_DIR, "blunders_curriculum.json"), "r", encoding="utf-8") as f:
    blunders_db = {it["id"]: it for items in json.load(f).values() for it in items}
with open(os.path.join(JSON_DIR, "endgames_curriculum.json"), "r", encoding="utf-8") as f:
    endgames_db = {it["id"]: it for items in json.load(f).values() for it in items}


def format_puzzle_caption(item, raw_text):
    options = OPT_PAT.findall(raw_text)
    side = "White" if item.get("turn") == "w" or " w " in item.get("fen", "") else "Black"
    opt_lines = [f"{emoji} *{txt.strip('*_ ')}*" for emoji, txt in options]
    return (
        f"*⚡ {side} to play: What is your move?*\n"
        f"_React with number_\n\n"
        + "\n".join(opt_lines)
    )


def format_puzzle_solution(item, raw_text):
    win_match = re.search(r'🎯\s*(?:\*Winning Move:\*|Winning Poll Choice:|\*Winning Poll Choice:\*)\s*(\S+)\s*(.*)', raw_text)
    win_emoji = win_match.group(1) if win_match else "🎯"
    win_move = win_match.group(2).strip("*_ ") if win_match else item.get("solution_san", "")

    fen = item.get("fen", "")
    sol_moves = item.get("solution_moves", [item.get("solution_uci")] if item.get("solution_uci") else [])

    try:
        seq_block = sdp.format_solution(fen, sol_moves) if sol_moves else f"1. *{win_move}*"
    except Exception:
        seq_block = f"1. *{win_move}*"

    explanation = item.get("explanation", "").strip()
    exp_line = f"\n\n📝 *Breakdown:* _{explanation}_" if explanation else ""

    return (
        f"*💡 SOLUTION REVEAL 💡*\n\n"
        f"🎯 *Winning Poll Choice:* {win_emoji} *{win_move}*\n\n"
        f"*🎬 Winning Sequence:*\n"
        f"{seq_block}"
        f"{exp_line}"
    )


def format_trap_caption(item, raw_text):
    options = OPT_PAT.findall(raw_text)
    side = "White" if item.get("turn") == "w" or " w " in item.get("fen", "") else "Black"
    opening = item.get("opening", "Opening Line")
    opt_lines = [f"{emoji} *{txt.strip('*_ ')}*" for emoji, txt in options]
    return (
        f"🪤 *Opening Trap:* {opening}\n"
        f"*{side} to play: What is the winning tactical strike?*\n"
        f"_React with number_\n\n"
        + "\n".join(opt_lines)
    )


def format_trap_solution(item, raw_text):
    win_match = re.search(r'(?:🎯 TRAP SOLUTION:|🎯 \*TRAP SOLUTION:\*|💥 \*Winning Strike:\*)\s*(\S+)\s*(.*)', raw_text)
    win_emoji = win_match.group(1) if win_match else "🎯"
    win_move = win_match.group(2).strip("*_ ") if win_match else item.get("solution_san", "")
    explanation = item.get("solution_explanation", "A decisive tactical blow wins material.").strip()

    return (
        f"🎯 *TRAP SOLUTION:* {win_emoji} *{win_move}*\n\n"
        f"📝 *Breakdown:* _{explanation}_"
    )


def format_blunder_caption(item, raw_text):
    options = OPT_PAT.findall(raw_text)
    turn = item.get("turn", "w")
    side = "White" if turn == "w" else "Black"
    opp_side = "Black" if side == "White" else "White"
    blunder_mv = item.get("blunder_move", "a blunder").strip("*` ")

    opt_lines = [f"{emoji} *{txt.strip('*_ ')}*" for emoji, txt in options]
    return (
        f"🤦 {opp_side} just played *{blunder_mv}* blundering in this position.\n"
        f"*{side} to play: How do you punish this blunder?*\n"
        f"_React with number_\n\n"
        + "\n".join(opt_lines)
    )


def format_blunder_solution(item, raw_text):
    win_match = re.search(r'(?:🔨 BLUNDER PUNISHMENT:|🔨 \*BLUNDER PUNISHMENT:\*|🎯 \*Punishing Move:\*)\s*(\S+)\s*(.*)', raw_text)
    win_emoji = win_match.group(1) if win_match else "🔨"
    win_move = win_match.group(2).strip("*_ ") if win_match else item.get("solution_san", "")

    turn = item.get("turn", "w")
    side = "White" if turn == "w" else "Black"
    opp_side = "Black" if side == "White" else "White"
    better_mv = item.get("better_move", "a safer move")
    explanation = f"{opp_side} should have played {better_mv} instead. {win_move} decisively punishes the mistake."

    return (
        f"🔨 *BLUNDER PUNISHMENT:* {win_emoji} *{win_move}*\n\n"
        f"📝 *Breakdown:* _{explanation}_"
    )


def format_endgame_caption(item, raw_text):
    options = OPT_PAT.findall(raw_text)
    turn = item.get("turn", "w")
    side = "White" if turn == "w" else "Black"
    opt_lines = [f"{emoji} *{txt.strip('*_ ')}*" for emoji, txt in options]
    return (
        f"*♟️ {side} to play: What is the crucial move?*\n"
        f"_React with number_\n\n"
        + "\n".join(opt_lines)
    )


def format_endgame_solution(item, raw_text):
    win_match = re.search(r'(?:🏆 ENDGAME TECHNIQUE:|🏆 \*ENDGAME TECHNIQUE:\*|🎯 \*Crucial Move:\*)\s*(\S+)\s*(.*)', raw_text)
    win_emoji = win_match.group(1) if win_match else "🏆"
    win_move = win_match.group(2).strip("*_ ") if win_match else item.get("solution_san", "")
    explanation = item.get("solution_explanation", "Accurate king and pawn play converts the endgame.").strip()

    return (
        f"🏆 *ENDGAME TECHNIQUE:* {win_emoji} *{win_move}*\n\n"
        f"📝 *Master Rule:* _{explanation}_"
    )


def process_all_files():
    counts = {
        "puzzle_captions": 0,
        "puzzle_solutions": 0,
        "trap_captions": 0,
        "trap_solutions": 0,
        "blunder_captions": 0,
        "blunder_solutions": 0,
        "endgame_captions": 0,
        "endgame_solutions": 0,
    }

    # 1. Daily Puzzles
    for path in sorted(glob.glob(os.path.join(CURRICULUM_DIR, "Month_*/1_Daily_Puzzles/*.txt"))):
        bn = os.path.basename(path)
        m = re.match(r'^Day_(\d+)_(m\d+_p\d+)_(caption|solution)\.txt$', bn)
        if not m:
            continue
        item_id = m.group(2)
        kind = m.group(3)
        item = puzzles_db[item_id]

        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()

        if kind == "caption":
            new_text = format_puzzle_caption(item, raw)
            counts["puzzle_captions"] += 1
        else:
            new_text = format_puzzle_solution(item, raw)
            counts["puzzle_solutions"] += 1

        with open(path, "w", encoding="utf-8") as f:
            f.write(new_text)

    # 2. Opening Traps
    for path in sorted(glob.glob(os.path.join(CURRICULUM_DIR, "Month_*/2_Opening_Traps/*.txt"))):
        bn = os.path.basename(path)
        m = re.match(r'^Trap_(\d+)_(trap_m\d+_\d+)_(caption|solution)\.txt$', bn)
        if not m:
            continue
        item_id = m.group(2)
        kind = m.group(3)
        item = traps_db[item_id]

        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()

        if kind == "caption":
            new_text = format_trap_caption(item, raw)
            counts["trap_captions"] += 1
        else:
            new_text = format_trap_solution(item, raw)
            counts["trap_solutions"] += 1

        with open(path, "w", encoding="utf-8") as f:
            f.write(new_text)

    # 3. Blunder Punishments
    for path in sorted(glob.glob(os.path.join(CURRICULUM_DIR, "Month_*/3_Blunder_Punishments/*.txt"))):
        bn = os.path.basename(path)
        m = re.match(r'^Blunder_(\d+)_(blunder_m\d+_\d+)_(caption|solution)\.txt$', bn)
        if not m:
            continue
        item_id = m.group(2)
        kind = m.group(3)
        item = blunders_db[item_id]

        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()

        if kind == "caption":
            new_text = format_blunder_caption(item, raw)
            counts["blunder_captions"] += 1
        else:
            new_text = format_blunder_solution(item, raw)
            counts["blunder_solutions"] += 1

        with open(path, "w", encoding="utf-8") as f:
            f.write(new_text)

    # 4. Endgame Skills
    for path in sorted(glob.glob(os.path.join(CURRICULUM_DIR, "Month_*/4_Endgame_Skills/*.txt"))):
        bn = os.path.basename(path)
        m = re.match(r'^Endgame_(\d+)_(endgame_m\d+_\d+)_(caption|solution)\.txt$', bn)
        if not m:
            continue
        item_id = m.group(2)
        kind = m.group(3)
        item = endgames_db[item_id]

        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()

        if kind == "caption":
            new_text = format_endgame_caption(item, raw)
            counts["endgame_captions"] += 1
        else:
            new_text = format_endgame_solution(item, raw)
            counts["endgame_solutions"] += 1

        with open(path, "w", encoding="utf-8") as f:
            f.write(new_text)

    return counts


if __name__ == "__main__":
    print("[*] Formatting all text files in PICT Knight Shift Curriculum...")
    c = process_all_files()
    total = sum(c.values())
    print(f"[✓] Successfully formatted {total} files:")
    for k, v in c.items():
        print(f"    - {k}: {v}")
