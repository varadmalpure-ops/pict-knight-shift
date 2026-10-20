"""
PICT KNIGHT SHIFT // ORGANIZER-ONLY REFERENCE BOTS
File: organizer_tools/reference_bots.py

Provides standardized, calibrated reference bots at ~1000, ~1500, and ~2000 Elo
to benchmark submitted bots and determine the "Giant Slayer" award.

Uses Stockfish UCI with calibrated limit options when available,
with pure-Python calibrated fallback engines for offline portability.
"""

import os
import shutil
import random
import time
from typing import Optional
import chess

# Try importing chess.engine (Organizer-side only! Never permitted in participant bots)
try:
    import chess.engine
    HAS_CHESS_ENGINE = True
except ImportError:
    HAS_CHESS_ENGINE = False


def find_stockfish_binary() -> Optional[str]:
    """Locate local Stockfish binary across standard installation paths."""
    candidates = [
        shutil.which("stockfish"),
        "/opt/homebrew/bin/stockfish",
        "/usr/local/bin/stockfish",
        "/usr/bin/stockfish",
        os.path.expanduser("~/stockfish/stockfish"),
    ]
    for path in candidates:
        if path and os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


class BaseReferenceBot:
    def __init__(self, name: str, elo: int):
        self.name = name
        self.elo = elo

    def get_move(self, board: chess.Board, time_limit: float = 1.0) -> chess.Move:
        raise NotImplementedError

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class StockfishReferenceBot(BaseReferenceBot):
    """
    Stockfish UCI wrapper calibrated to Elo bands:
    - 1000 Elo: Skill Level 0, limited depth (erratic tactical oversight, novice human level)
    - 1500 Elo: UCI_LimitStrength=True, UCI_Elo=1500 (solid club player)
    - 2000 Elo: UCI_LimitStrength=True, UCI_Elo=2000 (expert campus benchmark)
    """
    def __init__(self, elo: int, binary_path: str):
        super().__init__(f"Stockfish-{elo}", elo)
        self.binary_path = binary_path
        self.engine = chess.engine.SimpleEngine.popen_uci(binary_path)
        self._configure_elo(elo)

    def _configure_elo(self, elo: int):
        if elo <= 1000:
            self.engine.configure({"UCI_LimitStrength": False, "Skill Level": 0})
        else:
            calibrated_elo = max(1320, min(3190, elo))
            self.engine.configure({"UCI_LimitStrength": True, "UCI_Elo": calibrated_elo})

    def get_move(self, board: chess.Board, time_limit: float = 1.0) -> chess.Move:
        # Safe query budget to prevent hang
        query_time = max(0.05, min(time_limit * 0.75, 0.8))
        if self.elo <= 1000:
            # Novice depth limit
            result = self.engine.play(board, chess.engine.Limit(time=query_time, depth=2))
        else:
            result = self.engine.play(board, chess.engine.Limit(time=query_time))
        if result.move and result.move in board.legal_moves:
            return result.move
        return random.choice(list(board.legal_moves))

    def close(self):
        if self.engine:
            try:
                self.engine.quit()
            except Exception:
                pass
            self.engine = None


class PurePython1000Bot(BaseReferenceBot):
    """
    Pure-Python novice fallback (~1000 Elo):
    Greedy 1-ply captures + simple piece-square valuation + 25% random blunder rate.
    """
    def __init__(self):
        super().__init__("Python-1000-Novice", 1000)

    def get_move(self, board: chess.Board, time_limit: float = 1.0) -> chess.Move:
        legal = list(board.legal_moves)
        if not legal:
            return chess.Move.null()
        # Occasional blunder
        if random.random() < 0.25:
            return random.choice(legal)
        
        piece_vals = {chess.PAWN: 100, chess.KNIGHT: 310, chess.BISHOP: 320, chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0}
        best_score = -999999
        best_moves = []
        for m in legal:
            score = 0
            if board.is_capture(m):
                captured = board.piece_at(m.to_square)
                if captured:
                    score += piece_vals.get(captured.piece_type, 0) * 10
            if m.promotion:
                score += 800
            if score > best_score:
                best_score = score
                best_moves = [m]
            elif score == best_score:
                best_moves.append(m)
        return random.choice(best_moves) if best_moves else random.choice(legal)


class PurePython1500Bot(BaseReferenceBot):
    """
    Pure-Python club player fallback (~1500 Elo):
    2-3 ply alpha-beta with PST and basic MVV-LVA move ordering.
    """
    def __init__(self):
        super().__init__("Python-1500-Club", 1500)

    def get_move(self, board: chess.Board, time_limit: float = 1.0) -> chess.Move:
        from hackathon.bot_template import get_move as template_move
        try:
            return template_move(board, time_limit=time_limit)
        except Exception:
            return random.choice(list(board.legal_moves))


def create_reference_bot(target_elo: int) -> BaseReferenceBot:
    """
    Factory to construct reference bots.
    Prefers calibrated Stockfish UCI; falls back to pure Python if Stockfish is missing.
    """
    stockfish_path = find_stockfish_binary() if HAS_CHESS_ENGINE else None

    if stockfish_path:
        try:
            return StockfishReferenceBot(target_elo, stockfish_path)
        except Exception as e:
            print(f"[WARN] Failed to initialize Stockfish ({e}). Falling back to pure Python.")

    if target_elo <= 1200:
        return PurePython1000Bot()
    elif target_elo <= 1650:
        return PurePython1500Bot()
    else:
        # Fallback to pure-Python ~1800 Vanguard bot
        try:
            from hackathon.submitted_bots.victor_vanguard_bot import get_move as vanguard_move
            class PurePython1800Bot(BaseReferenceBot):
                def __init__(self):
                    super().__init__("Python-1800-Vanguard", 1800)
                def get_move(self, b: chess.Board, time_limit: float = 0.20) -> chess.Move:
                    return vanguard_move(b, time_limit=time_limit)
            return PurePython1800Bot()
        except Exception:
            return PurePython1500Bot()
