"""
PICT KNIGHT SHIFT — AGGRESSIVE GREEDY BOT
Prioritizes checkmates, winning captures, checks, and center pushes.
"""
import chess
import random

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}

def get_move(board: chess.Board, time_limit: float = 1.0) -> chess.Move:
    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return None

    best_move = random.choice(legal_moves)
    best_score = -999999

    for move in legal_moves:
        score = 0
        board.push(move)

        if board.is_checkmate():
            board.pop()
            return move  # Win instantly

        if board.is_check():
            score += 50

        board.pop()

        # Prioritize captures based on victim value
        if board.is_capture(move):
            captured_piece = board.piece_at(move.to_square)
            if captured_piece:
                score += PIECE_VALUES.get(captured_piece.piece_type, 100) * 10
            else:
                score += 100  # En passant

        # Promotion bonus
        if move.promotion:
            score += 800

        # Small random tiebreaker to avoid deterministic loops
        score += random.randint(0, 10)

        if score > best_score:
            best_score = score
            best_move = move

    return best_move
