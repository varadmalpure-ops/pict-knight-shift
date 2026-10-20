"""
PICT KNIGHT SHIFT — CHESS BOT STARTER TEMPLATE
-----------------------------------------------
Challenge: Build/optimize a Python chess bot within 1.0s time limit.
AI / Agents (Cursor, Claude, ChatGPT) are 100% encouraged!

Rules:
1. Your file MUST define a function: get_move(board, time_limit) -> chess.Move
2. Must run within time_limit (default: 1.0 second per move).
3. Allowed libraries: python-chess, math, random, time (pure Python, no external engines).
"""

import chess
import time

# Standard piece values in centipawns
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000,
}

# Bonus for controlling center squares (e4, d4, e5, d5, c4, f4, c5, f5)
CENTER_SQUARES = {
    chess.E4: 25, chess.D4: 25, chess.E5: 25, chess.D5: 25,
    chess.C4: 10, chess.F4: 10, chess.C5: 10, chess.F5: 10,
}


def evaluate_board(board: chess.Board) -> int:
    """
    Evaluates the board from the perspective of White.
    Positive score means White is winning; negative means Black is winning.
    
    PRO-TIP FOR AGENTS/VIBE-CODING:
    You can improve this by adding:
    - Piece-Square Tables (PST)
    - Mobility (number of legal moves)
    - King safety & pawn structure
    """
    if board.is_checkmate():
        return -99999 if board.turn == chess.WHITE else 99999
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is not None:
            value = PIECE_VALUES.get(piece.piece_type, 0)
            bonus = CENTER_SQUARES.get(square, 0)
            total = value + bonus
            if piece.color == chess.WHITE:
                score += total
            else:
                score -= total

    return score


def minimax(board: chess.Board, depth: int, alpha: int, beta: int, is_maximizing: bool) -> int:
    """Standard Minimax algorithm with Alpha-Beta pruning."""
    if depth == 0 or board.is_game_over():
        return evaluate_board(board)

    # Order moves: Captures first (heuristic to speed up alpha-beta cutoffs)
    legal_moves = sorted(
        board.legal_moves,
        key=lambda m: board.is_capture(m),
        reverse=True
    )

    if is_maximizing:
        max_eval = -1000000
        for move in legal_moves:
            board.push(move)
            eval_score = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = 1000000
        for move in legal_moves:
            board.push(move)
            eval_score = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval


def get_move(board: chess.Board, time_limit: float = 1.0) -> chess.Move:
    """
    The main tournament entry point.
    Given a chess.Board and a time limit in seconds, returns the best chess.Move.
    """
    start_time = time.time()
    best_move = None
    is_maximizing = (board.turn == chess.WHITE)

    # Sort moves: Check captures first
    legal_moves = sorted(
        board.legal_moves,
        key=lambda m: board.is_capture(m),
        reverse=True
    )

    if not legal_moves:
        return None

    best_move = legal_moves[0]
    best_eval = -1000000 if is_maximizing else 1000000

    # Search depth (Depth 2 or 3 is usually safe within 1.0s in pure Python)
    SEARCH_DEPTH = 2

    alpha = -1000000
    beta = 1000000

    for move in legal_moves:
        # Time check to prevent timeouts
        if time.time() - start_time > (time_limit * 0.85):
            break

        board.push(move)
        eval_score = minimax(board, SEARCH_DEPTH - 1, alpha, beta, not is_maximizing)
        board.pop()

        if is_maximizing:
            if eval_score > best_eval:
                best_eval = eval_score
                best_move = move
            alpha = max(alpha, eval_score)
        else:
            if eval_score < best_eval:
                best_eval = eval_score
                best_move = move
            beta = min(beta, eval_score)

    return best_move
