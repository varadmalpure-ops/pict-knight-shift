#!/usr/bin/env python3
"""
PICT Chess Club Daily Puzzle & 1-Year Mastery Curriculum Dispatcher.
Custom-designed for club members starting from 500 Elo and increasing by +100 Elo
each month over 1 full year (52 weeks / 12 months) without repeating:
- Month 1:  500-600 Elo (Novice Fundamentals)
- Month 2:  600-700 Elo (Beginner Tactics & Forks)
- Month 3:  700-800 Elo (Pins, Skewers & Back Ranks)
- Month 4:  800-900 Elo (Double Checks & Deflection)
- Month 5:  900-1000 Elo (Smothered Mates & Sacrifices)
- Month 6:  1000-1100 Elo (4-Digit Combinations)
- Month 7:  1100-1200 Elo (Interference & Clearance)
- Month 8:  1200-1300 Elo (Deep Tactical Calculation)
- Month 9:  1300-1400 Elo (Positional Sacrifices & Mating Nets)
- Month 10: 1400-1500 Elo (Complex Combinations)
- Month 11: 1500-1600 Elo (Master Level Calculation)
- Month 12: 1600-1700 Elo (Club Champion Tournament Mastery)
"""

import sys
import os
import io
import math
import random
import hashlib
import json
import time
import subprocess
import datetime
import threading
import urllib.request
import urllib.parse
import ssl
from PIL import Image, ImageDraw, ImageFont, ImageChops
import chess
import chess.pgn

# ==============================================================================
# 1. CONFIGURATION & PATHS
# ==============================================================================
PUZZLE_SEND_HOUR = 19
PUZZLE_SEND_MINUTE = 0
SOLUTION_SEND_HOUR = 7
SOLUTION_SEND_MINUTE = 0

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "last_puzzle_state.json")
DISPATCH_HISTORY_FILE = os.path.join(BASE_DIR, "dispatched_history.json")
CURRICULUM_DIR = os.path.join(BASE_DIR, "curriculum")

PAUSE_WEEKEND_PUZZLES = True

CURRICULUM_MONTH_INFO = {
    1: {"range": "500–600", "theme": "Novice Fundamentals", "tip": "Always scan the board for free unprotected pieces before moving!"},
    2: {"range": "600–700", "theme": "Beginner Tactics & Forks", "tip": "Knights and Queens are the best pieces for double-attacking two targets at once."},
    3: {"range": "700–800", "theme": "Pins, Skewers & Back Ranks", "tip": "A pinned piece cannot move—pile up pressure on it!"},
    4: {"range": "800–900", "theme": "Double Checks & Deflection", "tip": "Double check forces the King to move. Opponents cannot block or capture!"},
    5: {"range": "900–1000", "theme": "Smothered Mates & Sacrifices", "tip": "Sacrificing a piece to drag the enemy King into the open leads to fast checkmates."},
    6: {"range": "1000–1100", "theme": "4-Digit Combinations", "tip": "Calculate 2-3 moves ahead and anticipate opponent defensive tries."},
    7: {"range": "1100–1200", "theme": "Interference & Clearance", "tip": "Clear out lines and diagonals for your heavy pieces to dominate."},
    8: {"range": "1200–1300", "theme": "Deep Tactical Calculation", "tip": "Look for quiet non-checking candidate moves that create unstoppable threats."},
    9: {"range": "1300–1400", "theme": "Positional Sacrifices & Mating Nets", "tip": "Coordinate your pieces to surround the opponent's escape squares."},
    10: {"range": "1400–1500", "theme": "Complex Combinations", "tip": "Look for multiple motifs working together (e.g., pin + deflection)."},
    11: {"range": "1500–1600", "theme": "Master Level Calculation", "tip": "Precision calculation and eliminating counterplay turn advantages into wins."},
    12: {"range": "1600–1700", "theme": "Club Champion Tournament Mastery", "tip": "Trust your calculation, play actively, and seize the tactical initiative!"}
}

# ==============================================================================
# 2. DISPATCH HISTORY & 1-YEAR CURRICULUM STATE
# ==============================================================================
def load_dispatch_history():
    """Loads historical tracking of dispatched items and current curriculum month."""
    default_history = {
        "current_month": 1,
        "start_date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "dispatched_puzzles": [],
        "dispatched_traps": [],
        "dispatched_blunders": [],
        "dispatched_endgames": [],
        "recent_correct_labels": [],
        "poll_style": "numbers"
    }
    if os.path.exists(DISPATCH_HISTORY_FILE):
        try:
            with open(DISPATCH_HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {**default_history, **data}
        except Exception:
            pass
    return default_history


def save_dispatch_history(history):
    history["last_updated"] = datetime.datetime.now().isoformat()
    with open(DISPATCH_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)


def set_current_month(month_num):
    """Sets the active curriculum month (1-12)."""
    if month_num < 1 or month_num > 12:
        print(f"[!] Invalid month: {month_num}. Must be between 1 and 12.")
        return
    history = load_dispatch_history()
    history["current_month"] = month_num
    save_dispatch_history(history)
    info = CURRICULUM_MONTH_INFO.get(month_num, {})
    print(f"[✓] Active Curriculum Month set to Month {month_num} ({info.get('range', '')} Elo) — {info.get('theme', '')}!")


def set_poll_style(style_name):
    """Sets poll badge style: 'numbers' (1️⃣ 2️⃣ 3️⃣ 4️⃣ - default) or 'letters' (🅐 🅑 🅒 🅓) or 'red' (🟥 A) 🟥 B))."""
    valid_map = {
        "numbers": "numbers",
        "number": "numbers",
        "keycaps": "numbers",
        "keycap": "numbers",
        "digits": "numbers",
        "letters": "letters",
        "letter": "letters",
        "red": "red"
    }
    key = style_name.lower().strip()
    if key not in valid_map:
        print(f"[!] Invalid style '{style_name}'. Valid options: numbers, letters, red")
        return
    canonical = valid_map[key]
    history = load_dispatch_history()
    history["poll_style"] = canonical
    save_dispatch_history(history)
    sample_badges = {
        "numbers": "1️⃣ 2️⃣ 3️⃣ 4️⃣ (Numbers inside emoji buttons — default, instant WhatsApp reactions)",
        "letters": "🅐 🅑 🅒 🅓 (Letters inside solid badges)",
        "red": "🟥 A) 🟥 B) 🟥 C) 🟥 D) (Red square badges)"
    }
    print(f"[✓] Poll Option Style set to '{canonical}': {sample_badges[canonical]}")


def reset_dispatch_history():
    """Resets all history pools and resets curriculum back to Month 1."""
    history = {
        "current_month": 1,
        "start_date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "dispatched_puzzles": [],
        "dispatched_traps": [],
        "dispatched_blunders": [],
        "dispatched_endgames": [],
        "recent_correct_labels": [],
        "poll_style": "numbers",
        "last_updated": datetime.datetime.now().isoformat()
    }
    with open(DISPATCH_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)
    print("[✓] 1-Year Curriculum history reset to Month 1 (500–600 Elo) successfully!")


def load_curriculum_file(filename):
    """Loads a curriculum JSON database file."""
    filepath = os.path.join(CURRICULUM_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    print(f"[!] Warning: Curriculum file {filepath} not found!")
    return {}


def get_next_curriculum_item(filename, history_key, requested_id=None):
    """
    Retrieves the next progressive item from the active month tier.
    Automatically graduates to the next month (+100 Elo) when the current month is completed!
    """
    database = load_curriculum_file(filename)
    history = load_dispatch_history()
    current_month = history.get("current_month", 1)
    dispatched = set(history.get(history_key, []))

    month_key = f"month_{current_month}"
    month_items = database.get(month_key, [])

    if requested_id:
        for m_key, items in database.items():
            for item in items:
                if item["id"] == requested_id:
                    if requested_id not in history[history_key]:
                        history[history_key].append(requested_id)
                        save_dispatch_history(history)
                    return item

    remaining = [item for item in month_items if item["id"] not in dispatched]

    if not remaining:
        # Month finished! Graduate to next month!
        if current_month < 12:
            new_month = current_month + 1
            history["current_month"] = new_month
            info = CURRICULUM_MONTH_INFO.get(new_month, {})
            print("\n" + "=" * 65)
            print(f"  🎉🎓 CLUB LEVEL UP! ADVANCING TO MONTH {new_month} ({info.get('range', '')} Elo) 🎓🎉")
            print(f"  Theme: {info.get('theme', '')}")
            print("=" * 65 + "\n")
            month_key = f"month_{new_month}"
            month_items = database.get(month_key, [])
            remaining = [item for item in month_items if item["id"] not in dispatched]
        else:
            print("[*] Congratulations! 1-Year Curriculum completed (Month 12 reached)! Starting fresh cycle...")
            history[history_key] = []
            history["current_month"] = 1
            month_items = database.get("month_1", [])
            remaining = month_items

    selected_item = remaining[0] if remaining else month_items[0]

    if selected_item["id"] not in history[history_key]:
        history[history_key].append(selected_item["id"])
        save_dispatch_history(history)

    return selected_item


# ==============================================================================
# 3. WEEKLY TIMETABLE SCHEDULE
# ==============================================================================
WEEKLY_SCHEDULE = {
    "Monday": {
        "theme": "Trap Monday",
        "has_puzzle": True,
        "feature": "trap",
        "title": "Daily Tactical Puzzle (WhatsApp Poll) + Sneaky Opening Trap"
    },
    "Tuesday": {
        "theme": "Blunder Tuesday",
        "has_puzzle": True,
        "feature": "blunder",
        "title": "Daily Tactical Puzzle (WhatsApp Poll) + Blunder of the Day"
    },
    "Wednesday": {
        "theme": "Endgame Skills Wednesday",
        "has_puzzle": True,
        "feature": "endgame",
        "title": "Daily Tactical Puzzle (WhatsApp Poll) + Master Endgame Skills"
    },
    "Thursday": {
        "theme": "Blunder Thursday",
        "has_puzzle": True,
        "feature": "blunder",
        "title": "Daily Tactical Puzzle (WhatsApp Poll) + Blunder of the Day"
    },
    "Friday": {
        "theme": "Trap Friday",
        "has_puzzle": True,
        "feature": "trap",
        "title": "Daily Tactical Puzzle (WhatsApp Poll) + Sneaky Opening Trap"
    },
    "Saturday": {
        "theme": "Weekly Arena Tournament",
        "has_puzzle": False,
        "feature": "arena",
        "title": "Weekly Club Blitz/Rapid Arena Tournament on Lichess"
    },
    "Sunday": {
        "theme": "Tournament Recap & Awards",
        "has_puzzle": False,
        "feature": "recap",
        "title": "Tournament Results, Winners Podium, and Rating Awards"
    }
}


# ==============================================================================
# 4. POLL OPTIONS GENERATOR
# ==============================================================================
def generate_poll_options(fen, correct_uci):
    """
    Generates 4 candidate options (1 winning move + 3 plausible human distractors)
    for a WhatsApp poll. Returns (options, correct_emoji, correct_label, poll_caption, poll_creator_text).
    """
    try:
        board = chess.Board(fen)
        correct_move = chess.Move.from_uci(correct_uci)
        correct_san = board.san(correct_move)
        prefix = f"{board.fullmove_number}... " if board.turn == chess.BLACK else f"{board.fullmove_number}. "

        # Score legal moves to find the most tempting human distractors
        scored_distractors = []
        for m in board.legal_moves:
            if m == correct_move:
                continue
            san = board.san(m)
            score = 0
            if board.gives_check(m):
                score += 8
            if board.is_capture(m):
                score += 6
            piece = board.piece_at(m.from_square)
            if piece:
                if piece.piece_type == chess.QUEEN:
                    score += 4
                elif piece.piece_type in [chess.ROOK, chess.KNIGHT, chess.BISHOP]:
                    score += 2
            scored_distractors.append((score, san, m.uci()))

        scored_distractors.sort(key=lambda x: x[0], reverse=True)

        distractors = [d[1] for d in scored_distractors[:3]]
        all_legal_sans = [board.san(m) for m in board.legal_moves if m != correct_move]
        for s in all_legal_sans:
            if len(distractors) >= 3:
                break
            if s not in distractors:
                distractors.append(s)

        all_choices = [(correct_san, True)] + [(d, False) for d in distractors]

        history = load_dispatch_history()
        style = history.get("poll_style", "numbers")
        if style == "letters":
            emojis = ["🅐", "🅑", "🅒", "🅓"]
            labels = ["A", "B", "C", "D"]
        elif style == "red":
            emojis = ["🟥 A)", "🟥 B)", "🟥 C)", "🟥 D)"]
            labels = ["A", "B", "C", "D"]
        else:  # default "numbers" -> 1️⃣ 2️⃣ 3️⃣ 4️⃣ (Instant WhatsApp Emoji reactions!)
            emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
            labels = ["1", "2", "3", "4"]

        # Cryptographically secure unguessable shuffle using OS-level entropy
        sr = random.SystemRandom()
        sr.shuffle(all_choices)

        # Anti-streak protection: prevent the same winning option from occurring 3 times in a row
        recent_labels = history.get("recent_correct_labels", [])
        if len(recent_labels) >= 2 and recent_labels[-1] == recent_labels[-2]:
            banned_label = recent_labels[-1]
            for _ in range(25):
                corr_idx = [c[1] for c in all_choices].index(True)
                if labels[corr_idx] != banned_label:
                    break
                sr.shuffle(all_choices)

        options = []
        correct_emoji = emojis[0]
        correct_label = labels[0]

        caption_lines = []
        creator_lines = []

        turn_str = "Black" if board.turn == chess.BLACK else "White"
        creator_lines.append(f"Poll Question: ⚡ {turn_str} to move: What is your move?")

        for idx, (move_san, is_corr) in enumerate(all_choices):
            full_move_text = f"{prefix}{move_san}"
            emoji = emojis[idx]
            lbl = labels[idx]
            options.append({
                "emoji": emoji,
                "label": lbl,
                "san": move_san,
                "full_text": full_move_text,
                "is_correct": is_corr
            })
            if is_corr:
                correct_emoji = emoji
                correct_label = lbl

            caption_lines.append(f"{emoji} *{full_move_text}*")
            creator_lines.append(f"Option {idx + 1}: {emoji} {full_move_text}")

        # Record recent correct label to maintain anti-streak tracking
        recent_labels.append(correct_label)
        history["recent_correct_labels"] = recent_labels[-20:]
        save_dispatch_history(history)

        poll_caption = "\n".join(caption_lines)
        poll_creator_text = "\n".join(creator_lines)

        return options, correct_emoji, correct_label, poll_caption, poll_creator_text
    except Exception as e:
        print(f"[!] Warning generating poll options: {e}")
        return [], None, None, "", ""


def fetch_chesscom_daily_puzzle():
    """Fetches the official Puzzle of the Day from Chess.com public API."""
    url = "https://api.chess.com/pub/puzzle"
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) PICT-Chess-Club/1.0",
            "Accept": "application/json"
        }
    )
    with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def parse_chesscom_pgn(pgn_str):
    """Parses Chess.com PGN string into UCI move list and SAN move list."""
    if not pgn_str:
        return [], []
    try:
        game = chess.pgn.read_game(io.StringIO(pgn_str))
        if not game:
            return [], []
        board = game.board()
        uci_moves = []
        san_moves = []
        for move in game.mainline_moves():
            san_moves.append(board.san(move))
            uci_moves.append(move.uci())
            board.push(move)
        return uci_moves, san_moves
    except Exception as e:
        print(f"[!] Warning parsing PGN: {e}")
        return [], []


# ==============================================================================
# 5. PAYLOAD & IMAGE BUILDERS
# ==============================================================================
def generate_payload(target_day=None, puzzle_id=None, use_chesscom=False):
    """
    Builds the daily puzzle payload from the progressive 1-year curriculum.
    Starting at 500 Elo and increasing by +100 each month!
    """
    today = datetime.datetime.now().strftime("%A")
    day_str = target_day or today

    if use_chesscom:
        puzzle_data = None
        try:
            print("[*] Fetching Daily Puzzle from Chess.com API (https://api.chess.com/pub/puzzle)...")
            puzzle_data = fetch_chesscom_daily_puzzle()
        except Exception as e:
            print(f"[!] Warning: Failed to fetch Chess.com daily puzzle ({e}). Falling back to curriculum.")

        if puzzle_data and "fen" in puzzle_data:
            title = puzzle_data.get("title", "Tactical Challenge")
            url = puzzle_data.get("url", "")
            fen = puzzle_data["fen"]
            pgn = puzzle_data.get("pgn", "")
            solution, _ = parse_chesscom_pgn(pgn)
            puzzle_id = url.split("/")[-1] if url else str(puzzle_data.get("publish_time", "daily"))
            rating = puzzle_data.get("rating", 1500)
            hint = "Calculate forcing checks, captures, and piece coordination!"
            explanation = "Solid tactical calculation is required to crack this puzzle."
            tip = "Always check opponent replies before playing your move!"
            theme_str = "#tactics #chesscom"
            status_line = f"{day_str} Chess.com Daily Puzzle"
            month = 0
        else:
            use_chesscom = False

    if not use_chesscom:
        # Default: 1-Year Progressive Mastery Curriculum
        puzzle = get_next_curriculum_item("puzzles_curriculum.json", "dispatched_puzzles", requested_id=puzzle_id)
        puzzle_id = puzzle["id"]
        month = puzzle.get("month", 1)
        rating = puzzle["rating"]
        title = puzzle["title"]
        fen = puzzle["fen"]
        turn = puzzle["turn"]
        solution = puzzle.get("solution_moves", [puzzle["solution_uci"]])
        hint = puzzle.get("hint", "Look for undefended pieces and forcing checks!")
        explanation = puzzle.get("explanation", "")
        tip = puzzle.get("tip", "Always count attackers and defenders!")
        theme_str = f"#{puzzle['theme'].replace(' ', '')} #PICTChess"
        status_line = f"{day_str} • 1-Year Curriculum Month {month}/12"

    fen_parts = fen.split()
    turn = fen_parts[1].lower() if len(fen_parts) > 1 else "w"
    side_to_move = "White" if turn == "w" else "Black"
    flip_param = "&flip=true" if turn == "b" else ""
    encoded_fen = urllib.parse.quote(fen)
    image_url = f"https://www.chess.com/dynboard?fen={encoded_fen}&size=3{flip_param}"
    last_move_uci = puzzle.get("last_move_uci") if not use_chesscom else None

    poll_options, correct_emoji, correct_label, poll_caption, poll_creator_text = [], None, None, "", ""
    if fen and solution:
        poll_options, correct_emoji, correct_label, poll_caption, poll_creator_text = generate_poll_options(fen, solution[0])

    caption = (
        f"*⚡ {side_to_move} to play: What is your move?*\n"
        f"_React with number_\n\n"
        f"{poll_caption}"
    )

    return {
        "caption": caption,
        "title": title,
        "image_url": image_url,
        "puzzle_id": puzzle_id,
        "fen": fen,
        "last_move_uci": last_move_uci,
        "solution": solution,
        "month": month,
        "hint": hint,
        "explanation": explanation,
        "tip": tip,
        "poll_options": poll_options,
        "correct_emoji": correct_emoji,
        "correct_label": correct_label,
        "poll_creator_text": poll_creator_text,
        "difficulty_metadata": {
            "day": day_str,
            "month": month,
            "rating": rating,
            "theme": theme_str,
            "title": title
        }
    }


def annotate_board_image(raw_path, save_path, fen, last_move_uci=None):
    """
    Overlays on the chessboard:
    1. Crystal-clear board coordinates (a-h and 1-8) in large bold font.
    2. Clean header banner indicating 'WHITE TO PLAY' or 'BLACK TO PLAY' with color indicator disk.
    3. Warm yellow highlighted squares and directional arrow for the last played move!
    """
    try:
        im_board = Image.open(raw_path).convert("RGBA")
        sq_size = 90
        board_size = 720
        border_left = 44
        border_bottom = 44
        border_right = 16
        banner_top = 78

        total_w = border_left + board_size + border_right
        total_h = banner_top + board_size + border_bottom

        canvas = Image.new("RGBA", (total_w, total_h), (22, 26, 30, 255))
        draw = ImageDraw.Draw(canvas)

        board = chess.Board(fen)
        flipped = (board.turn == chess.BLACK)

        # Highlight last move if available
        if last_move_uci and len(last_move_uci) >= 4:
            try:
                from_sq = chess.parse_square(last_move_uci[:2])
                to_sq = chess.parse_square(last_move_uci[2:4])

                overlay = Image.new("RGBA", (board_size, board_size), (0, 0, 0, 0))
                ov_draw = ImageDraw.Draw(overlay)

                centers = {}
                for sq, is_dest in [(from_sq, False), (to_sq, True)]:
                    f_idx = chess.square_file(sq)
                    r_idx = chess.square_rank(sq)
                    col = (7 - f_idx) if flipped else f_idx
                    row = r_idx if flipped else (7 - r_idx)
                    x0, y0 = col * sq_size, row * sq_size
                    x1, y1 = x0 + sq_size, y0 + sq_size
                    centers[sq] = (x0 + sq_size // 2, y0 + sq_size // 2)

                    # Very soft shade on destination piece (alpha=30) so the piece remains 100% crisp & clear
                    fill_c = (248, 222, 58, 55) if not is_dest else (255, 235, 75, 30)
                    ov_draw.rectangle([x0, y0, x1, y1], fill=fill_c)
                    ov_draw.rectangle([x0, y0, x1, y1], outline=(235, 195, 30, 200), width=3)

                # Draw subtle directional arrow from from_sq towards to_sq (stops before piece)
                x0, y0 = centers[from_sq]
                x1, y1 = centers[to_sq]
                dx, dy = x1 - x0, y1 - y0
                dist = math.hypot(dx, dy)
                if dist > 15:
                    ux, uy = dx / dist, dy / dist
                    arrow_color = (235, 180, 20, 190)
                    start_x, start_y = x0 + ux * 10, y0 + uy * 10
                    tip_x, tip_y = x1 - ux * 28, y1 - uy * 28
                    line_end_x, line_end_y = tip_x - ux * 12, tip_y - uy * 12
                    ov_draw.line([(start_x, start_y), (line_end_x, line_end_y)], fill=arrow_color, width=4)

                    px, py = -uy, ux
                    p1 = (tip_x, tip_y)
                    p2 = (line_end_x + px * 9, line_end_y + py * 9)
                    p3 = (line_end_x - px * 9, line_end_y - py * 9)
                    ov_draw.polygon([p1, p2, p3], fill=arrow_color)

                im_board = Image.alpha_composite(im_board, overlay)
            except Exception as e:
                pass

        canvas.paste(im_board, (border_left, banner_top))

        # Fonts
        font_banner = None
        font_sub = None
        font_coords = None
        font_pill = None
        for font_candidate in ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/System/Library/Fonts/Helvetica.ttc", "/Library/Fonts/Arial Bold.ttf"]:
            if os.path.exists(font_candidate):
                try:
                    font_banner = ImageFont.truetype(font_candidate, 30)
                    font_coords = ImageFont.truetype(font_candidate, 24)
                    font_pill = ImageFont.truetype(font_candidate, 12)
                    break
                except Exception:
                    pass
        for font_candidate in ["/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc", "/Library/Fonts/Arial.ttf"]:
            if os.path.exists(font_candidate):
                try:
                    font_sub = ImageFont.truetype(font_candidate, 17)
                    break
                except Exception:
                    pass

        if font_banner is None:
            font_banner = ImageFont.load_default()
        if font_sub is None:
            font_sub = ImageFont.load_default()
        if font_coords is None:
            font_coords = ImageFont.load_default()
        if font_pill is None:
            font_pill = ImageFont.load_default()

        # Header Banner
        draw.rectangle([0, 0, total_w, banner_top], fill=(28, 33, 38, 255))
        draw.line([0, banner_top - 1, total_w, banner_top - 1], fill=(55, 62, 70, 255), width=2)

        # Subtle Club Tag Pill (Top-Right)
        pill_text = "PICT KNIGHT SHIFT"
        p_bbox = draw.textbbox((0, 0), pill_text, font=font_pill)
        ptw = p_bbox[2] - p_bbox[0]
        pth = p_bbox[3] - p_bbox[1]
        pw = ptw + 20
        ph = 24
        px = total_w - pw - 18
        py = (banner_top - ph) // 2
        draw.rounded_rectangle([px, py, px + pw, py + ph], radius=12, fill=(38, 45, 54, 255), outline=(215, 175, 45, 190), width=1)
        draw.text((px + (pw - ptw) // 2, py + (ph - pth) // 2 - 1), pill_text, fill=(235, 205, 110, 255), font=font_pill)

        side_title = "BLACK TO PLAY" if flipped else "WHITE TO PLAY"
        sub_title = "Find the winning tactical move!"

        tb_bbox = draw.textbbox((0, 0), side_title, font=font_banner)
        text_w = tb_bbox[2] - tb_bbox[0]
        total_group_w = 26 + 12 + text_w
        start_x = (total_w - total_group_w) // 2

        cy = 28
        if flipped:
            draw.ellipse([start_x, cy - 11, start_x + 22, cy + 11], fill=(20, 20, 20, 255), outline=(240, 240, 240, 255), width=2)
        else:
            draw.ellipse([start_x, cy - 11, start_x + 22, cy + 11], fill=(255, 255, 255, 255), outline=(150, 150, 150, 255), width=2)

        draw.text((start_x + 34, 12), side_title, fill=(255, 255, 255, 255), font=font_banner)

        sub_bbox = draw.textbbox((0, 0), sub_title, font=font_sub)
        sub_w = sub_bbox[2] - sub_bbox[0]
        draw.text(((total_w - sub_w) // 2, 50), sub_title, fill=(175, 185, 195, 255), font=font_sub)

        # Coordinates
        files = ["h", "g", "f", "e", "d", "c", "b", "a"] if flipped else ["a", "b", "c", "d", "e", "f", "g", "h"]
        ranks = ["1", "2", "3", "4", "5", "6", "7", "8"] if flipped else ["8", "7", "6", "5", "4", "3", "2", "1"]

        for col, f_char in enumerate(files):
            cx = border_left + col * sq_size + sq_size // 2
            cy = banner_top + board_size + border_bottom // 2
            f_bbox = draw.textbbox((0, 0), f_char, font=font_coords)
            fw, fh = f_bbox[2] - f_bbox[0], f_bbox[3] - f_bbox[1]
            draw.text((cx - fw // 2, cy - fh // 2 - 2), f_char, fill=(215, 220, 225, 255), font=font_coords)

        for row, r_char in enumerate(ranks):
            cx = border_left // 2
            cy = banner_top + row * sq_size + sq_size // 2
            r_bbox = draw.textbbox((0, 0), r_char, font=font_coords)
            rw, rh = r_bbox[2] - r_bbox[0], r_bbox[3] - r_bbox[1]
            draw.text((cx - rw // 2, cy - rh // 2 - 2), r_char, fill=(215, 220, 225, 255), font=font_coords)

        canvas.convert("RGB").save(save_path)
        return save_path
    except Exception as e:
        print(f"[!] Warning annotating board image: {e}")
        return raw_path


def download_image(url, save_path=None, fen=None, last_move_uci=None):
    if save_path is None:
        save_path = os.path.join(BASE_DIR, "chesscom_daily_puzzle.png")
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=ctx) as response:
        with open(save_path, "wb") as f:
            f.write(response.read())
    if fen:
        annotate_board_image(save_path, save_path, fen, last_move_uci)
    return os.path.abspath(save_path)


def copy_image_to_clipboard(image_path):
    """Uses AppleScript to place the image file into macOS clipboard as image data."""
    ext = os.path.splitext(image_path)[1].lower()
    img_class = "«class PNGf»" if ext == ".png" else "«class GIFf»"
    osa_cmd = f'set theFile to POSIX file "{image_path}"\nset the clipboard to (read theFile as {img_class})'
    try:
        subprocess.run(["osascript", "-e", osa_cmd], check=True)
    except subprocess.CalledProcessError:
        osa_cmd_generic = f'set theFile to POSIX file "{image_path}"\nset the clipboard to (read theFile as picture)'
        subprocess.run(["osascript", "-e", osa_cmd_generic], check=True)


def set_text_clipboard(text):
    """Puts text onto macOS clipboard."""
    p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
    p.communicate(text.encode("utf-8"))


def save_puzzle_state(payload):
    """Saves the dispatched puzzle state so its solution can be revealed next morning."""
    state = {
        "puzzle_id": payload.get("puzzle_id"),
        "title": payload.get("title", ""),
        "month": payload.get("month", 1),
        "rating": payload.get("difficulty_metadata", {}).get("rating"),
        "theme": payload.get("difficulty_metadata", {}).get("theme"),
        "fen": payload.get("fen"),
        "solution": payload.get("solution", []),
        "last_move_uci": payload.get("last_move_uci"),
        "hint": payload.get("hint", ""),
        "explanation": payload.get("explanation", ""),
        "tip": payload.get("tip", ""),
        "poll_options": payload.get("poll_options", []),
        "correct_emoji": payload.get("correct_emoji"),
        "correct_label": payload.get("correct_label"),
        "image_url": payload.get("image_url"),
        "saved_at": datetime.datetime.now().isoformat(),
        "solution_sent": False
    }
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    print(f"[✓] Puzzle state saved to: {STATE_FILE}")


def load_puzzle_state():
    """Loads previously saved puzzle state."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[!] Warning reading state file: {e}")
    return None


# ==============================================================================
# 6. ANIMATED SOLUTION GIF GENERATOR
# ==============================================================================
_BOARD_IMAGE_CACHE = {}
_BOARD_CACHE_LOCK = threading.Lock()


def generate_solution_animation(fen, solution_moves, save_path=None):
    """
    Creates an animated GIF of the board showing the solution move-by-move.
    """
    if save_path is None:
        save_path = os.path.join(BASE_DIR, "chesscom_solution_animation.gif")
    board = chess.Board(fen)
    color = "white" if board.turn == chess.WHITE else "black"
    flip_param = "&flip=true" if color == "black" else ""
    ctx = ssl._create_unverified_context()
    sq_size = 90
    bar_h = 48

    font = None
    for f_path in ["/System/Library/Fonts/Helvetica.ttc", "/System/Library/Fonts/Supplemental/Arial.ttf"]:
        if os.path.exists(f_path):
            try:
                font = ImageFont.truetype(f_path, 20)
                break
            except Exception:
                pass
    if font is None:
        font = ImageFont.load_default()

    def fetch_board(b_fen):
        cache_key = (b_fen, flip_param)
        with _BOARD_CACHE_LOCK:
            if cache_key in _BOARD_IMAGE_CACHE:
                return _BOARD_IMAGE_CACHE[cache_key].copy()

        url = f"https://www.chess.com/dynboard?fen={urllib.parse.quote(b_fen)}&size=3{flip_param}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        img = None
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
                img = Image.open(io.BytesIO(r.read())).convert("RGBA")
        except Exception:
            fallback_url = f"https://lichess1.org/export/fen.gif?fen={urllib.parse.quote(b_fen)}&color={color}"
            fallback_req = urllib.request.Request(fallback_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(fallback_req, context=ctx, timeout=10) as r:
                img = Image.open(io.BytesIO(r.read())).convert("RGBA")

        if img is not None:
            with _BOARD_CACHE_LOCK:
                _BOARD_IMAGE_CACHE[cache_key] = img.copy()
            return img.copy()
        return Image.new("RGBA", (720, 720), (240, 240, 240, 255))

    def attach_header(board_img, status_text, is_solved=False):
        canvas = Image.new("RGBA", (720, 720 + bar_h), (20, 24, 30, 255))
        canvas.paste(board_img, (0, bar_h))
        draw = ImageDraw.Draw(canvas)
        draw.line([(0, bar_h - 1), (720, bar_h - 1)], fill=(45, 52, 64), width=1)
        draw.text((16, 13), "PICT CHESS CLUB", font=font, fill=(240, 246, 252))

        bbox = font.getbbox(status_text)
        tw = bbox[2] - bbox[0]
        tx = 720 - 18 - tw
        text_color = (78, 201, 120) if is_solved else (88, 166, 255)
        draw.text((tx, 13), status_text, font=font, fill=text_color)
        return canvas

    board_states = [fetch_board(board.fen())]
    valid_moves = []
    for uci in solution_moves:
        try:
            m = chess.Move.from_uci(uci)
            board.push(m)
            valid_moves.append(uci)
            board_states.append(fetch_board(board.fen()))
        except Exception as e:
            print(f"[!] Warning applying move {uci}: {e}")
            break

    frames = []
    durations = []

    side_str = "White" if color == "white" else "Black"
    init_frame = attach_header(board_states[0], f"{side_str} to move")
    frames.append(init_frame)
    durations.append(1800)

    for i, uci in enumerate(valid_moves):
        after_img = board_states[i + 1]
        move_step = f"Move {i + 1}/{len(valid_moves)}"
        f = attach_header(after_img, move_step, is_solved=(i == len(valid_moves) - 1))
        frames.append(f)
        durations.append(1200)

    final_frame = attach_header(board_states[-1], "✓ SOLVED! PUZZLE COMPLETED", is_solved=True)
    frames.append(final_frame)
    durations.append(3000)

    palette_frames = []
    for frm in frames:
        rgb_frame = Image.new("RGB", frm.size, (255, 255, 255))
        rgb_frame.paste(frm, mask=frm.split()[3])
        p_frame = rgb_frame.convert("P", palette=Image.ADAPTIVE, colors=256)
        palette_frames.append(p_frame)

    os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
    palette_frames[0].save(
        save_path,
        save_all=True,
        append_images=palette_frames[1:],
        duration=durations,
        loop=0,
        optimize=True
    )
    return os.path.abspath(save_path)


def generate_opening_animation(opening_moves, save_path, final_turn=None, trap_name=None):
    """
    Animates the opening run-up starting from Move 1 (standard starting position)
    up to the exact trap position, demonstrating that the position is 100% legal & achievable.
    """
    board = chess.Board()
    flip = (final_turn == "b")
    color = "black" if flip else "white"
    flip_param = "&flip=true" if flip else ""
    ctx = ssl._create_unverified_context()
    bar_h = 48

    font = None
    for f_path in ["/System/Library/Fonts/Helvetica.ttc", "/System/Library/Fonts/Supplemental/Arial.ttf"]:
        if os.path.exists(f_path):
            try:
                font = ImageFont.truetype(f_path, 20)
                break
            except Exception:
                pass
    if font is None:
        font = ImageFont.load_default()

    def fetch_board(b_fen):
        cache_key = (b_fen, flip_param)
        with _BOARD_CACHE_LOCK:
            if cache_key in _BOARD_IMAGE_CACHE:
                return _BOARD_IMAGE_CACHE[cache_key].copy()

        url = f"https://www.chess.com/dynboard?fen={urllib.parse.quote(b_fen)}&size=3{flip_param}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        img = None
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
                img = Image.open(io.BytesIO(r.read())).convert("RGBA")
        except Exception:
            fallback_url = f"https://lichess1.org/export/fen.gif?fen={urllib.parse.quote(b_fen)}&color={color}"
            fallback_req = urllib.request.Request(fallback_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(fallback_req, context=ctx, timeout=10) as r:
                img = Image.open(io.BytesIO(r.read())).convert("RGBA")

        if img is not None:
            with _BOARD_CACHE_LOCK:
                _BOARD_IMAGE_CACHE[cache_key] = img.copy()
            return img.copy()
        return Image.new("RGBA", (720, 720), (240, 240, 240, 255))

    def attach_header(board_img, status_text, is_trap_reached=False):
        canvas = Image.new("RGBA", (720, 720 + bar_h), (20, 24, 30, 255))
        canvas.paste(board_img, (0, bar_h))
        draw = ImageDraw.Draw(canvas)
        draw.line([(0, bar_h - 1), (720, bar_h - 1)], fill=(45, 52, 64), width=1)
        draw.text((16, 13), "PICT CHESS CLUB", font=font, fill=(240, 246, 252))

        bbox = font.getbbox(status_text)
        tw = bbox[2] - bbox[0]
        tx = 720 - 18 - tw
        text_color = (255, 175, 50) if is_trap_reached else (88, 166, 255)
        draw.text((tx, 13), status_text, font=font, fill=text_color)
        return canvas

    board_states = [fetch_board(board.fen())]
    san_labels = []

    for uci in opening_moves:
        try:
            m = chess.Move.from_uci(uci)
            san = board.san(m)
            move_num = board.fullmove_number
            is_white = (board.turn == chess.WHITE)
            label = f"{move_num}. {san}" if is_white else f"{move_num}... {san}"
            san_labels.append(label)
            board.push(m)
            board_states.append(fetch_board(board.fen()))
        except Exception as e:
            print(f"[!] Warning applying opening move {uci}: {e}")
            break

    frames = []
    durations = []

    # Frame 0: Starting position
    init_frame = attach_header(board_states[0], "1. Starting Position")
    frames.append(init_frame)
    durations.append(1500)

    # Intermediate moves
    for i, label in enumerate(san_labels):
        img = board_states[i + 1]
        is_last = (i == len(san_labels) - 1)
        f = attach_header(img, label, is_trap_reached=is_last)
        frames.append(f)
        durations.append(1400 if is_last else 950)

    # Final frame: Trap reached! Side to move!
    side_str = "BLACK" if board.turn == chess.BLACK else "WHITE"
    final_frame = attach_header(board_states[-1], f"🪤 TRAP REACHED! {side_str} TO PLAY", is_trap_reached=True)
    frames.append(final_frame)
    durations.append(3500)

    palette_frames = []
    for frm in frames:
        rgb_frame = Image.new("RGB", frm.size, (255, 255, 255))
        rgb_frame.paste(frm, mask=frm.split()[3])
        p_frame = rgb_frame.convert("P", palette=Image.ADAPTIVE, colors=256)
        palette_frames.append(p_frame)

    os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
    palette_frames[0].save(
        save_path,
        save_all=True,
        append_images=palette_frames[1:],
        duration=durations,
        loop=0,
        optimize=True
    )
    return os.path.abspath(save_path)


def format_solution(fen, solution_moves):
    """Formats moves into human-readable notation."""
    if not fen or not solution_moves:
        return "No moves recorded."
    board = chess.Board(fen)
    friendly_lines = []
    for idx, uci in enumerate(solution_moves, 1):
        try:
            m = chess.Move.from_uci(uci)
            san = board.san(m)
            prefix = f"{board.fullmove_number}... " if board.turn == chess.BLACK else f"{board.fullmove_number}. "
            friendly_lines.append(f"{idx}. *{prefix}{san}* _({uci[:2]} ➔ {uci[2:4]})_")
            board.push(m)
        except Exception:
            friendly_lines.append(f"{idx}. *{uci[:2]} ➔ {uci[2:4]}*")
    return "\n".join(friendly_lines)


def generate_solution_payload():
    """Builds the reveal message for yesterday evening's puzzle."""
    state = load_puzzle_state()
    if not state:
        payload = generate_payload()
        save_puzzle_state(payload)
        state = payload

    puzzle_id = state.get("puzzle_id", "")
    title = state.get("title", "")
    month = state.get("month", 1)
    rating = state.get("rating", "N/A")
    fen = state.get("fen", "")
    solution_moves = state.get("solution", [])
    solution_block = format_solution(fen, solution_moves)
    explanation = state.get("explanation", "")
    tip = state.get("tip", "Always look for checks, captures, and loose pieces!")

    title_line = f"🏷️ Puzzle: \"{title}\"\n" if title else f"🧩 Puzzle: #{puzzle_id}\n"
    poll_result_line = ""
    if state and state.get("correct_emoji"):
        c_emoji = state.get("correct_emoji")
        poll_opts = state.get("poll_options", [])
        winning_move = ""
        for opt in poll_opts:
            if opt.get("is_correct"):
                winning_move = opt.get("full_text", "")
                break
        if winning_move:
            poll_result_line = f"🎯 *Winning Poll Choice:* {c_emoji} *{winning_move}*\n\n"
        else:
            poll_result_line = f"🎯 *Winning Poll Choice:* {c_emoji}\n\n"

    exp_text = f"\n\n📝 *Breakdown:* _{explanation}_" if explanation else ""

    caption = (
        f"*💡 SOLUTION REVEAL 💡*\n\n"
        f"{poll_result_line}"
        f"*🎬 Winning Sequence:*\n{solution_block}"
        f"{exp_text}"
    ).strip()

    return {
        "caption": caption,
        "puzzle_id": puzzle_id,
        "title": title,
        "solution": solution_moves,
        "fen": fen,
        "image_url": state.get("image_url"),
        "state": state
    }


# ==============================================================================
# 7. DISPATCHERS (PUZZLE, SOLUTION, TRAP, BLUNDER, ENDGAME)
# ==============================================================================
def copy_puzzle_manually(puzzle_id=None, use_chesscom=False):
    """Generates daily puzzle, board image, and copies to clipboard."""
    print(f"[*] Generating Daily Tactical Puzzle (1-Year Progressive Curriculum)...")
    payload = generate_payload(puzzle_id=puzzle_id, use_chesscom=use_chesscom)
    save_puzzle_state(payload)
    local_image = os.path.join(BASE_DIR, "chesscom_daily_puzzle.png")
    image_path = download_image(payload["image_url"], save_path=local_image, fen=payload["fen"], last_move_uci=payload.get("last_move_uci"))

    caption_file = os.path.join(BASE_DIR, "whatsapp_puzzle_message.txt")
    with open(caption_file, "w", encoding="utf-8") as f:
        f.write(payload["caption"])

    copy_image_to_clipboard(image_path)
    set_text_clipboard(payload["caption"])

    print("\n" + "=" * 65)
    print("  🧩 DAILY TACTICAL PUZZLE READY TO SEND ON WHATSAPP")
    print("=" * 65)
    print(payload["caption"])
    print("=" * 65)
    print(f"\n[✓] Board Image File:    {local_image}")
    print(f"[✓] Caption Text File:   {caption_file}")
    print("[✓] Board image & caption copied to your Mac clipboard!")
    print("[*] Ready to send:")
    print(f"    1. Drag & drop '{os.path.basename(local_image)}' into your WhatsApp chat.")
    print("    2. Paste the caption (Cmd+V) and hit Send!\n")
    return local_image, caption_file


def copy_solution_manually():
    """Builds solution reveal, generates animated GIF if multi-move, and copies to clipboard."""
    print(f"[*] Generating Solution Reveal...")
    payload = generate_solution_payload()
    state = payload["state"]

    fen = payload["fen"]
    solution_moves = payload["solution"]
    gif_file = os.path.join(BASE_DIR, "chesscom_solution_animation.gif")
    has_gif = len(solution_moves) > 1

    if has_gif:
        print(f"[*] Rendering animated GIF: {gif_file}...")
        generate_solution_animation(fen, solution_moves, save_path=gif_file)
        copy_image_to_clipboard(gif_file)
    elif os.path.exists(gif_file):
        try:
            os.remove(gif_file)
        except Exception:
            pass

    caption_file = os.path.join(BASE_DIR, "whatsapp_solution_message.txt")
    with open(caption_file, "w", encoding="utf-8") as f:
        f.write(payload["caption"])

    set_text_clipboard(payload["caption"])

    if state:
        state["solution_sent"] = True
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    print("\n" + "=" * 65)
    print("  💡 SOLUTION REVEAL READY TO SEND ON WHATSAPP")
    print("=" * 65)
    print(payload["caption"])
    print("=" * 65)
    if has_gif:
        print(f"\n[✓] Animated GIF:      {gif_file}")
    print(f"[✓] Solution Text:     {caption_file}")
    print("[✓] Caption copied to your Mac clipboard!")
    print("[*] Ready to send:")
    if has_gif:
        print(f"    1. Drag & drop '{os.path.basename(gif_file)}' into your WhatsApp chat.")
        print("    2. Paste the caption (Cmd+V) and hit Send!\n")
    else:
        print("    1. Paste the caption (Cmd+V) into your WhatsApp chat and hit Send!\n")
    return gif_file if has_gif else None, caption_file


def copy_trap_manually(trap_id=None):
    """Generates Opening Trap from curriculum, board image, and copies to clipboard."""
    print(f"[*] Generating Sneaky Opening Trap (1-Year Curriculum)...")
    trap = get_next_curriculum_item("traps_curriculum.json", "dispatched_traps", requested_id=trap_id)
    fen = trap["fen"]
    turn = trap["turn"]
    month = trap.get("month", 1)
    rating = trap.get("rating", 550)
    side_to_move = "White" if turn == "w" else "Black"
    flip_param = "&flip=true" if turn == "b" else ""
    encoded_fen = urllib.parse.quote(fen)
    image_url = f"https://www.chess.com/dynboard?fen={encoded_fen}&size=3{flip_param}"

    poll_options, correct_emoji, correct_label, poll_caption, _ = generate_poll_options(fen, trap["solution_uci"])
    opening_name = trap.get("opening", "Opening Line")

    caption = (
        f"🪤 *Opening Trap:* {opening_name}\n"
        f"*{side_to_move} to play: What is the winning tactical strike?*\n"
        f"_React with number_\n\n"
        f"{poll_caption}"
    )

    solution_text = (
        f"🎯 *TRAP SOLUTION:* {correct_emoji} *{trap['solution_san']}*\n\n"
        f"📝 *Breakdown:* _{trap.get('solution_explanation', 'A decisive tactical blow wins material.').strip()}_"
    )

    local_image = os.path.join(BASE_DIR, "chesscom_trap_board.png")
    image_path = download_image(image_url, save_path=local_image, fen=fen, last_move_uci=trap.get("last_move_uci"))

    opening_gif = None
    moves_start = trap.get("moves_from_start", [])
    if moves_start:
        local_gif = os.path.join(BASE_DIR, "chesscom_trap_opening.gif")
        print(f"[*] Generating animated opening run-up GIF: {local_gif}...")
        opening_gif = generate_opening_animation(moves_start, save_path=local_gif, final_turn=turn, trap_name=trap.get("name"))

    caption_file = os.path.join(BASE_DIR, "whatsapp_trap_message.txt")
    with open(caption_file, "w", encoding="utf-8") as f:
        f.write(caption)

    solution_file = os.path.join(BASE_DIR, "whatsapp_trap_solution.txt")
    with open(solution_file, "w", encoding="utf-8") as f:
        f.write(solution_text)

    copy_image_to_clipboard(image_path)
    set_text_clipboard(caption)

    print("\n" + "=" * 65)
    print("  🪤 TRAP OF THE DAY READY TO SEND ON WHATSAPP")
    print("=" * 65)
    print(caption)
    print("=" * 65)
    print(f"\n[✓] Board Image File:    {local_image}")
    if opening_gif:
        print(f"[✓] Opening Run-up GIF:  {opening_gif}")
    print(f"[✓] Caption Text File:   {caption_file}")
    print(f"[✓] Solution & Tips:     {solution_file}")
    print("[✓] Board image & caption copied to your Mac clipboard!")
    print("[*] Ready to send:")
    if opening_gif:
        print(f"    1. Drag & drop '{os.path.basename(local_image)}' and '{os.path.basename(opening_gif)}' into WhatsApp.")
    else:
        print(f"    1. Drag & drop '{os.path.basename(local_image)}' into WhatsApp.")
    print("    2. Paste the caption (Cmd+V) and hit Send!\n")
    return local_image, caption_file


def copy_blunder_manually(blunder_id=None):
    """Generates Blunder of the Day from curriculum, board image, and copies to clipboard."""
    print(f"[*] Generating Blunder of the Day (1-Year Curriculum)...")
    blunder = get_next_curriculum_item("blunders_curriculum.json", "dispatched_blunders", requested_id=blunder_id)
    fen = blunder["fen"]
    turn = blunder["turn"]
    month = blunder.get("month", 1)
    rating = blunder.get("rating", 550)
    side_to_move = "White" if turn == "w" else "Black"
    opp_side = "Black" if side_to_move == "White" else "White"
    flip_param = "&flip=true" if turn == "b" else ""
    encoded_fen = urllib.parse.quote(fen)
    image_url = f"https://www.chess.com/dynboard?fen={encoded_fen}&size=3{flip_param}"

    poll_options, correct_emoji, correct_label, poll_caption, _ = generate_poll_options(fen, blunder["solution_uci"])
    blunder_mv = blunder.get("blunder_move", "a blunder").strip("*` ")
    better_mv = blunder.get("better_move", "a safer move")

    caption = (
        f"🤦 {opp_side} just played *{blunder_mv}* blundering in this position.\n"
        f"*{side_to_move} to play: How do you punish this blunder?*\n"
        f"_React with number_\n\n"
        f"{poll_caption}"
    )

    solution_text = (
        f"🔨 *BLUNDER PUNISHMENT:* {correct_emoji} *{blunder['solution_san']}*\n\n"
        f"📝 *Breakdown:* _{opp_side} should have played {better_mv} instead. {blunder['solution_san']} decisively punishes the mistake._"
    )

    local_image = os.path.join(BASE_DIR, "chesscom_blunder_board.png")
    image_path = download_image(image_url, save_path=local_image, fen=fen, last_move_uci=blunder.get("last_move_uci"))

    caption_file = os.path.join(BASE_DIR, "whatsapp_blunder_message.txt")
    with open(caption_file, "w", encoding="utf-8") as f:
        f.write(caption)

    solution_file = os.path.join(BASE_DIR, "whatsapp_blunder_solution.txt")
    with open(solution_file, "w", encoding="utf-8") as f:
        f.write(solution_text)

    copy_image_to_clipboard(image_path)
    set_text_clipboard(caption)

    print("\n" + "=" * 65)
    print("  🤦 BLUNDER OF THE DAY READY TO SEND ON WHATSAPP")
    print("=" * 65)
    print(caption)
    print("=" * 65)
    print(f"\n[✓] Board Image File:    {local_image}")
    print(f"[✓] Caption Text File:   {caption_file}")
    print(f"[✓] Solution & Lesson:   {solution_file}")
    print("[✓] Board image & caption copied to your Mac clipboard!")
    return local_image, caption_file


def copy_endgame_manually(endgame_id=None):
    """Generates Endgame Skill from curriculum, board image, and copies to clipboard."""
    print(f"[*] Generating Endgame Skill of the Day (1-Year Curriculum)...")
    endgame = get_next_curriculum_item("endgames_curriculum.json", "dispatched_endgames", requested_id=endgame_id)
    fen = endgame["fen"]
    turn = endgame["turn"]
    month = endgame.get("month", 1)
    rating = endgame.get("rating", 550)
    side_to_move = "White" if turn == "w" else "Black"
    flip_param = "&flip=true" if turn == "b" else ""
    encoded_fen = urllib.parse.quote(fen)
    image_url = f"https://www.chess.com/dynboard?fen={encoded_fen}&size=3{flip_param}"

    poll_options, correct_emoji, correct_label, poll_caption, _ = generate_poll_options(fen, endgame["solution_uci"])

    caption = (
        f"*♟️ {side_to_move} to play: What is the crucial move?*\n"
        f"_React with number_\n\n"
        f"{poll_caption}"
    )

    solution_text = (
        f"🏆 *ENDGAME TECHNIQUE:* {correct_emoji} *{endgame['solution_san']}*\n\n"
        f"📝 *Master Rule:* _{endgame.get('solution_explanation', 'Accurate king and pawn play converts the endgame.').strip()}_"
    )

    local_image = os.path.join(BASE_DIR, "chesscom_endgame_board.png")
    image_path = download_image(image_url, save_path=local_image, fen=fen, last_move_uci=endgame.get("last_move_uci"))

    caption_file = os.path.join(BASE_DIR, "whatsapp_endgame_message.txt")
    with open(caption_file, "w", encoding="utf-8") as f:
        f.write(caption)

    solution_file = os.path.join(BASE_DIR, "whatsapp_endgame_solution.txt")
    with open(solution_file, "w", encoding="utf-8") as f:
        f.write(solution_text)

    copy_image_to_clipboard(image_path)
    set_text_clipboard(caption)

    print("\n" + "=" * 65)
    print("  ♟️ ENDGAME SKILL READY TO SEND ON WHATSAPP")
    print("=" * 65)
    print(caption)
    print("=" * 65)
    print(f"\n[✓] Board Image File:    {local_image}")
    print(f"[✓] Caption Text File:   {caption_file}")
    print(f"[✓] Solution & Rules:    {solution_file}")
    print("[✓] Board image & caption copied to your Mac clipboard!")
    return local_image, caption_file


# ==============================================================================
# 8. SCHEDULE & CURRICULUM CONTROLLER
# ==============================================================================
def print_timetable():
    """Prints the weekly PICT Knight Shift community schedule."""
    print("""
========================================================================================
             📅 PICT KNIGHT SHIFT - WEEKLY COMMUNITY TIMETABLE
========================================================================================
Day         Primary Event                 Specialized Daily Feature
----------------------------------------------------------------------------------------
Monday      Daily Puzzle (WhatsApp Poll)  🪤 Sneaky Opening Trap Monday
Tuesday     Daily Puzzle (WhatsApp Poll)  🤦 Blunder of the Day (Reverse Puzzle)
Wednesday   Daily Puzzle (WhatsApp Poll)  ♟️ Master Endgame Skills Wednesday
Thursday    Daily Puzzle (WhatsApp Poll)  🤦 Blunder of the Day (Reverse Puzzle)
Friday      Daily Puzzle (WhatsApp Poll)  🪤 Sneaky Opening Trap Friday
Saturday    Weekly Lichess Arena          🏆 Club Tournament Day (Puzzles Paused)
Sunday      Tournament Recap & Awards     🏅 Winners Podium & Rating Awards (Puzzles Paused)
========================================================================================
""")


def print_curriculum():
    """Prints the complete 1-year progressive curriculum roadmap (Months 1-12)."""
    history = load_dispatch_history()
    curr_m = history.get("current_month", 1)

    print("\n" + "=" * 80)
    print("       🎓 PICT KNIGHT SHIFT: 1-YEAR CHESS MASTERY CURRICULUM (500–1700 ELO)")
    print("=" * 80)
    print("Month  Rating Tier   Theme & Focus Area                        Status")
    print("-" * 80)
    for m in range(1, 13):
        info = CURRICULUM_MONTH_INFO.get(m, {})
        status = "👉 ACTIVE (CURRENT)" if m == curr_m else ("✓ Completed" if m < curr_m else "Upcoming")
        print(f"M{m:02d}    {info.get('range', ''):13} {info.get('theme', ''):40} [{status}]")
    print("=" * 80)
    print(f"[*] Started: {history.get('start_date', 'N/A')} | Active Month: {curr_m} | Increases by +100 Elo every month!")
    print("[*] To switch month manually: python3 send_daily_puzzle.py set-month <1-12>\n")


def print_history():
    """Displays tracking status of the 1-year curriculum pools."""
    history = load_dispatch_history()
    curr_m = history.get("current_month", 1)
    info = CURRICULUM_MONTH_INFO.get(curr_m, {})

    puzzles_db = load_curriculum_file("puzzles_curriculum.json")
    traps_db = load_curriculum_file("traps_curriculum.json")
    blunders_db = load_curriculum_file("blunders_curriculum.json")
    endgames_db = load_curriculum_file("endgames_curriculum.json")

    total_p = sum(len(v) for v in puzzles_db.values())
    total_t = sum(len(v) for v in traps_db.values())
    total_b = sum(len(v) for v in blunders_db.values())
    total_e = sum(len(v) for v in endgames_db.values())

    p_disp = len(history.get("dispatched_puzzles", []))
    t_disp = len(history.get("dispatched_traps", []))
    b_disp = len(history.get("dispatched_blunders", []))
    e_disp = len(history.get("dispatched_endgames", []))

    month_key = f"month_{curr_m}"
    m_p_total = len(puzzles_db.get(month_key, []))
    m_p_disp = len([pid for pid in history.get("dispatched_puzzles", []) if pid.startswith(f"m{curr_m:02d}_")])

    print("\n=======================================================")
    print(f"  📊 1-YEAR CURRICULUM DISPATCH STATUS: MONTH {curr_m}/12")
    print(f"  🎯 Target Rating: {info.get('range', '')} Elo | {info.get('theme', '')}")
    print("=======================================================")
    print(f"• Current Month Puzzles: {m_p_disp}/{m_p_total} dispatched in Month {curr_m}")
    print(f"• Total Year Puzzles:    {p_disp}/{total_p} dispatched ({total_p - p_disp} remaining)")
    print(f"• Total Year Traps:      {t_disp}/{total_t} dispatched ({total_t - t_disp} remaining)")
    print(f"• Total Year Blunders:   {b_disp}/{total_b} dispatched ({total_b - b_disp} remaining)")
    print(f"• Total Year Endgames:   {e_disp}/{total_e} dispatched ({total_e - e_disp} remaining)")
    style = history.get("poll_style", "numbers")
    style_names = {
        "numbers": "Numbers inside emoji buttons (1️⃣ 2️⃣ 3️⃣ 4️⃣ — default, instant WhatsApp reactions)",
        "letters": "Letters inside solid badges (🅐 🅑 🅒 🅓)",
        "red": "Red square badges (🟥 A) 🟥 B))"
    }
    print(f"• Poll Option Style:     {style_names.get(style, style)}")
    print("=======================================================\n")


def dispatch_today(force=False, use_chesscom=False):
    """Executes the exact scheduled event for today according to the weekly timetable."""
    now = datetime.datetime.now()
    day_name = now.strftime("%A")
    sched = WEEKLY_SCHEDULE.get(day_name)
    if not sched:
        print(f"[!] Unknown day: {day_name}")
        return

    print("=" * 65)
    print(f"  📅 PICT KNIGHT SHIFT: {sched['theme'].upper()} ({day_name.upper()})")
    print("=" * 65)
    print(f"[*] Schedule: {sched['title']}\n")

    if day_name in ["Saturday", "Sunday"] and not force:
        if day_name == "Saturday":
            print("🏆 SATURDAY: TOURNAMENT DAY")
            print("   Daily tactical puzzles are paused today.")
            print("   Today is reserved for our Weekly PICT Knight Shift Arena Tournament on Lichess!")
            print("   Tip: Pass --force if you want to export today's puzzle anyway.\n")
        else:
            print("🏅 SUNDAY: TOURNAMENT RECAP DAY")
            print("   Daily tactical puzzles are paused today.")
            print("   Today is reserved for sharing the Tournament recap, podium winners, and rating awards!")
            print("   Tip: Pass --force if you want to export today's puzzle anyway.\n")
        return

    # 1. Run Daily Puzzle (Everyday Monday to Friday)
    print(f"--- [1/2] Today's Daily Puzzle (with 4-Choice WhatsApp Poll) ---")
    copy_puzzle_manually(use_chesscom=use_chesscom)

    # 2. Run the Day's Feature
    feature = sched["feature"]
    if feature == "trap":
        print(f"\n--- [2/2] {sched['theme']} (Sneaky Opening Trap) ---")
        copy_trap_manually()
    elif feature == "blunder":
        print(f"\n--- [2/2] {sched['theme']} (Blunder of the Day) ---")
        copy_blunder_manually()
    elif feature == "endgame":
        print(f"\n--- [2/2] {sched['theme']} (Master Endgame Skills) ---")
        copy_endgame_manually()


# ==============================================================================
# 9. CLI ENTRY POINT
# ==============================================================================
def main():
    args = sys.argv[1:]
    command = "today" if not args else "puzzle"
    force = False
    use_chesscom = False
    use_gdrive = False

    if "--force" in args:
        force = True
        args.remove("--force")
    if "-f" in args:
        force = True
        args.remove("-f")
    if "--chesscom" in args:
        use_chesscom = True
        args.remove("--chesscom")
    if "--gdrive" in args:
        use_gdrive = True
        args.remove("--gdrive")
    if "-g" in args:
        use_gdrive = True
        args.remove("-g")

    sub_arg = None
    if args:
        if args[0] in ["-h", "--help", "help"]:
            print("""Usage: python3 send_daily_puzzle.py [COMMAND] [OPTIONS] [--force] [--chesscom] [--gdrive]

Core Schedule Commands:
  today              Run today's scheduled events according to weekly timetable (Default)
  timetable          Display the full PICT Knight Shift weekly community schedule
  curriculum         Display the 1-Year Mastery Curriculum Roadmap (500–1700 Elo)
  set-month <1-12>   Set the active curriculum month (e.g., set-month 2 for 600–700 Elo)
  puzzle [id|list]   Generate curriculum daily puzzle with 4-choice WhatsApp poll
  solution           Reveal solution with winning poll answer & animated GIF
  animate            Generate and save the animated GIF locally for testing

Community Engagement Features (1-Year Inexhaustible Pools):
  trap [name|list]   Sneaky Opening Trap (Mon & Fri) with board image & 4-choice poll
  blunder [name|list] Blunder of the Day (Tue & Thu) with board image & 4-choice poll
  endgame [name|list] Master Endgame Skills (Wed) with board image & 4-choice poll

Mobile & Cloud Sync:
  gdrive             Sync today's generated image, caption, and poll directly to Google Drive
  gdrive status      Check Google Drive authorization and setup status

History & Pool Tracking:
  history            View active month status and 1-year dispatch progress
  history-reset      Reset curriculum history back to Month 1 (500–600 Elo)
  set-style <style>  Set poll badge style: 'letters' (🅐 🅑 🅒 🅓) or 'keycaps' (1️⃣ 2️⃣ 3️⃣ 4️⃣)

Flags:
  --gdrive, -g       Automatically upload generated images & text to Google Drive folder
  --chesscom         Use Chess.com public daily puzzle instead of curriculum
  --force, -f        Bypass weekend pause or duplicate checks
""")
            return
        elif args[0] in [
            "today", "timetable", "calendar", "curriculum", "set-month",
            "history", "history-reset", "set-style", "style", "puzzle", "solution", "animate",
            "copy", "copy-puzzle", "manual", "export", "copy-solution",
            "trap", "copy-trap", "blunder", "copy-blunder", "endgame", "copy-endgame",
            "gdrive", "upload", "sync"
        ]:
            command = args[0]
            if len(args) > 1:
                sub_arg = args[1]

    if command == "today":
        dispatch_today(force=force, use_chesscom=use_chesscom)
    elif command in ["timetable", "calendar"]:
        print_timetable()
    elif command == "curriculum":
        print_curriculum()
    elif command == "set-month":
        if sub_arg:
            try:
                set_current_month(int(sub_arg))
            except ValueError:
                print(f"[!] Invalid month argument: {sub_arg}. Please specify an integer from 1 to 12.")
        else:
            print("[!] Please provide a month number: python3 send_daily_puzzle.py set-month <1-12>")
    elif command in ["set-style", "style"]:
        if sub_arg:
            set_poll_style(sub_arg)
        else:
            print("[!] Please provide a style name: python3 send_daily_puzzle.py set-style <letters|keycaps|red>")
    elif command == "history":
        print_history()
    elif command == "history-reset":
        reset_dispatch_history()
    elif command in ["copy", "copy-puzzle", "manual", "export", "puzzle"]:
        if sub_arg == "list":
            history = load_dispatch_history()
            m = history.get("current_month", 1)
            p_db = load_curriculum_file("puzzles_curriculum.json")
            m_puzzles = p_db.get(f"month_{m}", [])
            print(f"\nAvailable Puzzles for Month {m} ({CURRICULUM_MONTH_INFO.get(m, {}).get('range', '')} Elo):")
            for item in m_puzzles:
                print(f"  • {item['id']:18} -> {item['title']} ({item['theme']})")
            print()
            return
        copy_puzzle_manually(puzzle_id=sub_arg, use_chesscom=use_chesscom)
    elif command in ["solution", "copy-solution"]:
        copy_solution_manually()
    elif command in ["trap", "copy-trap"]:
        if sub_arg == "list":
            history = load_dispatch_history()
            m = history.get("current_month", 1)
            t_db = load_curriculum_file("traps_curriculum.json")
            m_traps = t_db.get(f"month_{m}", [])
            print(f"\nAvailable Traps for Month {m} ({CURRICULUM_MONTH_INFO.get(m, {}).get('range', '')} Elo):")
            for item in m_traps:
                print(f"  • {item['id']:22} -> {item['name']} ({item['opening']})")
            print()
            return
        copy_trap_manually(trap_id=sub_arg)
    elif command in ["blunder", "copy-blunder"]:
        if sub_arg == "list":
            history = load_dispatch_history()
            m = history.get("current_month", 1)
            b_db = load_curriculum_file("blunders_curriculum.json")
            m_blunders = b_db.get(f"month_{m}", [])
            print(f"\nAvailable Blunders for Month {m} ({CURRICULUM_MONTH_INFO.get(m, {}).get('range', '')} Elo):")
            for item in m_blunders:
                print(f"  • {item['id']:24} -> {item['title']} ({item['blunder_move']})")
            print()
            return
        copy_blunder_manually(blunder_id=sub_arg)
    elif command in ["endgame", "copy-endgame"]:
        if sub_arg == "list":
            history = load_dispatch_history()
            m = history.get("current_month", 1)
            e_db = load_curriculum_file("endgames_curriculum.json")
            m_endgames = e_db.get(f"month_{m}", [])
            print(f"\nAvailable Endgames for Month {m} ({CURRICULUM_MONTH_INFO.get(m, {}).get('range', '')} Elo):")
            for item in m_endgames:
                print(f"  • {item['id']:22} -> {item['title']} ({item['technique']})")
            print()
            return
        copy_endgame_manually(endgame_id=sub_arg)
    elif command == "animate":
        out = os.path.join(BASE_DIR, "chesscom_solution_animation.gif")
        state = load_puzzle_state()
        if not state:
            p = generate_payload()
            fen = p["fen"]
            sol = p["solution"]
        else:
            fen = state.get("fen")
            sol = state.get("solution", [])
        print(f"[*] Generating animation for puzzle to: {out}...")
        path = generate_solution_animation(fen, sol, save_path=out)
        print(f"[✓] Animation generated successfully: {path} ({os.path.getsize(path)} bytes)")
    elif command in ["gdrive", "upload", "sync"]:
        try:
            import gdrive_sync
            if sub_arg in ["status", "check"]:
                gdrive_sync.check_auth_status()
            elif sub_arg in ["guide", "help", "setup"]:
                gdrive_sync.print_setup_guide()
            elif sub_arg in ["auth", "login"]:
                gdrive_sync.get_gdrive_service()
            else:
                gdrive_sync.sync_to_google_drive()
        except Exception as e:
            print(f"[!] Google Drive sync failed: {e}")
        return

    # If --gdrive flag was specified with any generator command, auto-sync now
    if use_gdrive:
        try:
            import gdrive_sync
            print("\n[*] Automatically syncing generated files to Google Drive...")
            gdrive_sync.sync_to_google_drive()
        except Exception as e:
            print(f"[!] Google Drive auto-sync failed: {e}")


if __name__ == "__main__":
    main()
