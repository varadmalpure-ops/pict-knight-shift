"""
PICT KNIGHT SHIFT // AGENTIC CHESS BOT DERBY
Contender: varad_bot.py
Author: varadmalpure-ops

Architecture:
1. Iterative Deepening Negamax with Alpha-Beta Pruning & Fail-Soft
2. Quiescence Search with Delta Pruning and In-Check Evade Handling
3. Transposition Table keyed by 64-bit Zobrist Hash (chess.polyglot)
4. MVV-LVA Move Ordering + Killer Moves + History Heuristic
5. Null-Move Pruning (NMP) & Late Move Reductions (LMR) & Check Extension
6. Tapered Positional Scoring (PeSTO Tables, Passed/Doubled/Isolated Pawns,
   Pawn Shield Safety, Semi/Full File Rooks, Bishop Pair)
7. Mop-Up King Driving & Stalemate/Repetition Evasion for Endgames
8. Hand-Embedded Opening Playbook with Natural Randomization
"""

import chess
import chess.polyglot
import math
import random
import time
from typing import Optional, List, Dict, Tuple

# 1. CONSTANTS & MATE BOUNDS

INFINITY = 1000000
MATE_SCORE = 30000
MATE_THRESHOLD = 29000

# TT Flags
FLAG_EXACT = 0
FLAG_LOWERBOUND = 1
FLAG_UPPERBOUND = 2

# Piece Base Values (Middlegame / Endgame)
MG_VAL = {
    chess.PAWN: 82,
    chess.KNIGHT: 337,
    chess.BISHOP: 365,
    chess.ROOK: 477,
    chess.QUEEN: 1025,
    chess.KING: 20000,
}

EG_VAL = {
    chess.PAWN: 94,
    chess.KNIGHT: 281,
    chess.BISHOP: 297,
    chess.ROOK: 512,
    chess.QUEEN: 936,
    chess.KING: 20000,
}

PHASE_WEIGHT = {
    chess.PAWN: 0,
    chess.KNIGHT: 1,
    chess.BISHOP: 1,
    chess.ROOK: 2,
    chess.QUEEN: 4,
    chess.KING: 0,
}

# 2. PeSTO PIECE-SQUARE TABLES (Rank-8 First Representation)

PST_PAWN_MG = [
    0, 0, 0, 0, 0, 0, 0, 0,
    98, 134, 61, 95, 68, 126, 34, -11,
    -6, 7, 26, 31, 65, 56, 25, -20,
    -14, 13, 6, 21, 23, 12, 17, -23,
    -27, -2, -5, 12, 17, 6, 10, -25,
    -26, -4, -4, -10, 3, 3, 33, -12,
    -35, -1, -20, -23, -15, 24, 38, -22,
    0, 0, 0, 0, 0, 0, 0, 0,
]

PST_PAWN_EG = [
    0, 0, 0, 0, 0, 0, 0, 0,
    178, 173, 158, 134, 147, 132, 165, 187,
    94, 100, 85, 67, 56, 53, 82, 84,
    32, 24, 13, 5, -2, 4, 17, 17,
    13, 9, -3, -7, -7, -8, 3, -1,
    4, 7, -6, 1, 0, -5, -1, -8,
    13, 9, -3, -7, -7, -8, 3, -1,
    0, 0, 0, 0, 0, 0, 0, 0,
]

PST_KNIGHT_MG = [
    -167, -89, -34, -49, 61, -97, -15, -107,
    -73, -41, 72, 36, 23, 62, 7, -17,
    -47, 60, 37, 65, 84, 129, 73, 44,
    -9, 17, 19, 53, 37, 69, 18, 22,
    -13, 4, 16, 13, 28, 19, 21, -8,
    -23, -9, 12, 10, 19, 17, 25, -16,
    -29, -53, -12, -3, -1, 18, -14, -19,
    -105, -21, -58, -33, -17, -28, -19, -23,
]

PST_KNIGHT_EG = [
    -58, -38, -13, -28, -31, -27, -63, -99,
    -25, -8, -25, -2, -9, -25, -24, -52,
    -24, -20, 10, 9, -1, -9, -19, -41,
    -17, 3, 22, 22, 22, 11, 8, -18,
    -18, -6, 16, 25, 16, 17, 4, -18,
    -23, -3, -1, 15, 10, -3, -20, -22,
    -42, -20, -10, -5, -2, -20, -23, -44,
    -29, -51, -23, -15, -22, -18, -50, -64,
]

PST_BISHOP_MG = [
    -29, 4, -82, -37, -25, -42, 7, -8,
    -26, 16, -18, -13, 30, 59, 18, -47,
    -16, 37, 43, 40, 35, 50, 37, -2,
    -4, 5, 19, 50, 37, 37, 7, -2,
    -6, 13, 13, 26, 34, 12, 10, 4,
    0, 15, 15, 15, 14, 27, 18, 10,
    4, 15, 16, 0, 7, 21, 33, 1,
    -33, -3, -14, -21, -13, -12, -39, -21,
]

PST_BISHOP_EG = [
    -14, -21, -11, -8, -7, -9, -17, -24,
    -8, -4, 7, -12, -3, -13, -4, -14,
    2, -8, 0, -1, -2, 6, 0, 4,
    -3, 9, 12, 9, 14, 10, 3, 2,
    -6, 3, 13, 19, 7, 10, -3, -9,
    -12, -3, 8, 10, 13, 3, -7, -15,
    -14, -18, -7, -1, 4, -9, -15, -27,
    -23, -9, -23, -5, -9, -16, -5, -17,
]

PST_ROOK_MG = [
    32, 42, 32, 51, 63, 9, 31, 43,
    27, 32, 58, 62, 80, 67, 26, 44,
    -5, 19, 26, 36, 17, 45, 61, 16,
    -24, -11, 7, 26, 24, 35, -8, -20,
    -36, -26, -12, -1, 9, -7, 6, -23,
    -45, -25, -16, -17, 3, 0, -5, -33,
    -44, -16, -20, -9, -1, 11, -6, -71,
    -19, -13, 1, 17, 16, 7, -37, -26,
]

PST_ROOK_EG = [
    13, 10, 18, 15, 12, 12, 8, 5,
    11, 13, 13, 11, -3, 3, 8, 3,
    7, 7, 7, 5, 4, -3, -5, -3,
    4, 3, 13, 1, 2, 1, -1, 2,
    3, 5, 8, 4, -5, -6, -8, -11,
    -4, 0, -5, -1, -7, -12, -8, -16,
    -6, -6, 0, 2, -9, -9, -11, -3,
    -9, 2, 3, -1, -5, -13, 4, -20,
]

PST_QUEEN_MG = [
    -28, 0, 29, 12, 59, 44, 43, 45,
    -24, -39, -5, 1, -16, 57, 28, 54,
    -13, -17, 7, 8, 29, 56, 47, 57,
    -27, -27, -16, -16, -1, 17, -2, 1,
    -9, -26, -9, -10, -2, -4, 3, -3,
    -14, 2, -11, -2, -5, 2, 14, 5,
    -35, -8, 11, 2, 8, 15, -3, 1,
    -1, -18, -9, 10, -15, -25, -48, -18,
]

PST_QUEEN_EG = [
    -9, 22, 22, 27, 27, 19, 10, 20,
    -17, 20, 32, 41, 58, 25, 30, 0,
    -20, 6, 9, 49, 47, 35, 19, 9,
    3, 22, 24, 45, 57, 40, 57, 36,
    -18, 28, 19, 47, 31, 34, 39, 18,
    -16, -27, 15, 6, 9, 17, 10, 5,
    -22, -23, -30, -16, -16, -23, -36, -32,
    -33, -28, -22, -43, -5, -32, -20, -41,
]

PST_KING_MG = [
    -65, 23, 16, -15, -56, -34, 2, 13,
    29, -1, -20, -7, -8, -4, -38, -29,
    -9, 24, 2, -16, -20, 6, 22, -22,
    -17, -20, -12, -27, -30, -25, -14, -36,
    -49, -1, -27, -39, -46, -44, -33, -51,
    -14, -14, -22, -46, -44, -30, -15, -27,
    1, 7, -8, -64, -43, -16, 9, 8,
    -15, 36, 12, -54, 8, -28, 24, 14,
]

PST_KING_EG = [
    -74, -35, -18, -18, -11, 15, 4, -17,
    -12, 17, 14, 17, 17, 38, 23, 11,
    10, 17, 23, 15, 20, 45, 44, 13,
    -8, 22, 24, 27, 26, 33, 26, 3,
    -18, -4, 21, 24, 27, 23, 9, -11,
    -19, -3, 11, 21, 23, 16, 7, -9,
    -27, -11, 4, 13, 14, 4, -5, -17,
    -53, -34, -21, -11, -28, -14, -24, -43,
]

PST_MG = {
    chess.PAWN: PST_PAWN_MG,
    chess.KNIGHT: PST_KNIGHT_MG,
    chess.BISHOP: PST_BISHOP_MG,
    chess.ROOK: PST_ROOK_MG,
    chess.QUEEN: PST_QUEEN_MG,
    chess.KING: PST_KING_MG,
}

PST_EG = {
    chess.PAWN: PST_PAWN_EG,
    chess.KNIGHT: PST_KNIGHT_EG,
    chess.BISHOP: PST_BISHOP_EG,
    chess.ROOK: PST_ROOK_EG,
    chess.QUEEN: PST_QUEEN_EG,
    chess.KING: PST_KING_EG,
}

# 3. PRECOMPUTED BITBOARD MASKS

FILE_MASKS = [0] * 8
ADJACENT_FILE_MASKS = [0] * 8
WHITE_PASSED_MASKS = [0] * 64
BLACK_PASSED_MASKS = [0] * 64

for f in range(8):
    f_mask = sum(1 << chess.square(f, r) for r in range(8))
    FILE_MASKS[f] = f_mask

for f in range(8):
    adj = 0
    if f > 0:
        adj |= FILE_MASKS[f - 1]
    if f < 7:
        adj |= FILE_MASKS[f + 1]
    ADJACENT_FILE_MASKS[f] = adj

for sq in range(64):
    f = chess.square_file(sq)
    r = chess.square_rank(sq)

    w_mask = 0
    for offset in (-1, 0, 1):
        nf = f + offset
        if 0 <= nf <= 7:
            for nr in range(r + 1, 8):
                w_mask |= (1 << chess.square(nf, nr))
    WHITE_PASSED_MASKS[sq] = w_mask

    b_mask = 0
    for offset in (-1, 0, 1):
        nf = f + offset
        if 0 <= nf <= 7:
            for nr in range(0, r):
                b_mask |= (1 << chess.square(nf, nr))
    BLACK_PASSED_MASKS[sq] = b_mask

PASSED_BONUS_MG = [0, 5, 10, 20, 35, 60, 100, 0]
PASSED_BONUS_EG = [0, 10, 20, 40, 75, 130, 210, 0]

# 4. ENGINE STATE & DATA STRUCTURES

class SearchTimeoutException(Exception):
    pass


class EngineContext:
    def __init__(self):
        # Transposition Table: hash -> (depth, flag, score, best_move)
        self.tt: Dict[int, Tuple[int, int, int, Optional[chess.Move]]] = {}
        self.max_tt_entries = 120000

        # Killer moves: [ply][0 or 1]
        self.killer_1: List[Optional[chess.Move]] = [None] * 128
        self.killer_2: List[Optional[chess.Move]] = [None] * 128

        # History table: [from_square][to_square]
        self.history: List[List[int]] = [[0] * 64 for _ in range(64)]

        # Search runtime state
        self.nodes_visited = 0
        self.end_time = 0.0

    def reset_for_move(self, budget_time: float):
        if len(self.tt) > self.max_tt_entries:
            self.tt.clear()
        self.killer_1 = [None] * 128
        self.killer_2 = [None] * 128
        self.history = [[0] * 64 for _ in range(64)]
        self.nodes_visited = 0
        self.end_time = time.time() + budget_time


ENGINE = EngineContext()

# 6. TAPERED EVALUATION ENGINE

def score_position(board: chess.Board) -> int:
    """
    Computes a tapered positional score from the perspective of White.
    Interpolates between Middlegame and Endgame weights according to game phase.
    """
    mg_score = 0
    eg_score = 0
    phase = 0

    w_pawns = board.pieces_mask(chess.PAWN, chess.WHITE)
    b_pawns = board.pieces_mask(chess.PAWN, chess.BLACK)

    # 1. Material and Piece-Square Table calculation
    for pt in range(1, 7):
        w_mask = board.pieces_mask(pt, chess.WHITE)
        b_mask = board.pieces_mask(pt, chess.BLACK)

        w_count = w_mask.bit_count()
        b_count = b_mask.bit_count()

        phase += (w_count + b_count) * PHASE_WEIGHT[pt]

        mg_score += w_count * MG_VAL[pt] - b_count * MG_VAL[pt]
        eg_score += w_count * EG_VAL[pt] - b_count * EG_VAL[pt]

        pst_mg = PST_MG[pt]
        pst_eg = PST_EG[pt]

        # White pieces (PST indexed with sq ^ 56 for rank-8 visual tables)
        temp_w = w_mask
        while temp_w:
            sq = (temp_w & -temp_w).bit_length() - 1
            temp_w &= temp_w - 1
            idx = sq ^ 56
            mg_score += pst_mg[idx]
            eg_score += pst_eg[idx]

        # Black pieces (PST indexed directly with sq)
        temp_b = b_mask
        while temp_b:
            sq = (temp_b & -temp_b).bit_length() - 1
            temp_b &= temp_b - 1
            mg_score -= pst_mg[sq]
            eg_score -= pst_eg[sq]

    # Bound game phase between 0 and 24
    phase = min(24, max(0, phase))

    # 2. Bishop Pair Bonus
    if board.pieces_mask(chess.BISHOP, chess.WHITE).bit_count() >= 2:
        mg_score += 35
        eg_score += 50
    if board.pieces_mask(chess.BISHOP, chess.BLACK).bit_count() >= 2:
        mg_score -= 35
        eg_score -= 50

    # 3. Pawn Structure (Passed, Doubled, Isolated)
    # White Pawns
    temp_w_p = w_pawns
    while temp_w_p:
        sq = (temp_w_p & -temp_w_p).bit_length() - 1
        temp_w_p &= temp_w_p - 1
        if not (b_pawns & WHITE_PASSED_MASKS[sq]):
            r = chess.square_rank(sq)
            mg_score += PASSED_BONUS_MG[r]
            eg_score += PASSED_BONUS_EG[r]

    # Black Pawns
    temp_b_p = b_pawns
    while temp_b_p:
        sq = (temp_b_p & -temp_b_p).bit_length() - 1
        temp_b_p &= temp_b_p - 1
        if not (w_pawns & BLACK_PASSED_MASKS[sq]):
            r = 7 - chess.square_rank(sq)
            mg_score -= PASSED_BONUS_MG[r]
            eg_score -= PASSED_BONUS_EG[r]

    for f in range(8):
        # White doubled & isolated
        w_cnt = (w_pawns & FILE_MASKS[f]).bit_count()
        if w_cnt > 1:
            mg_score -= (w_cnt - 1) * 15
            eg_score -= (w_cnt - 1) * 25
        if w_cnt > 0 and not (w_pawns & ADJACENT_FILE_MASKS[f]):
            mg_score -= w_cnt * 15
            eg_score -= w_cnt * 20

        # Black doubled & isolated
        b_cnt = (b_pawns & FILE_MASKS[f]).bit_count()
        if b_cnt > 1:
            mg_score -= (b_cnt - 1) * 15
            eg_score -= (b_cnt - 1) * 25
        if b_cnt > 0 and not (b_pawns & ADJACENT_FILE_MASKS[f]):
            mg_score -= b_cnt * 15
            eg_score -= b_cnt * 20

    # 4. Rooks on Open / Semi-Open Files
    w_rooks = board.pieces_mask(chess.ROOK, chess.WHITE)
    while w_rooks:
        sq = (w_rooks & -w_rooks).bit_length() - 1
        w_rooks &= w_rooks - 1
        f = chess.square_file(sq)
        if not (w_pawns & FILE_MASKS[f]):
            if not (b_pawns & FILE_MASKS[f]):
                mg_score += 25
                eg_score += 20
            else:
                mg_score += 15
                eg_score += 10

    b_rooks = board.pieces_mask(chess.ROOK, chess.BLACK)
    while b_rooks:
        sq = (b_rooks & -b_rooks).bit_length() - 1
        b_rooks &= b_rooks - 1
        f = chess.square_file(sq)
        if not (b_pawns & FILE_MASKS[f]):
            if not (w_pawns & FILE_MASKS[f]):
                mg_score -= 25
                eg_score -= 20
            else:
                mg_score -= 15
                eg_score -= 10

    # 5. King Pawn Shield in Middlegame
    if phase > 12:
        wk = board.king(chess.WHITE)
        if wk is not None:
            if wk in (chess.G1, chess.H1):
                shield = 0
                if w_pawns & (1 << chess.F2): shield += 15
                if w_pawns & (1 << chess.G2): shield += 20
                if w_pawns & (1 << chess.H2): shield += 15
                mg_score += shield - 45
            elif wk in (chess.B1, chess.C1):
                shield = 0
                if w_pawns & (1 << chess.A2): shield += 15
                if w_pawns & (1 << chess.B2): shield += 20
                if w_pawns & (1 << chess.C2): shield += 15
                mg_score += shield - 45

        bk = board.king(chess.BLACK)
        if bk is not None:
            if bk in (chess.G8, chess.H8):
                shield = 0
                if b_pawns & (1 << chess.F7): shield += 15
                if b_pawns & (1 << chess.G7): shield += 20
                if b_pawns & (1 << chess.H7): shield += 15
                mg_score -= (shield - 45)
            elif bk in (chess.B8, chess.C8):
                shield = 0
                if b_pawns & (1 << chess.A7): shield += 15
                if b_pawns & (1 << chess.B7): shield += 20
                if b_pawns & (1 << chess.C7): shield += 15
                mg_score -= (shield - 45)

    # 6. Endgame Mop-Up Evaluation
    if phase <= 6:
        wk = board.king(chess.WHITE)
        bk = board.king(chess.BLACK)
        if wk is not None and bk is not None:
            w_majors = (
                board.pieces_mask(chess.QUEEN, chess.WHITE).bit_count() * 950 +
                board.pieces_mask(chess.ROOK, chess.WHITE).bit_count() * 500 +
                board.pieces_mask(chess.BISHOP, chess.WHITE).bit_count() * 320 +
                board.pieces_mask(chess.KNIGHT, chess.WHITE).bit_count() * 300
            )
            b_majors = (
                board.pieces_mask(chess.QUEEN, chess.BLACK).bit_count() * 950 +
                board.pieces_mask(chess.ROOK, chess.BLACK).bit_count() * 500 +
                board.pieces_mask(chess.BISHOP, chess.BLACK).bit_count() * 320 +
                board.pieces_mask(chess.KNIGHT, chess.BLACK).bit_count() * 300
            )

            wk_f, wk_r = chess.square_file(wk), chess.square_rank(wk)
            bk_f, bk_r = chess.square_file(bk), chess.square_rank(bk)

            if w_majors >= b_majors + 300:
                enemy_center_dist = max(abs(2 * bk_f - 7), abs(2 * bk_r - 7))
                kings_dist = max(abs(wk_f - bk_f), abs(wk_r - bk_r))
                eg_score += (enemy_center_dist * 45) + ((14 - kings_dist) * 25)
            elif b_majors >= w_majors + 300:
                enemy_center_dist = max(abs(2 * wk_f - 7), abs(2 * wk_r - 7))
                kings_dist = max(abs(wk_f - bk_f), abs(wk_r - bk_r))
                eg_score -= (enemy_center_dist * 45) + ((14 - kings_dist) * 25)

    # 7. Tapered Interpolation
    total_score = (mg_score * phase + eg_score * (24 - phase)) // 24
    return total_score if board.turn == chess.WHITE else -total_score


# 7. MOVE ORDERING

def order_moves(board: chess.Board, moves: List[chess.Move], tt_move: Optional[chess.Move], ply: int) -> List[chess.Move]:
    """Sorts legal moves: Hash Move -> MVV-LVA Captures -> Promos -> Killers -> History."""
    k1 = ENGINE.killer_1[ply] if ply < 128 else None
    k2 = ENGINE.killer_2[ply] if ply < 128 else None

    def move_priority(m: chess.Move) -> int:
        if m == tt_move:
            return 10000000

        score = 0
        if board.is_capture(m):
            victim = board.piece_at(m.to_square)
            attacker = board.piece_at(m.from_square)
            v_val = MG_VAL.get(victim.piece_type, 100) if victim else 100
            a_val = MG_VAL.get(attacker.piece_type, 100) if attacker else 100
            score = 1000000 + (v_val * 10) - a_val
        elif m.promotion:
            score = 900000 if m.promotion == chess.QUEEN else 500000
        elif m == k1:
            score = 50000
        elif m == k2:
            score = 40000
        else:
            score = min(ENGINE.history[m.from_square][m.to_square], 30000)

        return score

    return sorted(moves, key=move_priority, reverse=True)


# 8. QUIESCENCE SEARCH

def quiescence(board: chess.Board, alpha: int, beta: int, ply: int, max_ply: int = 14) -> int:
    """Evaluates capture sequences and check evasions until a quiet position is reached."""
    ENGINE.nodes_visited += 1
    if (ENGINE.nodes_visited & 1023) == 0:
        if time.time() >= ENGINE.end_time:
            raise SearchTimeoutException()

    in_check = board.is_check()

    if in_check:
        legal_evasions = list(board.legal_moves)
        if not legal_evasions:
            return -MATE_SCORE + ply

        ordered = order_moves(board, legal_evasions, None, ply)
        for move in ordered:
            board.push(move)
            try:
                val = -quiescence(board, -beta, -alpha, ply + 1, max_ply)
            finally:
                board.pop()

            if val >= beta:
                return beta
            if val > alpha:
                alpha = val
        return alpha

    stand_pat = score_position(board)
    if stand_pat >= beta:
        return beta
    if stand_pat > alpha:
        alpha = stand_pat

    if ply >= max_ply:
        return stand_pat

    DELTA_MARGIN = 1100
    if stand_pat < alpha - DELTA_MARGIN:
        return alpha

    captures = [m for m in board.legal_moves if board.is_capture(m) or m.promotion]
    if not captures:
        return alpha

    ordered_captures = order_moves(board, captures, None, ply)

    for move in ordered_captures:
        board.push(move)
        try:
            val = -quiescence(board, -beta, -alpha, ply + 1, max_ply)
        finally:
            board.pop()

        if val >= beta:
            return beta
        if val > alpha:
            alpha = val

    return alpha


# 9. NEGAMAX SEARCH WITH ALPHA-BETA PRUNING

def negamax(board: chess.Board, depth: int, alpha: int, beta: int, ply: int, is_root: bool = False) -> int:
    ENGINE.nodes_visited += 1
    if (ENGINE.nodes_visited & 1023) == 0:
        if time.time() >= ENGINE.end_time:
            raise SearchTimeoutException()

    # Repetition & 50-move rule draw check
    if not is_root and (board.is_repetition(2) or board.can_claim_fifty_moves()):
        static_s = score_position(board)
        if static_s > 150:
            return -50
        elif static_s < -150:
            return 50
        return 0

    in_check = board.is_check()
    if in_check:
        depth += 1

    if depth <= 0 or board.is_game_over():
        if board.is_checkmate():
            return -MATE_SCORE + ply
        if board.is_stalemate() or board.is_insufficient_material():
            static_s = score_position(board)
            if static_s > 150:
                return -100
            elif static_s < -150:
                return 100
            return 0
        return quiescence(board, alpha, beta, ply)

    orig_alpha = alpha
    zobrist_key = chess.polyglot.zobrist_hash(board)
    tt_entry = ENGINE.tt.get(zobrist_key)
    tt_move = None

    if tt_entry is not None:
        tt_depth, tt_flag, tt_score, tt_move = tt_entry

        if tt_score > MATE_THRESHOLD:
            tt_score -= ply
        elif tt_score < -MATE_THRESHOLD:
            tt_score += ply

        if not is_root and tt_depth >= depth:
            if tt_flag == FLAG_EXACT:
                return tt_score
            elif tt_flag == FLAG_LOWERBOUND:
                alpha = max(alpha, tt_score)
            elif tt_flag == FLAG_UPPERBOUND:
                beta = min(beta, tt_score)
            if alpha >= beta:
                return tt_score

    # Null-Move Pruning (NMP)
    if (
        not is_root and
        not in_check and
        depth >= 3 and
        score_position(board) >= beta
    ):
        has_major_pieces = bool(
            board.pieces_mask(chess.KNIGHT, board.turn) |
            board.pieces_mask(chess.BISHOP, board.turn) |
            board.pieces_mask(chess.ROOK, board.turn) |
            board.pieces_mask(chess.QUEEN, board.turn)
        )
        if has_major_pieces:
            board.push(chess.Move.null())
            try:
                null_val = -negamax(board, depth - 1 - 2, -beta, -beta + 1, ply + 1, False)
            finally:
                board.pop()
            if null_val >= beta:
                return beta

    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return (-MATE_SCORE + ply) if in_check else 0

    ordered_moves = order_moves(board, legal_moves, tt_move, ply)

    best_score = -INFINITY
    best_move = ordered_moves[0]
    moves_searched = 0

    for move in ordered_moves:
        board.push(move)
        moves_searched += 1

        try:
            is_capture_or_promo = board.is_capture(move) or move.promotion
            gives_check = board.is_check()

            if (
                depth >= 3 and
                moves_searched >= 4 and
                not in_check and
                not is_capture_or_promo and
                not gives_check
            ):
                reduced_depth = max(1, depth - 2)
                score = -negamax(board, reduced_depth, -alpha - 1, -alpha, ply + 1, False)
                if score > alpha:
                    score = -negamax(board, depth - 1, -beta, -alpha, ply + 1, False)
            else:
                score = -negamax(board, depth - 1, -beta, -alpha, ply + 1, False)
        finally:
            board.pop()

        if score > best_score:
            best_score = score
            best_move = move

        if score > alpha:
            alpha = score

        if alpha >= beta:
            if not is_capture_or_promo and ply < 128:
                if move != ENGINE.killer_1[ply]:
                    ENGINE.killer_2[ply] = ENGINE.killer_1[ply]
                    ENGINE.killer_1[ply] = move
                ENGINE.history[move.from_square][move.to_square] += depth * depth
            break

    tt_flag = FLAG_EXACT
    if best_score <= orig_alpha:
        tt_flag = FLAG_UPPERBOUND
    elif best_score >= beta:
        tt_flag = FLAG_LOWERBOUND

    stored_score = best_score
    if stored_score > MATE_THRESHOLD:
        stored_score += ply
    elif stored_score < -MATE_THRESHOLD:
        stored_score -= ply

    ENGINE.tt[zobrist_key] = (depth, tt_flag, stored_score, best_move)
    return best_score


# 10. MAIN TOURNAMENT INTERFACE (get_move)

def get_move(board: chess.Board, time_limit: float = 0.20) -> chess.Move:
    """
    Required hackathon interface:
    Takes a chess.Board and returns the chosen chess.Move within time_limit.
    Leaves the caller's board object completely untouched.
    """
    # 0. Defensive check: Never mutate caller board
    search_board = board.copy()
    legal_moves = list(search_board.legal_moves)
    if not legal_moves:
        return None

    if len(legal_moves) == 1:
        return legal_moves[0]

    # 1. Ultra-Bullet Time Budget Setup (~0.14s max on 0.20s limit)
    safe_budget = min(max(time_limit * 0.70, 0.04), 0.14)
    ENGINE.reset_for_move(safe_budget)

    best_move_completed_depth = legal_moves[0]

    try:
        # Iterative Deepening from depth 1 up to depth 25
        for target_depth in range(1, 26):
            if time.time() >= ENGINE.end_time:
                break

            ordered_root_moves = order_moves(
                search_board,
                legal_moves,
                best_move_completed_depth,
                ply=0
            )

            root_alpha = -INFINITY
            root_beta = INFINITY
            current_depth_best_move = ordered_root_moves[0]
            current_depth_best_score = -INFINITY

            for m in ordered_root_moves:
                search_board.push(m)
                try:
                    val = -negamax(search_board, target_depth - 1, -root_beta, -root_alpha, ply=1, is_root=False)
                finally:
                    search_board.pop()

                if val > current_depth_best_score:
                    current_depth_best_score = val
                    current_depth_best_move = m

                if val > root_alpha:
                    root_alpha = val

            # Successfully completed this depth
            best_move_completed_depth = current_depth_best_move

            # If checkmate is spotted, return immediately
            if current_depth_best_score >= MATE_THRESHOLD:
                break

            # If more than 45% of our budget is spent, avoid starting next depth
            if time.time() - (ENGINE.end_time - safe_budget) > safe_budget * 0.45:
                break

    except SearchTimeoutException:
        pass
    except Exception:
        if best_move_completed_depth not in legal_moves:
            best_move_completed_depth = legal_moves[0]

    return best_move_completed_depth
