"""
PICT KNIGHT SHIFT — RANDOM BASELINE BOT
Plays random legal moves. Used as a baseline sanity check.
"""
import chess
import random

def get_move(board: chess.Board, time_limit: float = 1.0) -> chess.Move:
    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return None
    return random.choice(legal_moves)
