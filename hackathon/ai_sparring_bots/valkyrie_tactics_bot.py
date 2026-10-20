"""
PICT KNIGHT SHIFT // valkyrie_tactics_bot.py (Boss Bot 2: ~1750 Elo Tactical Berserker)
File Size: <= 10 KB | Compliance: AST Clean, 0 Books, 0.20s Bullet Time
Architecture: Dynamic Tactical Negamax, Zobrist TT, Aggressive Quiescence,
King Hunter Evaluation (King Zone Pressure, Piece Mobility, Attack Vectors).
"""
import chess
import chess.polyglot
import time

INF = 999999
MATE = 30000
MATE_THRESH = 28000

VALS = {chess.PAWN: 100, chess.KNIGHT: 330, chess.BISHOP: 340, chess.ROOK: 510, chess.QUEEN: 960, chess.KING: 20000}

class ValkyrieEngine:
    def __init__(self):
        self.tt = {}
        self.k1 = [None] * 64
        self.k2 = [None] * 64
        self.hist = [[0] * 64 for _ in range(64)]
        self.deadline = 0.0
        self.nodes = 0

    def reset(self, budget):
        self.deadline = time.perf_counter() + budget
        self.nodes = 0
        self.k1 = [None] * 64
        self.k2 = [None] * 64
        if len(self.tt) > 65536:
            self.tt.clear()
        for r in range(64):
            for c in range(64):
                self.hist[r][c] //= 2

    def check(self):
        self.nodes += 1
        if (self.nodes & 63) == 0 and time.perf_counter() >= self.deadline:
            raise TimeoutError()

ENG = ValkyrieEngine()

def eval_tactics(board):
    if board.is_checkmate():
        return -MATE
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    w_score, b_score = 0, 0
    wk = board.king(chess.WHITE)
    bk = board.king(chess.BLACK)
    wk_f, wk_r = (chess.square_file(wk), chess.square_rank(wk)) if wk is not None else (4, 0)
    bk_f, bk_r = (chess.square_file(bk), chess.square_rank(bk)) if bk is not None else (4, 7)

    pm = board.piece_map()
    for sq, p in pm.items():
        pt, c = p.piece_type, p.color
        v = VALS[pt]
        f, r = chess.square_file(sq), chess.square_rank(sq)

        # Tactical vector: distance to enemy king
        tgt_f, tgt_r = (bk_f, bk_r) if c == chess.WHITE else (wk_f, wk_r)
        k_dist = max(abs(f - tgt_f), abs(r - tgt_r))

        act = 0
        if pt in (chess.KNIGHT, chess.BISHOP):
            act = (7 - k_dist) * 8  # Swarm the enemy king!
        elif pt == chess.ROOK:
            act = (7 - abs(f - tgt_f)) * 6
        elif pt == chess.QUEEN:
            act = (7 - k_dist) * 10
        elif pt == chess.PAWN:
            rf = r if c == chess.WHITE else 7 - r
            act = rf * 10

        if c == chess.WHITE:
            w_score += v + act
        else:
            b_score += v + act

    # Check bonus (relentless pressure)
    if board.is_check():
        if board.turn == chess.WHITE:
            b_score += 40
        else:
            w_score += 40

    diff = w_score - b_score
    return diff if board.turn == chess.WHITE else -diff

def score_move(board, m, hash_m, ply):
    if hash_m and m == hash_m:
        return 2000000
    if board.is_capture(m):
        vic = board.piece_at(m.to_square)
        att = board.piece_at(m.from_square)
        vv = VALS[vic.piece_type] if vic else 100
        av = VALS[att.piece_type] if att else 100
        return 1000000 + vv * 12 - av
    if m.promotion:
        return 950000
    if ply < 64:
        if m == ENG.k1[ply]:
            return 800000
        if m == ENG.k2[ply]:
            return 700000
    return ENG.hist[m.from_square][m.to_square]

def order_moves(board, moves, hash_m, ply):
    s = [(score_move(board, m, hash_m, ply), m) for m in moves]
    s.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in s]

def quiescence(board, alpha, beta, qply=0):
    ENG.check()
    sp = eval_tactics(board)
    if qply >= 7 or sp >= beta:
        return sp if qply >= 7 else beta
    if sp > alpha:
        alpha = sp

    noisy = [m for m in board.legal_moves if board.is_capture(m) or m.promotion == chess.QUEEN or board.gives_check(m)]
    if not noisy:
        return alpha
    noisy = order_moves(board, noisy, None, qply)

    for m in noisy:
        board.push(m)
        try:
            val = -quiescence(board, -beta, -alpha, qply + 1)
        finally:
            board.pop()
        if val >= beta:
            return beta
        if val > alpha:
            alpha = val
    return alpha

def negamax(board, depth, alpha, beta, ply=0):
    ENG.check()
    if board.is_checkmate():
        return -MATE + ply
    if board.is_stalemate() or board.is_insufficient_material() or (ply > 0 and board.is_repetition(2)):
        return 0
    if depth <= 0:
        return quiescence(board, alpha, beta, 0)

    zkey = chess.polyglot.zobrist_hash(board)
    hash_m = None
    if zkey in ENG.tt:
        td, tf, ts, tm = ENG.tt[zkey]
        if td >= depth:
            if tf == 0:
                return ts
            elif tf == 1 and ts >= beta:
                return ts
            elif tf == 2 and ts <= alpha:
                return ts
        hash_m = tm

    legal = list(board.legal_moves)
    if not legal:
        return -MATE + ply if board.is_check() else 0

    ordered = order_moves(board, legal, hash_m, ply)
    best_s = -INF
    best_m = ordered[0]
    orig_a = alpha

    for m in ordered:
        board.push(m)
        try:
            val = -negamax(board, depth - 1, -beta, -alpha, ply + 1)
        finally:
            board.pop()

        if val > best_s:
            best_s = val
            best_m = m
        if val > alpha:
            alpha = val
        if alpha >= beta:
            if not board.is_capture(m) and ply < 64:
                if m != ENG.k1[ply]:
                    ENG.k2[ply] = ENG.k1[ply]
                    ENG.k1[ply] = m
                ENG.hist[m.from_square][m.to_square] += depth * depth
            break

    flag = 0 if orig_a < best_s < beta else (1 if best_s >= beta else 2)
    ENG.tt[zkey] = (depth, flag, best_s, best_m)
    return best_s

def get_move(board: chess.Board, time_limit: float = 0.20) -> chess.Move:
    wb = board.copy()
    legal = list(wb.legal_moves)
    if not legal:
        return None
    if len(legal) == 1:
        return legal[0]

    budget = min(max(time_limit * 0.65, 0.04), 0.13)
    ENG.reset(budget)
    best_m = legal[0]

    zkey = chess.polyglot.zobrist_hash(wb)
    hash_m = ENG.tt.get(zkey, (0, 0, 0, None))[3]

    try:
        for depth in range(1, 20):
            if time.perf_counter() >= ENG.deadline:
                break
            ordered = order_moves(wb, legal, hash_m, 0)
            cur_s = -INF
            cur_m = ordered[0]
            alpha, beta = -INF, INF

            for m in ordered:
                wb.push(m)
                try:
                    s = -negamax(wb, depth - 1, -beta, -alpha, 1)
                finally:
                    wb.pop()
                if s > cur_s:
                    cur_s = s
                    cur_m = m
                if s > alpha:
                    alpha = s

            best_m = cur_m
            hash_m = best_m
            if cur_s >= MATE_THRESH or (time.perf_counter() - (ENG.deadline - budget)) > budget * 0.50:
                break
    except TimeoutError:
        pass
    except Exception:
        if best_m not in legal:
            best_m = legal[0]

    return best_m
