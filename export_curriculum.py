#!/usr/bin/env python3
"""
export_curriculum.py - Generates the complete 1-Year Curriculum into organized
local folders ready for batch Google Drive upload and instant mobile access.
"""

import os
import sys
import json
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

import send_daily_puzzle as sdp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_EXPORT_NAME = "PICT Knight Shift Curriculum" if os.path.exists(os.path.join(BASE_DIR, "PICT Knight Shift Curriculum")) else "exported_curriculum"
EXPORT_DIR = os.path.join(BASE_DIR, DEFAULT_EXPORT_NAME)


FIXED_IDS = {
    'm02_p73461', 'm02_p72928', 'm03_p63168', 'm03_p61978', 'm03_p74865',
    'm04_p69979', 'm05_p70920', 'm08_p19269', 'm09_p83278', 'm09_p62796',
    'm09_p15632', 'm11_p2861', 'trap_m07_61474', 'blunder_m07_63571',
    'blunder_m07_27882', 'blunder_m12_74248', 'endgame_m09_15632'
}


def load_curriculum(filename):
    with open(os.path.join(BASE_DIR, "curriculum", filename), "r", encoding="utf-8") as f:
        return json.load(f)


def export_puzzle_item(item, idx, folder, generate_gif=True, overwrite=False):
    day_num = idx + 1
    prefix = f"Day_{day_num:02d}_{item['id']}"
    fen = item["fen"]
    last_move_uci = item.get("last_move_uci")
    turn = "w" if " w " in fen else "b"
    side_to_move = "White" if turn == "w" else "Black"
    flip_param = "&flip=true" if turn == "b" else ""
    encoded_fen = urllib.parse.quote(fen)
    image_url = f"https://www.chess.com/dynboard?fen={encoded_fen}&size=3{flip_param}"

    sol_moves = item.get("solution_moves", item.get("solution", []))
    best_move_uci = item.get("solution_uci") or (sol_moves[0] if sol_moves else "")

    # Generate poll choices
    poll_options, correct_emoji, correct_label, poll_caption, _ = sdp.generate_poll_options(fen, best_move_uci)

    # Caption (Brief WhatsApp formatted)
    caption = (
        f"*⚡ {side_to_move} to play: What is your move?*\n"
        f"_React with number_\n\n"
        f"{poll_caption}"
    )

    # Solution text
    winning_san = item.get("solution_san", "")
    if not winning_san:
        for opt in poll_options:
            if opt["is_correct"]:
                winning_san = opt["san"]
                break

    try:
        sol_breakdown = sdp.format_solution(fen, sol_moves) if sol_moves else f"1. *{winning_san}*"
    except Exception:
        sol_breakdown = "\n".join([f"{i+1}. *{mv}*" for i, mv in enumerate(sol_moves)]) if sol_moves else f"1. *{winning_san}*"

    explanation = item.get("explanation", "").strip()
    exp_line = f"\n\n📝 *Breakdown:* _{explanation}_" if explanation else ""

    solution_text = (
        f"*💡 SOLUTION REVEAL 💡*\n\n"
        f"🎯 *Winning Poll Choice:* {correct_emoji} *{winning_san}*\n\n"
        f"*🎬 Winning Sequence:*\n{sol_breakdown}"
        f"{exp_line}"
    )

    # Save board image (re-download if missing, overwrite requested, or fixed illegal last move)
    img_path = os.path.join(folder, f"{prefix}_board.png")
    if overwrite or item.get("id") in FIXED_IDS or not os.path.exists(img_path):
        sdp.download_image(image_url, save_path=img_path, fen=fen, last_move_uci=last_move_uci)

    with open(os.path.join(folder, f"{prefix}_caption.txt"), "w", encoding="utf-8") as f:
        f.write(caption)

    # Ensure no poll file exists
    poll_path = os.path.join(folder, f"{prefix}_poll.txt")
    if os.path.exists(poll_path):
        try:
            os.remove(poll_path)
        except Exception:
            pass

    with open(os.path.join(folder, f"{prefix}_solution.txt"), "w", encoding="utf-8") as f:
        f.write(solution_text)

    # Save animated GIF solution ONLY if solution has more than 1 move
    gif_path = os.path.join(folder, f"{prefix}_solution.gif")
    if generate_gif and len(sol_moves) > 1:
        if overwrite or not os.path.exists(gif_path):
            sdp.generate_solution_animation(fen, sol_moves, save_path=gif_path)
    else:
        if os.path.exists(gif_path):
            try:
                os.remove(gif_path)
            except Exception:
                pass

    return f"Puzzle Day {day_num:02d}"


def export_trap_item(item, idx, folder, generate_gif=True, overwrite=False):
    num = idx + 1
    prefix = f"Trap_{num:02d}_{item['id']}"
    fen = item["fen"]
    last_move_uci = item.get("last_move_uci")
    turn = item.get("turn", "w")
    side_to_move = "White" if turn == "w" else "Black"
    flip_param = "&flip=true" if turn == "b" else ""
    encoded_fen = urllib.parse.quote(fen)
    image_url = f"https://www.chess.com/dynboard?fen={encoded_fen}&size=3{flip_param}"

    poll_options, correct_emoji, correct_label, poll_caption, _ = sdp.generate_poll_options(fen, item["solution_uci"])
    opening_name = item.get("opening", "Opening Line")
    explanation = item.get("solution_explanation", "A decisive tactical blow wins material.").strip()

    caption = (
        f"🪤 *Opening Trap:* {opening_name}\n"
        f"*{side_to_move} to play: What is the winning tactical strike?*\n"
        f"_React with number_\n\n"
        f"{poll_caption}"
    )

    solution_text = (
        f"🎯 *TRAP SOLUTION:* {correct_emoji} *{item['solution_san']}*\n\n"
        f"📝 *Breakdown:* _{explanation}_"
    )

    img_path = os.path.join(folder, f"{prefix}_board.png")
    if os.path.exists(img_path):
        try:
            os.remove(img_path)
        except Exception:
            pass

    with open(os.path.join(folder, f"{prefix}_caption.txt"), "w", encoding="utf-8") as f:
        f.write(caption)

    poll_path = os.path.join(folder, f"{prefix}_poll.txt")
    if os.path.exists(poll_path):
        try:
            os.remove(poll_path)
        except Exception:
            pass

    with open(os.path.join(folder, f"{prefix}_solution.txt"), "w", encoding="utf-8") as f:
        f.write(solution_text)

    # Extra animated GIF showing how the position was reached starting from Move 1!
    if generate_gif:
        opening_gif_path = os.path.join(folder, f"{prefix}_opening.gif")
        moves_start = item.get("moves_from_start", [])
        if moves_start and (overwrite or not os.path.exists(opening_gif_path)):
            sdp.generate_opening_animation(moves_start, save_path=opening_gif_path, final_turn=turn, trap_name=item.get("name"))

    # Traps have 1-move solutions -> remove any stray _solution.gif
    sol_gif_path = os.path.join(folder, f"{prefix}_solution.gif")
    if os.path.exists(sol_gif_path):
        try:
            os.remove(sol_gif_path)
        except Exception:
            pass

    return f"Trap {num:02d}"


def export_blunder_item(item, idx, folder, generate_gif=True, overwrite=False):
    num = idx + 1
    prefix = f"Blunder_{num:02d}_{item['id']}"
    fen = item["fen"]
    last_move_uci = item.get("last_move_uci")
    turn = item.get("turn", "w")
    side_to_move = "White" if turn == "w" else "Black"
    opp_side = "Black" if side_to_move == "White" else "White"
    flip_param = "&flip=true" if turn == "b" else ""
    encoded_fen = urllib.parse.quote(fen)
    image_url = f"https://www.chess.com/dynboard?fen={encoded_fen}&size=3{flip_param}"

    poll_options, correct_emoji, correct_label, poll_caption, _ = sdp.generate_poll_options(fen, item["solution_uci"])
    blunder_mv = item.get("blunder_move", "a blunder").strip("*` ")
    better_mv = item.get("better_move", "a safer move")

    caption = (
        f"🤦 {opp_side} just played *{blunder_mv}* blundering in this position.\n"
        f"*{side_to_move} to play: How do you punish this blunder?*\n"
        f"_React with number_\n\n"
        f"{poll_caption}"
    )

    solution_text = (
        f"🔨 *BLUNDER PUNISHMENT:* {correct_emoji} *{item['solution_san']}*\n\n"
        f"📝 *Breakdown:* _{opp_side} should have played {better_mv} instead. {item['solution_san']} decisively punishes the mistake._"
    )

    img_path = os.path.join(folder, f"{prefix}_board.png")
    if overwrite or item.get("id") in FIXED_IDS or not os.path.exists(img_path):
        sdp.download_image(image_url, save_path=img_path, fen=fen, last_move_uci=last_move_uci)

    with open(os.path.join(folder, f"{prefix}_caption.txt"), "w", encoding="utf-8") as f:
        f.write(caption)

    poll_path = os.path.join(folder, f"{prefix}_poll.txt")
    if os.path.exists(poll_path):
        try:
            os.remove(poll_path)
        except Exception:
            pass

    with open(os.path.join(folder, f"{prefix}_solution.txt"), "w", encoding="utf-8") as f:
        f.write(solution_text)

    # Blunders have 1-move solutions -> no GIF
    gif_path = os.path.join(folder, f"{prefix}_solution.gif")
    if os.path.exists(gif_path):
        try:
            os.remove(gif_path)
        except Exception:
            pass

    return f"Blunder {num:02d}"


def export_endgame_item(item, idx, folder, generate_gif=True, overwrite=False):
    num = idx + 1
    prefix = f"Endgame_{num:02d}_{item['id']}"
    fen = item["fen"]
    last_move_uci = item.get("last_move_uci")
    turn = item.get("turn", "w")
    side_to_move = "White" if turn == "w" else "Black"
    flip_param = "&flip=true" if turn == "b" else ""
    encoded_fen = urllib.parse.quote(fen)
    image_url = f"https://www.chess.com/dynboard?fen={encoded_fen}&size=3{flip_param}"

    poll_options, correct_emoji, correct_label, poll_caption, _ = sdp.generate_poll_options(fen, item["solution_uci"])

    explanation = item.get("solution_explanation", "Accurate king and pawn play converts the endgame.").strip()

    caption = (
        f"*♟️ {side_to_move} to play: What is the crucial move?*\n"
        f"_React with number_\n\n"
        f"{poll_caption}"
    )

    solution_text = (
        f"🏆 *ENDGAME TECHNIQUE:* {correct_emoji} *{item['solution_san']}*\n\n"
        f"📝 *Master Rule:* _{explanation}_"
    )

    img_path = os.path.join(folder, f"{prefix}_board.png")
    if overwrite or item.get("id") in FIXED_IDS or not os.path.exists(img_path):
        sdp.download_image(image_url, save_path=img_path, fen=fen, last_move_uci=last_move_uci)

    with open(os.path.join(folder, f"{prefix}_caption.txt"), "w", encoding="utf-8") as f:
        f.write(caption)

    poll_path = os.path.join(folder, f"{prefix}_poll.txt")
    if os.path.exists(poll_path):
        try:
            os.remove(poll_path)
        except Exception:
            pass

    with open(os.path.join(folder, f"{prefix}_solution.txt"), "w", encoding="utf-8") as f:
        f.write(solution_text)

    # Endgames have 1-move solutions -> no GIF
    gif_path = os.path.join(folder, f"{prefix}_solution.gif")
    if os.path.exists(gif_path):
        try:
            os.remove(gif_path)
        except Exception:
            pass

    return f"Endgame {num:02d}"


def export_single_month(month_num, puzzles_db, traps_db, blunders_db, endgames_db, max_workers=8, generate_gif=True, overwrite=False):
    m_info = sdp.CURRICULUM_MONTH_INFO.get(month_num, {})
    m_theme = m_info.get("theme", f"Month_{month_num}").replace(" ", "_")
    m_range = m_info.get("range", "Mastery").replace(" ", "_").replace("–", "-")
    month_folder_name = f"Month_{month_num:02d}_{m_theme}_{m_range}_Elo"
    month_folder = os.path.join(EXPORT_DIR, month_folder_name)

    folder_puzzles = os.path.join(month_folder, "1_Daily_Puzzles")
    folder_traps = os.path.join(month_folder, "2_Opening_Traps")
    folder_blunders = os.path.join(month_folder, "3_Blunder_Punishments")
    folder_endgames = os.path.join(month_folder, "4_Endgame_Skills")

    for f_dir in [folder_puzzles, folder_traps, folder_blunders, folder_endgames]:
        os.makedirs(f_dir, exist_ok=True)

    m_key = f"month_{month_num}"
    p_items = puzzles_db.get(m_key, [])
    t_items = traps_db.get(m_key, [])
    b_items = blunders_db.get(m_key, [])
    e_items = endgames_db.get(m_key, [])

    valid_trap_prefixes = set(f"Trap_{idx+1:02d}_{it['id']}" for idx, it in enumerate(t_items))
    for fname in os.listdir(folder_traps):
        if not any(fname.startswith(vp) for vp in valid_trap_prefixes):
            try:
                os.remove(os.path.join(folder_traps, fname))
            except Exception:
                pass

    print(f"\n[*] Exporting Month {month_num:02d} ({len(p_items)} puzzles, {len(t_items)} traps, {len(b_items)} blunders, {len(e_items)} endgames)...")
    if generate_gif:
        print("    [+] Generating animated GIF solutions (_solution.gif)...")

    tasks = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for idx, item in enumerate(p_items):
            tasks.append(executor.submit(export_puzzle_item, item, idx, folder_puzzles, generate_gif, overwrite))
        for idx, item in enumerate(t_items):
            tasks.append(executor.submit(export_trap_item, item, idx, folder_traps, generate_gif, overwrite))
        for idx, item in enumerate(b_items):
            tasks.append(executor.submit(export_blunder_item, item, idx, folder_blunders, generate_gif, overwrite))
        for idx, item in enumerate(e_items):
            tasks.append(executor.submit(export_endgame_item, item, idx, folder_endgames, generate_gif, overwrite))

        completed = 0
        total = len(tasks)
        for fut in as_completed(tasks):
            try:
                fut.result()
                completed += 1
                if completed % 10 == 0 or completed == total:
                    print(f"    Progress: {completed}/{total} items processed...")
            except Exception as e:
                print(f"[!] Error exporting item: {e}")

    print(f"[✓] Month {month_num:02d} exported to: {month_folder}")
    return month_folder


def export_all_months(start_month=1, end_month=12, max_workers=8, generate_gif=True, overwrite=False):
    os.makedirs(EXPORT_DIR, exist_ok=True)
    puzzles_db = load_curriculum("puzzles_curriculum.json")
    traps_db = load_curriculum("traps_curriculum.json")
    blunders_db = load_curriculum("blunders_curriculum.json")
    endgames_db = load_curriculum("endgames_curriculum.json")

    print("=" * 65)
    print(f"  📦 EXPORTING COMPLETE 1-YEAR CURRICULUM (Months {start_month} to {end_month})")
    print("=" * 65)
    print(f"Target Directory: {EXPORT_DIR}")
    print(f"Animated GIF Solutions: {'Enabled (_solution.gif)' if generate_gif else 'Disabled'}")

    for m in range(start_month, end_month + 1):
        export_single_month(m, puzzles_db, traps_db, blunders_db, endgames_db, max_workers=max_workers, generate_gif=generate_gif, overwrite=overwrite)

    print("\n" + "=" * 65)
    print("  ✅ 1-YEAR CURRICULUM EXPORT FINISHED")
    print("=" * 65)
    print(f"Target Directory: {EXPORT_DIR}")
    print("All challenges include board coordinates, side-to-play banner, and club pill tag.")
    print("All challenges include animated solution GIFs (_solution.gif) and poll options ready for WhatsApp!\n")


def main():
    args = sys.argv[1:]
    generate_gif = "--no-gif" not in args
    overwrite = "--overwrite" in args or "--force" in args
    workers = 8

    # Extract flags and remaining positional arguments
    pos_args = []
    i = 0
    while i < len(args):
        a = args[i]
        if a in ["--workers", "-w"] and i + 1 < len(args) and args[i + 1].isdigit():
            workers = int(args[i + 1])
            i += 2
        elif a.startswith("--workers="):
            workers = int(a.split("=")[1])
            i += 1
        elif a.startswith("-"):
            i += 1
        else:
            pos_args.append(a)
            i += 1

    numeric_args = [int(a) for a in pos_args if a.isdigit()]
    cleaned_args = [a.lower() for a in pos_args if not a.isdigit()]

    puzzles_db = load_curriculum("puzzles_curriculum.json")
    traps_db = load_curriculum("traps_curriculum.json")
    blunders_db = load_curriculum("blunders_curriculum.json")
    endgames_db = load_curriculum("endgames_curriculum.json")

    if "gifs" in cleaned_args or "gif" in cleaned_args:
        print("[*] Generating missing animated GIF solutions across curriculum...")
        target_month = numeric_args[0] if numeric_args else None
        if target_month:
            export_single_month(target_month, puzzles_db, traps_db, blunders_db, endgames_db, max_workers=workers, generate_gif=True, overwrite=overwrite)
        else:
            export_all_months(start_month=1, end_month=12, max_workers=workers, generate_gif=True, overwrite=overwrite)
    elif numeric_args:
        target_month = numeric_args[0]
        export_single_month(target_month, puzzles_db, traps_db, blunders_db, endgames_db, max_workers=workers, generate_gif=generate_gif, overwrite=overwrite)
    else:
        export_all_months(start_month=1, end_month=12, max_workers=workers, generate_gif=generate_gif, overwrite=overwrite)


if __name__ == "__main__":
    main()
