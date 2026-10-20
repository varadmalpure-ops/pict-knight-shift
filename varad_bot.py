"""
PICT KNIGHT SHIFT // varad_bot.py (Elite Compact Edition <= 10 KB)
Author: varadmalpure-ops
Architecture: Iterative Deepening Negamax, Alpha-Beta, Zobrist TT,
MVV-LVA, Dual Killers, History Table, Quiescence with Delta Pruning,
Tapered Procedural Evaluation (Passed Pawns, King Safety, Open Files).
"""
import chess
import chess.polyglot
import time

INF = 999999
MATE = 30000
MATE_THRESH = 28000

P_VALS = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330, chess.ROOK: 500, chess.QUEEN: 950, chess.KING: 20000}
PHASE_W = {chess.PAWN: 0, chess.KNIGHT: 1, chess.BISHOP: 1, chess.ROOK: 2, chess.QUEEN: 4, chess.KING: 0}

class EngineState:
    def __init__(self):
        self.tt = {}
        self.k1 = [None] * 64
        self.k2 = [None] * 64
        self.hist = [[0] * 64 for _ in range(64)]
        self.end_t = 0.0
        self.nodes = 0

    def reset(self, budget):
        self.end_t = time.perf_counter() + budget
        self.nodes = 0
        self.k1 = [None] * 64
        self.k2 = [None] * 64
        if len(self.tt) > 65536:
            self.tt.clear()
        for i in range(64):
            for j in range(64):
                self.hist[i][j] //= 2

    def check(self):
        self.nodes += 1
        if (self.nodes & 63) == 0 and time.perf_counter() >= self.end_t:
            raise TimeoutError()

ENG = EngineState()

def evaluate(board):
    if board.is_checkmate():
        return -MATE
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    w_mat, b_mat = 0, 0
    w_pos, b_pos = 0, 0
    phase = 0

    wp = board.pieces(chess.PAWN, chess.WHITE)
    bp = board.pieces(chess.PAWN, chess.BLACK)
    wp_files = [0] * 8
    bp_files = [0] * 8
    for sq in wp:
        wp_files[chess.square_file(sq)] += 1
    for sq in bp:
        bp_files[chess.square_file(sq)] += 1

    pm = board.piece_map()
    for sq, piece in pm.items():
        pt, c = piece.piece_type, piece.color
        val = P_VALS[pt]
        phase += PHASE_W[pt]
        f, r = chess.square_file(sq), chess.square_rank(sq)
        rf = r if c == chess.WHITE else 7 - r
        cdist = max(abs(2 * f - 7), abs(2 * r - 7))

        pos = (7 - cdist) * 4
        if pt == chess.PAWN:
            pos += rf * 8
            # Passed pawn bonus
            passed = True
            for af in range(max(0, f - 1), min(7, f + 1) + 1):
                enemy_pawns = bp if c == chess.WHITE else wp
                ranks_ahead = range(r + 1, 8) if c == chess.WHITE else range(0, r)
                if any((ar * 8 + af) in enemy_pawns for ar in ranks_ahead):
                    passed = False
                    break
            if passed:
                pos += 15 + rf * 10
        elif pt == chess.KNIGHT:
            pos = (7 - cdist) * 6
        elif pt == chess.BISHOP:
            pos = (7 - cdist) * 3
        elif pt == chess.ROOK:
            my_f = wp_files if c == chess.WHITE else bp_files
            opp_f = bp_files if c == chess.WHITE else wp_files
            if my_f[f] == 0:
                pos += 25 if opp_f[f] == 0 else 15
            if rf == 6:
                pos += 25
        elif pt == chess.KING:
            if phase > 10:
                pos = -cdist * 5  # Stay safe
            else:
                pos = (7 - cdist) * 8  # Centralize in endgame

        if c == chess.WHITE:
            w_mat += val
            w_pos += pos
        else:
            b_mat += val
            b_pos += pos

    # Bishop pair
    if len(board.pieces(chess.BISHOP, chess.WHITE)) >= 2:
        w_pos += 35
    if len(board.pieces(chess.BISHOP, chess.BLACK)) >= 2:
        b_pos += 35

    score = (w_mat + w_pos) - (b_mat + b_pos)
    return score if board.turn == chess.WHITE else -score

def score_move(board, m, hash_m, ply):
    if hash_m and m == hash_m:
        return 2000000
    if board.is_capture(m):
        vic = board.piece_at(m.to_square)
        v_val = P_VALS[vic.piece_type] if vic else 100
        att = board.piece_at(m.from_square)
        a_val = P_VALS[att.piece_type] if att else 100
        return 1000000 + v_val * 10 - a_val
    if m.promotion:
        return 900000 + (800 if m.promotion == chess.QUEEN else 200)
    if ply < 64:
        if m == ENG.k1[ply]:
            return 800000
        if m == ENG.k2[ply]:
            return 700000
    return ENG.hist[m.from_square][m.to_square]

def order_moves(board, moves, hash_m, ply):
    scored = [(score_move(board, m, hash_m, ply), m) for m in moves]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored]

def quiescence(board, alpha, beta, qply=0):
    ENG.check()
    sp = evaluate(board)
    if qply >= 6 or sp >= beta:
        return sp if qply >= 6 else beta
    if sp > alpha:
        alpha = sp

    if sp < alpha - 950 and not board.is_check():
        return alpha

    noisy = [m for m in board.legal_moves if board.is_capture(m) or m.promotion == chess.QUEEN]
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
        tdepth, tflag, tscore, tmove = ENG.tt[zkey]
        if tdepth >= depth:
            if tflag == 0:
                return tscore
            elif tflag == 1 and tscore >= beta:
                return tscore
            elif tflag == 2 and tscore <= alpha:
                return tscore
        hash_m = tmove

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
            if time.perf_counter() >= ENG.end_t:
                break
            ordered = order_moves(wb, legal, hash_m, 0)
            cur_s = -INF
            cur_m = ordered[0]
            alpha, beta = -INF, INF

            for m in ordered:
                wb.push(m)
                try:
                    score = -negamax(wb, depth - 1, -beta, -alpha, 1)
                finally:
                    wb.pop()
                if score > cur_s:
                    cur_s = score
                    cur_m = m
                if score > alpha:
                    alpha = score

            best_m = cur_m
            hash_m = best_m
            if cur_s >= MATE_THRESH or (time.perf_counter() - (ENG.end_t - budget)) > budget * 0.50:
                break
    except TimeoutError:
        pass
    except Exception:
        if best_m not in legal:
            best_m = legal[0]

    return best_m
