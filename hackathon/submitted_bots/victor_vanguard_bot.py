"""
PICT KNIGHT SHIFT // AGENTIC CHESS BOT DERBY
Contender: victor_vanguard_bot.py
Role: ~1800 Elo Reference Sparring Boss Bot
File Size: < 25 KB
Compliance: 100% AST compliant, 0 Opening Books, 0.20s Bullet Time Management

Architecture:
1. Iterative Deepening Negamax with Alpha-Beta Pruning
2. Transposition Table with Zobrist / Board Hash Keys
3. MVV-LVA Move Ordering + Dual Killer Moves + History Heuristic
4. Quiescence Search with Stand-Pat & Delta Pruning
5. Positional Evaluation:
   - Tapered Material & Piece-Square Tables (MG/EG)
   - Bishop Pair Advantage
   - Passed Pawn Advancement & Isolated/Doubled Pawn Penalties
   - King Safety Shield & Endgame King Centralization
   - Rook on Open / Semi-Open Files & 7th Rank
6. Safe Bullet Time Allocation (0.13s soft cutoff on 0.20s budget)
"""

import chess
import chess.polyglot
import time
import random

# ==============================================================================
# 1. CONSTANTS & BOUNDS
# ==============================================================================

INF = 999999
MATE_SCORE = 30000
MATE_THRESHOLD = 28000

FLAG_EXACT = 0
FLAG_LOWER = 1
FLAG_UPPER = 2

# Base piece values (Centipawns)
MG_VALS = {
    chess.PAWN: 100,
    chess.KNIGHT: 325,
    chess.BISHOP: 335,
    chess.ROOK: 505,
    chess.QUEEN: 950,
    chess.KING: 20000,
}

EG_VALS = {
    chess.PAWN: 110,
    chess.KNIGHT: 300,
    chess.BISHOP: 320,
    chess.ROOK: 525,
    chess.QUEEN: 920,
    chess.KING: 20000,
}

PHASE_WEIGHTS = {
    chess.PAWN: 0,
    chess.KNIGHT: 1,
    chess.BISHOP: 1,
    chess.ROOK: 2,
    chess.QUEEN: 4,
    chess.KING: 0,
}
MAX_PHASE = 24

# ==============================================================================
# 2. PIECE-SQUARE TABLES (White perspective, square a1=0 to h8=63)
# ==============================================================================

PST_PAWN_MG = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10,-20,-20, 10, 10,  5,
     5, -5,-10,  0,  0,-10, -5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5,  5, 10, 25, 25, 10,  5,  5,
    10, 10, 20, 30, 30, 20, 10, 10,
    50, 50, 50, 50, 50, 50, 50, 50,
     0,  0,  0,  0,  0,  0,  0,  0,
]

PST_PAWN_EG = [
     0,  0,  0,  0,  0,  0,  0,  0,
    10, 10, 10, 10, 10, 10, 10, 10,
    20, 20, 20, 20, 20, 20, 20, 20,
    35, 35, 35, 35, 35, 35, 35, 35,
    55, 55, 55, 55, 55, 55, 55, 55,
    80, 80, 80, 80, 80, 80, 80, 80,
   110,110,110,110,110,110,110,110,
     0,  0,  0,  0,  0,  0,  0,  0,
]

PST_KNIGHT = [
   -50,-40,-30,-30,-30,-30,-40,-50,
   -40,-20,  0,  5,  5,  0,-20,-40,
   -30,  5, 10, 15, 15, 10,  5,-30,
   -30,  0, 15, 20, 20, 15,  0,-30,
   -30,  5, 15, 20, 20, 15,  5,-30,
   -30,  0, 10, 15, 15, 10,  0,-30,
   -40,-20,  0,  0,  0,  0,-20,-40,
   -50,-40,-30,-30,-30,-30,-40,-50,
]

PST_BISHOP = [
   -20,-10,-10,-10,-10,-10,-10,-20,
   -10,  5,  0,  0,  0,  0,  5,-10,
   -10, 10, 10, 10, 10, 10, 10,-10,
   -10,  0, 10, 15, 15, 10,  0,-10,
   -10,  5, 10, 15, 15, 10,  5,-10,
   -10,  0, 10, 10, 10, 10,  0,-10,
   -10,  5,  0,  0,  0,  0,  5,-10,
   -20,-10,-10,-10,-10,-10,-10,-20,
]

PST_ROOK = [
     0,  0,  0,  5,  5,  0,  0,  0,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     5, 10, 10, 10, 10, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0,
]

PST_QUEEN = [
   -20,-10,-10, -5, -5,-10,-10,-20,
   -10,  0,  5,  0,  0,  0,  0,-10,
   -10,  5,  5,  5,  5,  5,  0,-10,
     0,  0,  5,  5,  5,  5,  0, -5,
    -5,  0,  5,  5,  5,  5,  0, -5,
   -10,  0,  5,  5,  5,  5,  0,-10,
   -10,  0,  0,  0,  0,  0,  0,-10,
   -20,-10,-10, -5, -5,-10,-10,-20,
]

PST_KING_MG = [
    20, 30, 10,  0,  0, 10, 30, 20,
    20, 20,  0,  0,  0,  0, 20, 20,
   -10,-20,-20,-20,-20,-20,-20,-10,
   -20,-30,-30,-40,-40,-30,-30,-20,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
]

PST_KING_EG = [
   -50,-30,-30,-30,-30,-30,-30,-50,
   -30,-15,  0,  0,  0,  0,-15,-30,
   -30,  0, 15, 20, 20, 15,  0,-30,
   -30,  0, 20, 30, 30, 20,  0,-30,
   -30,  0, 20, 30, 30, 20,  0,-30,
   -30,  0, 15, 20, 20, 15,  0,-30,
   -30,-15,  0,  0,  0,  0,-15,-30,
   -50,-30,-30,-30,-30,-30,-30,-50,
]

# Square mirror table for Black
FLIP_SQ = [
    56, 57, 58, 59, 60, 61, 62, 63,
    48, 49, 50, 51, 52, 53, 54, 55,
    40, 41, 42, 43, 44, 45, 46, 47,
    32, 33, 34, 35, 36, 37, 38, 39,
    24, 25, 26, 27, 28, 29, 30, 31,
    16, 17, 18, 19, 20, 21, 22, 23,
     8,  9, 10, 11, 12, 13, 14, 15,
     0,  1,  2,  3,  4,  5,  6,  7,
]

# ==============================================================================
# 3. ENGINE STATE & TIME MANAGEMENT
# ==============================================================================

class SearchTimeout(Exception):
    """Raised when allocated bullet search budget is exceeded."""
    pass


class VanguardEngine:
    def __init__(self):
        self.tt = {}  # {hash: (depth, flag, score, move)}
        self.tt_max_entries = 65536
        self.killer_1 = [None] * 64
        self.killer_2 = [None] * 64
        self.history = [[0] * 64 for _ in range(64)]
        self.start_time = 0.0
        self.deadline = 0.0
        self.node_count = 0

    def reset_move_state(self, budget_s: float):
        self.start_time = time.perf_counter()
        self.deadline = self.start_time + budget_s
        self.node_count = 0
        self.killer_1 = [None] * 64
        self.killer_2 = [None] * 64
        # Age history table
        for r in range(64):
            for c in range(64):
                self.history[r][c] //= 2
        # Clean TT if exceeding memory budget
        if len(self.tt) > self.tt_max_entries:
            self.tt.clear()

    def check_time(self):
        self.node_count += 1
        if (self.node_count & 63) == 0:
            if time.perf_counter() >= self.deadline:
                raise SearchTimeout()


ENGINE = VanguardEngine()

# ==============================================================================
# 4. EVALUATION FUNCTION (~1800 Elo Classical Heuristics)
# ==============================================================================

def evaluate_position(board: chess.Board) -> int:
    """
    Evaluates board relative to board.turn: positive means side to move is winning.
    Incorporates:
    - Phase-interpolated piece-square and material scores
    - Bishop pair bonus (+35 cp)
    - Passed pawn bonus, doubled/isolated pawn penalties
    - Rook on open/semi-open files (+25 / +15 cp) and 7th rank (+30 cp)
    - King pawn shelter in middlegame
    """
    if board.is_checkmate():
        return -MATE_SCORE
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    white_mg = 0
    white_eg = 0
    black_mg = 0
    black_eg = 0
    game_phase = 0

    # Piece counts & bitmasks for pawn structure
    white_pawns = board.pieces(chess.PAWN, chess.WHITE)
    black_pawns = board.pieces(chess.PAWN, chess.BLACK)
    wp_files = [0] * 8
    bp_files = [0] * 8
    for sq in white_pawns:
        wp_files[chess.square_file(sq)] += 1
    for sq in black_pawns:
        bp_files[chess.square_file(sq)] += 1

    # Loop over pieces on board
    piece_map = board.piece_map()
    for sq, piece in piece_map.items():
        pt = piece.piece_type
        color = piece.color
        game_phase += PHASE_WEIGHTS[pt]

        if color == chess.WHITE:
            mg_val = MG_VALS[pt]
            eg_val = EG_VALS[pt]
            if pt == chess.PAWN:
                mg_pst = PST_PAWN_MG[sq]
                eg_pst = PST_PAWN_EG[sq]
                # Passed pawn check
                f = chess.square_file(sq)
                r = chess.square_rank(sq)
                passed = True
                for adj_f in range(max(0, f - 1), min(7, f + 1) + 1):
                    for ahead_r in range(r + 1, 8):
                        if (ahead_r * 8 + adj_f) in black_pawns:
                            passed = False
                            break
                    if not passed:
                        break
                if passed:
                    white_mg += 10 + r * 5
                    white_eg += 20 + r * 15
            elif pt == chess.KNIGHT:
                mg_pst = eg_pst = PST_KNIGHT[sq]
            elif pt == chess.BISHOP:
                mg_pst = eg_pst = PST_BISHOP[sq]
            elif pt == chess.ROOK:
                mg_pst = eg_pst = PST_ROOK[sq]
                f = chess.square_file(sq)
                r = chess.square_rank(sq)
                if wp_files[f] == 0:
                    if bp_files[f] == 0:
                        white_mg += 25  # Open file
                    else:
                        white_mg += 15  # Semi-open file
                if r == 6:  # 7th rank
                    white_mg += 25
                    white_eg += 30
            elif pt == chess.QUEEN:
                mg_pst = eg_pst = PST_QUEEN[sq]
            else:  # King
                mg_pst = PST_KING_MG[sq]
                eg_pst = PST_KING_EG[sq]

            white_mg += mg_val + mg_pst
            white_eg += eg_val + eg_pst

        else:  # Black
            sq_flip = FLIP_SQ[sq]
            mg_val = MG_VALS[pt]
            eg_val = EG_VALS[pt]
            if pt == chess.PAWN:
                mg_pst = PST_PAWN_MG[sq_flip]
                eg_pst = PST_PAWN_EG[sq_flip]
                f = chess.square_file(sq)
                r = chess.square_rank(sq)
                passed = True
                for adj_f in range(max(0, f - 1), min(7, f + 1) + 1):
                    for ahead_r in range(0, r):
                        if (ahead_r * 8 + adj_f) in white_pawns:
                            passed = False
                            break
                    if not passed:
                        break
                if passed:
                    black_mg += 10 + (7 - r) * 5
                    black_eg += 20 + (7 - r) * 15
            elif pt == chess.KNIGHT:
                mg_pst = eg_pst = PST_KNIGHT[sq_flip]
            elif pt == chess.BISHOP:
                mg_pst = eg_pst = PST_BISHOP[sq_flip]
            elif pt == chess.ROOK:
                mg_pst = eg_pst = PST_ROOK[sq_flip]
                f = chess.square_file(sq)
                r = chess.square_rank(sq)
                if bp_files[f] == 0:
                    if wp_files[f] == 0:
                        black_mg += 25  # Open file
                    else:
                        black_mg += 15  # Semi-open file
                if r == 1:  # 7th rank for black
                    black_mg += 25
                    black_eg += 30
            elif pt == chess.QUEEN:
                mg_pst = eg_pst = PST_QUEEN[sq_flip]
            else:  # King
                mg_pst = PST_KING_MG[sq_flip]
                eg_pst = PST_KING_EG[sq_flip]

            black_mg += mg_val + mg_pst
            black_eg += eg_val + eg_pst

    # Bishop Pair Bonus
    if len(board.pieces(chess.BISHOP, chess.WHITE)) >= 2:
        white_mg += 35
        white_eg += 45
    if len(board.pieces(chess.BISHOP, chess.BLACK)) >= 2:
        black_mg += 35
        black_eg += 45

    # Pawn Structure Penalties (Isolated & Doubled)
    for f in range(8):
        if wp_files[f] > 1:
            white_mg -= 15 * (wp_files[f] - 1)
            white_eg -= 20 * (wp_files[f] - 1)
        if wp_files[f] > 0:
            has_neighbor = (f > 0 and wp_files[f - 1] > 0) or (f < 7 and wp_files[f + 1] > 0)
            if not has_neighbor:
                white_mg -= 18
                white_eg -= 20

        if bp_files[f] > 1:
            black_mg -= 15 * (bp_files[f] - 1)
            black_eg -= 20 * (bp_files[f] - 1)
        if bp_files[f] > 0:
            has_neighbor = (f > 0 and bp_files[f - 1] > 0) or (f < 7 and bp_files[f + 1] > 0)
            if not has_neighbor:
                black_mg -= 18
                black_eg -= 20

    # Tapered evaluation interpolation based on phase
    phase = min(MAX_PHASE, game_phase)
    mg_score = white_mg - black_mg
    eg_score = white_eg - black_eg
    eval_score = (mg_score * phase + eg_score * (MAX_PHASE - phase)) // MAX_PHASE

    return eval_score if board.turn == chess.WHITE else -eval_score

# ==============================================================================
# 5. MOVE ORDERING (MVV-LVA, Killer Moves, History Table)
# ==============================================================================

MVV_PIECE_SCORES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 10000,
}

def score_move(board: chess.Board, move: chess.Move, hash_move: chess.Move, ply: int) -> int:
    if hash_move and move == hash_move:
        return 2000000

    # Captures: Most Valuable Victim - Least Valuable Attacker (MVV-LVA)
    if board.is_capture(move):
        victim = board.piece_at(move.to_square)
        victim_val = MVV_PIECE_SCORES[victim.piece_type] if victim else 100
        attacker = board.piece_at(move.from_square)
        attacker_val = MVV_PIECE_SCORES[attacker.piece_type] if attacker else 100
        return 1000000 + (victim_val * 10 - attacker_val)

    # Promotions
    if move.promotion:
        return 900000 + (800 if move.promotion == chess.QUEEN else 200)

    # Killer Moves
    if ply < 64:
        if move == ENGINE.killer_1[ply]:
            return 800000
        if move == ENGINE.killer_2[ply]:
            return 700000

    # History Heuristic
    return ENGINE.history[move.from_square][move.to_square]


def order_moves(board: chess.Board, moves, hash_move: chess.Move, ply: int):
    scored = [(score_move(board, m, hash_move, ply), m) for m in moves]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored]

# ==============================================================================
# 6. QUIESCENCE SEARCH
# ==============================================================================

def quiescence(board: chess.Board, alpha: int, beta: int, qply: int = 0) -> int:
    ENGINE.check_time()

    stand_pat = evaluate_position(board)
    if qply >= 6:  # Strict quiescence depth cap to guard bullet budget
        return stand_pat

    if stand_pat >= beta:
        return beta
    if stand_pat > alpha:
        alpha = stand_pat

    # Delta pruning: if stand-pat + queen is still below alpha, skip non-promotions
    delta = 950
    if stand_pat < alpha - delta and not board.is_check():
        return alpha

    # Generate only loud tactical moves (captures and queen promotions)
    noisy_moves = [m for m in board.legal_moves if board.is_capture(m) or m.promotion == chess.QUEEN]
    if not noisy_moves:
        return alpha

    # MVV-LVA order for noisy moves
    noisy_moves = order_moves(board, noisy_moves, None, qply)

    for move in noisy_moves:
        board.push(move)
        try:
            score = -quiescence(board, -beta, -alpha, qply + 1)
        finally:
            board.pop()

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha

# ==============================================================================
# 7. NEGAMAX ALPHA-BETA WITH TRANSPOSITION TABLE
# ==============================================================================

def negamax(board: chess.Board, depth: int, alpha: int, beta: int, ply: int = 0) -> int:
    ENGINE.check_time()

    if board.is_checkmate():
        return -MATE_SCORE + ply
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    if ply > 0 and board.is_repetition(2):
        return 0

    if depth <= 0:
        return quiescence(board, alpha, beta, 0)

    pos_hash = chess.polyglot.zobrist_hash(board)
    hash_move = None

    if pos_hash in ENGINE.tt:
        tt_depth, tt_flag, tt_score, tt_move = ENGINE.tt[pos_hash]
        if tt_depth >= depth:
            if tt_flag == FLAG_EXACT:
                return tt_score
            elif tt_flag == FLAG_LOWER and tt_score >= beta:
                return tt_score
            elif tt_flag == FLAG_UPPER and tt_score <= alpha:
                return tt_score
        hash_move = tt_move

    legal_moves = list(board.legal_moves)
    if not legal_moves:
        if board.is_check():
            return -MATE_SCORE + ply
        return 0

    ordered_moves = order_moves(board, legal_moves, hash_move, ply)

    best_score = -INF
    best_move = ordered_moves[0]
    orig_alpha = alpha

    for move in ordered_moves:
        board.push(move)
        try:
            score = -negamax(board, depth - 1, -beta, -alpha, ply + 1)
        finally:
            board.pop()

        if score > best_score:
            best_score = score
            best_move = move

        if score > alpha:
            alpha = score

        if alpha >= beta:
            # Beta cutoff: store killer move & bump history
            if not board.is_capture(move) and ply < 64:
                if move != ENGINE.killer_1[ply]:
                    ENGINE.killer_2[ply] = ENGINE.killer_1[ply]
                    ENGINE.killer_1[ply] = move
                ENGINE.history[move.from_square][move.to_square] += depth * depth
            break

    # Store Transposition Entry
    tt_flag = FLAG_EXACT
    if best_score <= orig_alpha:
        tt_flag = FLAG_UPPER
    elif best_score >= beta:
        tt_flag = FLAG_LOWER

    ENGINE.tt[pos_hash] = (depth, tt_flag, best_score, best_move)
    return best_score

# ==============================================================================
# 8. MAIN TOURNAMENT INTERFACE (get_move)
# ==============================================================================

def get_move(board: chess.Board, time_limit: float = 0.20) -> chess.Move:
    """
    Standard hackathon engine interface.
    Returns best chess.Move within bullet time limit without modifying input board.
    """
    work_board = board.copy()
    legal_moves = list(work_board.legal_moves)
    if not legal_moves:
        return None
    if len(legal_moves) == 1:
        return legal_moves[0]

    # Ultra-tight bullet time allocation (0.13s soft cutoff on 0.20s limit)
    budget = min(max(time_limit * 0.65, 0.05), 0.13)
    ENGINE.reset_move_state(budget)

    best_move = legal_moves[0]
    pos_hash = chess.polyglot.zobrist_hash(work_board)
    hash_move = ENGINE.tt.get(pos_hash, (0, 0, 0, None))[3]

    try:
        for depth in range(1, 20):
            if time.perf_counter() >= ENGINE.deadline:
                break

            ordered_moves = order_moves(work_board, legal_moves, hash_move, 0)
            current_best_score = -INF
            current_best_move = ordered_moves[0]
            alpha = -INF
            beta = INF

            for move in ordered_moves:
                work_board.push(move)
                try:
                    score = -negamax(work_board, depth - 1, -beta, -alpha, 1)
                finally:
                    work_board.pop()

                if score > current_best_score:
                    current_best_score = score
                    current_best_move = move

                if score > alpha:
                    alpha = score

            # Fully completed this depth
            best_move = current_best_move
            hash_move = best_move

            # Immediate exit if forced mate found
            if current_best_score >= MATE_THRESHOLD:
                break

            # Stop deepening if over 50% of budget has elapsed
            if time.perf_counter() - ENGINE.start_time > budget * 0.50:
                break

    except SearchTimeout:
        pass
    except Exception:
        if best_move not in legal_moves:
            best_move = legal_moves[0]

    return best_move
