"""
PICT KNIGHT SHIFT // POSTER COMPOSITOR & GRAPHIC GENERATOR
File: hackathon/create_poster.py

Composites typography, glow effects, badges, feature cards, and registration QR code
onto the cybernetic Knight artwork to produce a high-impact promotional poster.
"""

import os
import sys
import urllib.request
import ssl
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BG_PATH = "/Users/varadmalpure/.gemini/antigravity-cli/brain/7c5459a4-384b-499c-b6f7-2f31b0da7489/pict_knight_shift_clean_bg_1792433926411.jpg"
OUTPUT_PNG = os.path.join(BASE_DIR, "PICT_KNIGHT_SHIFT_POSTER.png")
OUTPUT_JPG = os.path.join(BASE_DIR, "PICT_KNIGHT_SHIFT_POSTER.jpg")


def get_font(font_path, size):
    try:
        return ImageFont.truetype(font_path, size)
    except Exception:
        return ImageFont.load_default()


def download_qr_code(save_path):
    url = "https://api.qrserver.com/v1/create-qr-code/?size=240x240&data=https://forms.gle/4vuAAeGVSjJ5JzFV6&margin=6"
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=ctx) as r:
        with open(save_path, "wb") as f:
            f.write(r.read())
    return save_path


def create_poster():
    print("[*] Loading background artwork...")
    im = Image.open(BG_PATH).convert("RGBA")
    w, h = im.size  # 896 x 1200

    # Fonts
    f_title = get_font("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 52)
    f_eyebrow = get_font("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 15)
    f_subtitle = get_font("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 18)
    f_badge = get_font("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 13)
    f_card_header = get_font("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 16)
    f_card_body = get_font("/System/Library/Fonts/Supplemental/Arial.ttf", 14)
    f_card_bold = get_font("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 14)
    f_qr_label = get_font("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 12)
    f_qr_url = get_font("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 11)

    # Separate overlay canvas for clean alpha blending
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # -------------------------------------------------------------------------
    # 1. TOP HEADER & TITLE
    # -------------------------------------------------------------------------
    # Dark gradient behind top text to guarantee razor-sharp legibility
    for y_pos in range(0, 240):
        alpha = int(220 * (1.0 - (y_pos / 240.0) ** 1.5))
        draw.line([(0, y_pos), (w, y_pos)], fill=(8, 12, 18, alpha))

    # Eyebrow Pill
    eyebrow_text = "PICT CHESS CLUB PRESENTS"
    eb_bbox = draw.textbbox((0, 0), eyebrow_text, font=f_eyebrow)
    eb_w = eb_bbox[2] - eb_bbox[0]
    eb_h = eb_bbox[3] - eb_bbox[1]
    eb_pad_x, eb_pad_y = 16, 6
    eb_x0 = (w - (eb_w + eb_pad_x * 2)) // 2
    eb_y0 = 34
    draw.rounded_rectangle(
        [eb_x0, eb_y0, eb_x0 + eb_w + eb_pad_x * 2, eb_y0 + eb_h + eb_pad_y * 2],
        radius=14,
        fill=(16, 22, 32, 230),
        outline=(215, 175, 45, 200),
        width=1
    )
    draw.text((eb_x0 + eb_pad_x, eb_y0 + eb_pad_y - 1), eyebrow_text, font=f_eyebrow, fill=(240, 215, 120, 255))

    # Main Title: "PICT KNIGHT SHIFT"
    title_text = "PICT KNIGHT SHIFT"
    t_bbox = draw.textbbox((0, 0), title_text, font=f_title)
    t_w = t_bbox[2] - t_bbox[0]
    t_x = (w - t_w) // 2
    t_y = 78

    # Multi-layered glowing drop shadow
    for offset, color in [((0, 4), (0, 0, 0, 240)), ((0, 2), (0, 160, 255, 160)), ((-1, 0), (220, 175, 45, 120))]:
        draw.text((t_x + offset[0], t_y + offset[1]), title_text, font=f_title, fill=color)
    draw.text((t_x, t_y), title_text, font=f_title, fill=(255, 255, 255, 255))

    # Subtitle: "CAMPUS CHESS BOT DERBY // DIWALI 2026 EDITION"
    sub_text = "CAMPUS CHESS BOT DERBY  •  DIWALI 2026"
    s_bbox = draw.textbbox((0, 0), sub_text, font=f_subtitle)
    s_w = s_bbox[2] - s_bbox[0]
    s_x = (w - s_w) // 2
    s_y = 142
    draw.text((s_x + 1, s_y + 1), sub_text, font=f_subtitle, fill=(0, 0, 0, 200))
    draw.text((s_x, s_y), sub_text, font=f_subtitle, fill=(88, 195, 255, 255))

    # Tagline
    tag_text = "Code, Prompt & Battle Your AI Chess Engine on 64 Squares!"
    tag_bbox = draw.textbbox((0, 0), tag_text, font=f_card_bold)
    tag_w = tag_bbox[2] - tag_bbox[0]
    draw.text(((w - tag_w) // 2, 172), tag_text, font=f_card_bold, fill=(215, 225, 235, 255))

    # -------------------------------------------------------------------------
    # 2. KEY HIGHLIGHT BADGES ROW
    # -------------------------------------------------------------------------
    badges = [
        ("AI Agents Encouraged", (40, 160, 255)),
        ("Pure Python (<=100 KB)", (235, 185, 45)),
        ("1.0s Move Budget", (78, 201, 120)),
        ("100% Automated Arena", (220, 120, 255))
    ]
    b_total_w = sum(draw.textbbox((0, 0), b[0], font=f_badge)[2] - draw.textbbox((0, 0), b[0], font=f_badge)[0] + 20 for b in badges) + (len(badges) - 1) * 8
    cur_bx = (w - b_total_w) // 2
    by0 = 202
    for b_text, b_col in badges:
        bw = draw.textbbox((0, 0), b_text, font=f_badge)[2] - draw.textbbox((0, 0), b_text, font=f_badge)[0]
        pw = bw + 20
        draw.rounded_rectangle([cur_bx, by0, cur_bx + pw, by0 + 26], radius=13, fill=(14, 18, 26, 230), outline=(b_col[0], b_col[1], b_col[2], 180), width=1)
        draw.text((cur_bx + 10, by0 + 5), b_text, font=f_badge, fill=(245, 248, 252, 255))
        cur_bx += pw + 8

    # -------------------------------------------------------------------------
    # 3. BOTTOM INFORMATION & REGISTRATION CARD
    # -------------------------------------------------------------------------
    # Subtle dark gradient rising from bottom
    for y_pos in range(780, 1200):
        alpha = int(245 * (((y_pos - 780) / 420.0) ** 1.3))
        draw.line([(0, y_pos), (w, y_pos)], fill=(6, 10, 16, alpha))

    card_x0, card_y0 = 36, 850
    card_x1, card_y1 = w - 36, 1166

    # Frosted glass card backing
    draw.rounded_rectangle(
        [card_x0, card_y0, card_x1, card_y1],
        radius=18,
        fill=(12, 17, 26, 235),
        outline=(52, 72, 105, 220),
        width=2
    )
    # Accent top highlight line
    draw.line([(card_x0 + 30, card_y0 + 1), (card_x1 - 30, card_y0 + 1)], fill=(90, 165, 255, 180), width=2)

    # LEFT COLUMN: TOURNAMENT STRUCTURE & DATES
    col_x = card_x0 + 24
    cy = card_y0 + 18

    # Section 1: The 100-Point Automated Arena
    draw.text((col_x, cy), "100-POINT AUTOMATED SCORING (NO VIVA, NO MANUAL GRADING)", font=f_card_header, fill=(240, 205, 95, 255))
    cy += 24

    scoring_points = [
        ("• 60% Main Arena:", " Swiss Qualifier + Double Round-Robin (Paired Openings)"),
        ("• 20% Challenge Suite:", " 18 Secret Tactical, Endgame & Chess960 Tests"),
        ("• 20% Reference Gauntlet:", " Battle ~1000, ~1500 & ~2000 Elo Reference Engines")
    ]
    for prefix, body in scoring_points:
        pw = draw.textbbox((0, 0), prefix, font=f_card_bold)[2] - draw.textbbox((0, 0), prefix, font=f_card_bold)[0]
        draw.text((col_x + 8, cy), prefix, font=f_card_bold, fill=(88, 185, 255, 255))
        draw.text((col_x + 8 + pw, cy), body, font=f_card_body, fill=(215, 225, 235, 255))
        cy += 20

    # Section 2: Timeline & Rules
    cy += 8
    draw.line([(col_x, cy), (card_x1 - 220, cy)], fill=(38, 50, 70, 200), width=1)
    cy += 12

    draw.text((col_x, cy), "CRITICAL DATES & TIMELINE", font=f_card_header, fill=(240, 205, 95, 255))
    cy += 24

    timeline_points = [
        ("• Sunday Leaderboard Runs:", " Oct 25 & Nov 1 @ 9:00 PM (Unlimited Resubmissions!)"),
        ("• Final Submissions Close:", " Diwali Eve (Saturday, Nov 7 @ 11:59 PM)"),
        ("• Grand Finale & Replays:", " Sunday, Nov 8 (PGN Games Analyzed on Lichess)")
    ]
    for prefix, body in timeline_points:
        pw = draw.textbbox((0, 0), prefix, font=f_card_bold)[2] - draw.textbbox((0, 0), prefix, font=f_card_bold)[0]
        draw.text((col_x + 8, cy), prefix, font=f_card_bold, fill=(78, 205, 130, 255))
        draw.text((col_x + 8 + pw, cy), body, font=f_card_body, fill=(215, 225, 235, 255))
        cy += 20

    # Section 3: Official Honors Banner
    cy += 8
    awards_text = "Campus Grandmaster  •  The Giant Slayer  •  The Iron Bastion  •  Tactical Maestro"
    draw.text((col_x + 8, cy), awards_text, font=f_badge, fill=(245, 170, 70, 255))

    # RIGHT COLUMN: REGISTRATION QR CODE & URL
    qr_w, qr_h = 160, 160
    qr_x0 = card_x1 - qr_w - 24
    qr_y0 = card_y0 + 26

    qr_temp = "/tmp/hackathon_form_qr.png"
    download_qr_code(qr_temp)
    qr_img = Image.open(qr_temp).convert("RGBA").resize((qr_w, qr_h), Image.Resampling.LANCZOS)

    # QR Container Box with white backing
    draw.rounded_rectangle([qr_x0 - 8, qr_y0 - 8, qr_x0 + qr_w + 8, qr_y0 + qr_h + 8], radius=12, fill=(255, 255, 255, 255))
    overlay.paste(qr_img, (qr_x0, qr_y0))

    # QR Label & Link below
    lbl_text = "SCAN TO REGISTER"
    lbl_w = draw.textbbox((0, 0), lbl_text, font=f_qr_label)[2] - draw.textbbox((0, 0), lbl_text, font=f_qr_label)[0]
    draw.text((qr_x0 + (qr_w - lbl_w) // 2, qr_y0 + qr_h + 16), lbl_text, font=f_qr_label, fill=(240, 215, 110, 255))

    url_text = "forms.gle/4vuAAeGVSjJ5JzFV6"
    url_w = draw.textbbox((0, 0), url_text, font=f_qr_url)[2] - draw.textbbox((0, 0), url_text, font=f_qr_url)[0]
    draw.text((qr_x0 + (qr_w - url_w) // 2, qr_y0 + qr_h + 34), url_text, font=f_qr_url, fill=(88, 185, 255, 255))

    badge_free = "FREE ENTRY • CAMPUS WIDE"
    bf_w = draw.textbbox((0, 0), badge_free, font=f_badge)[2] - draw.textbbox((0, 0), badge_free, font=f_badge)[0]
    draw.text((qr_x0 + (qr_w - bf_w) // 2, qr_y0 + qr_h + 54), badge_free, font=f_badge, fill=(180, 195, 210, 255))

    # Final Composite
    print("[*] Compositing artwork with text overlay...")
    final_poster = Image.alpha_composite(im, overlay)

    print(f"[*] Saving high-res poster to: {OUTPUT_PNG}...")
    final_poster.save(OUTPUT_PNG, format="PNG")

    print(f"[*] Saving compressed JPEG to: {OUTPUT_JPG}...")
    final_poster.convert("RGB").save(OUTPUT_JPG, format="JPEG", quality=95)

    print("[✓] POSTER GENERATION COMPLETE!")
    return OUTPUT_PNG, OUTPUT_JPG


if __name__ == "__main__":
    create_poster()
