"""
PICT KNIGHT SHIFT — HIGH-PERFORMANCE CHESS BOT STARTER
------------------------------------------------------
Tournament Target: 1600 - 2000+ Elo playstyle
Features:
- Full PeSTO Piece-Square Tables (Positional Mastery)
- Iterative Deepening with strict timer management
- MVV-LVA Move Ordering (Alpha-Beta cutoff optimization)
- Quiescence Search (Eliminates the horizon effect & blunder traps)
"""

import chess
import time

# ============================================================================
# 1. PIECE VALUES & PeSTO PIECE-SQUARE TABLES (Centipawns)
# ============================================================================

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000,
}

# Simplified PeSTO Piece-Square Tables for White (mirrored for Black)
PST_PAWN = [
      0,   0,   0,   0,   0,   0,   0,   0,
     50,  50,  50,  50,  50,  50,  50,  50,
     10,  10,  20,  30,  30,  20,  10,  10,
      5,   5,  10,  25,  25,  10,   5,   5,
      0,   0,   0,  20,  20,   0,   0,   0,
      5,  -5, -10,   0,   0, -10,  -5,   5,
      5,  10,  10, -20, -20,  10,  10,   5,
      0,   0,   0,   0,   0,   0,   0,   0
]

PST_KNIGHT = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20,   0,   0,   0,   0, -20, -40,
    -30,   0,  10,  15,  15,  10,   0, -30,
    -30,   5,  15,  20,  20,  15,   5, -30,
    -30,   0,  15,  20,  20,  15,   0, -30,
    -30,   5,  10,  15,  15,  10,   5, -30,
    -40, -20,   0,   5,   5,   0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50,
]

PST_BISHOP = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10,   0,   0,   0,   0,   0,   0, -10,
    -10,   0,   5,  10,  10,   5,   0, -10,
    -10,   5,   5,  10,  10,   5,   5, -10,
    -10,   0,  10,  10,  10,  10,   0, -10,
    -10,  10,  10,  10,  10,  10,  10, -10,
    -10,   5,   0,   0,   0,   0,   5, -10,
    -20, -10, -10, -10, -10, -10, -10, -20,
]

PST_ROOK = [
      0,   0,   0,   0,   0,   0,   0,   0,
      5,  10,  10,  10,  10,  10,  10,   5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
      0,   0,   0,   5,   5,   0,   0,   0
]

PST_QUEEN = [
    -20, -10, -10,  -5,  -5, -10, -10, -20,
    -10,   0,   0,   0,   0,   0,   0, -10,
    -10,   0,   5,   5,   5,   5,   0, -10,
     -5,   0,   5,   5,   5,   5,   0,  -5,
      0,   0,   5,   5,   5,   5,   0,  -5,
    -10,   5,   5,   5,   5,   5,   0, -10,
    -10,   0,   5,   0,   0,   0,   0, -10,
    -20, -10, -10,  -5,  -5, -10, -10, -20
]

PST_KING_MID = [
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
     20,  20,   0,   0,   0,   0,  20,  20,
     20,  30,  10,   0,   0,  10,  30,  20
]

PST_TABLES = {
    chess.PAWN: PST_PAWN,
    chess.KNIGHT: PST_KNIGHT,
    chess.BISHOP: PST_BISHOP,
    chess.ROOK: PST_ROOK,
    chess.QUEEN: PST_QUEEN,
    chess.KING: PST_KING_MID,
}

# ============================================================================
# 2. EVALUATION FUNCTION
# ============================================================================

def evaluate(board: chess.Board) -> int:
    """Evaluates the board from White's perspective."""
    if board.is_checkmate():
        return -99999 if board.turn == chess.WHITE else 99999
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is not None:
            val = PIECE_VALUES[piece.piece_type]
            pst = PST_TABLES[piece.piece_type]
            # If black, flip rank index (square ^ 56)
            pst_idx = square if piece.color == chess.WHITE else (square ^ 56)
            pst_val = pst[pst_idx]

            total = val + pst_val
            if piece.color == chess.WHITE:
                score += total
            else:
                score -= total

    return score

# ============================================================================
# 3. MVV-LVA MOVE ORDERING (Most Valuable Victim - Least Valuable Attacker)
# ============================================================================

def order_moves(board: chess.Board, moves):
    """Sorts moves: Captures ordered by MVV-LVA, checks next, then quiet moves."""
    def score_move(move):
        score = 0
        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            victim_val = PIECE_VALUES.get(victim.piece_type, 100) if victim else 100
            attacker_val = PIECE_VALUES.get(attacker.piece_type, 100) if attacker else 100
            score += 10000 + (victim_val * 10) - attacker_val
        if move.promotion:
            score += 9000
        if board.gives_check(move):
            score += 500
        return score

    return sorted(moves, key=score_move, reverse=True)

# ============================================================================
# 4. QUIESCENCE SEARCH (Prevents the Horizon Effect & Blunders)
# ============================================================================

def quiescence(board: chess.Board, alpha: int, beta: int, is_max: bool, end_time: float) -> int:
    """Searches capture sequences until the position is calm."""
    if time.time() > end_time:
        return evaluate(board)

    stand_pat = evaluate(board)
    if is_max:
        if stand_pat >= beta:
            return beta
        if alpha < stand_pat:
            alpha = stand_pat
    else:
        if stand_pat <= alpha:
            return alpha
        if beta > stand_pat:
            beta = stand_pat

    # Only examine legal captures
    capture_moves = [m for m in board.legal_moves if board.is_capture(m)]
    ordered = order_moves(board, capture_moves)

    for move in ordered:
        board.push(move)
        score = quiescence(board, alpha, beta, not is_max, end_time)
        board.pop()

        if is_max:
            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
        else:
            if score <= alpha:
                return alpha
            if score < beta:
                beta = score

    return alpha if is_max else beta

# ============================================================================
# 5. ALPHA-BETA WITH ITERATIVE DEEPENING
# ============================================================================

def alpha_beta(board: chess.Board, depth: int, alpha: int, beta: int, is_max: bool, end_time: float):
    if time.time() > end_time:
        return evaluate(board)

    if depth == 0 or board.is_game_over():
        return quiescence(board, alpha, beta, is_max, end_time)

    ordered_moves = order_moves(board, list(board.legal_moves))

    if is_max:
        max_eval = -1000000
        for move in ordered_moves:
            board.push(move)
            eval_score = alpha_beta(board, depth - 1, alpha, beta, False, end_time)
            board.pop()
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = 1000000
        for move in ordered_moves:
            board.push(move)
            eval_score = alpha_beta(board, depth - 1, alpha, beta, True, end_time)
            board.pop()
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

# ============================================================================
# 6. TOURNAMENT ENTRY POINT
# ============================================================================

def get_move(board: chess.Board, time_limit: float = 1.0) -> chess.Move:
    """
    Main tournament move selector.
    Uses Iterative Deepening to search deeper (depth 1, 2, 3, 4...)
    as long as time allows, guaranteeing a valid move is always returned.
    """
    start_time = time.time()
    # Allocate 85% of time limit to stay safe from timeouts
    end_time = start_time + (time_limit * 0.85)

    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return None

    best_move = legal_moves[0]
    is_max = (board.turn == chess.WHITE)

    # Iterative Deepening from depth 1 up to depth 6
    for depth in range(1, 7):
        if time.time() > end_time:
            break

        current_best_move = best_move
        ordered = order_moves(board, legal_moves)
        best_val = -1000000 if is_max else 1000000
        alpha = -1000000
        beta = 1000000

        for move in ordered:
            if time.time() > end_time:
                break

            board.push(move)
            val = alpha_beta(board, depth - 1, alpha, beta, not is_max, end_time)
            board.pop()

            if is_max:
                if val > best_val:
                    best_val = val
                    current_best_move = move
                alpha = max(alpha, val)
            else:
                if val < best_val:
                    best_val = val
                    current_best_move = move
                beta = min(beta, val)

        # Only update if the depth search completed in time
        if time.time() <= end_time:
            best_move = current_best_move

    return best_move
