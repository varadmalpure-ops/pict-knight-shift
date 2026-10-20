"""
PICT KNIGHT SHIFT // HARDENED SECURITY SCANNER & RUNTIME SANDBOX
Module: hackathon.security
Provides AST-level static security analysis and runtime isolation for chess bots.
"""

import ast
import os
import sys
import time
import importlib.util
import multiprocessing as mp
import chess

# POSIX memory limits
try:
    import resource
    HAS_RESOURCE = True
except ImportError:
    HAS_RESOURCE = False

# ============================================================================
# 1. STATIC AST SECURITY RULES & POLICIES
# ============================================================================

ALLOWED_MODULES = {
    "chess", "chess.polyglot", "math", "random", "time", "copy",
    "collections", "itertools", "functools", "typing", "dataclasses", "enum"
}

FORBIDDEN_CALLS = {
    "eval", "exec", "compile", "open", "__import__",
    "getattr", "setattr", "delattr", "hasattr",
    "globals", "locals", "vars", "dir", "breakpoint", "input", "print"
}

FORBIDDEN_DUNDER_ATTRS = {
    "__class__", "__base__", "__bases__", "__subclasses__",
    "__globals__", "__builtins__", "__code__", "__dict__",
    "__loader__", "__spec__", "__import__"
}

FORBIDDEN_STRING_TOKENS = {
    "subprocess", "os.system", "os.popen", "ctypes", "shutil",
    "urllib", "requests", "socket", "http", "chess.engine", "Stockfish"
}

MAX_FILE_SIZE_BYTES = 100 * 1024       # 100 KB max file size
MAX_SINGLE_LITERAL_BYTES = 4 * 1024     # 4 KB max per literal
MAX_CUMULATIVE_LITERAL_BYTES = 20 * 1024 # 20 KB cumulative constants
MEMORY_LIMIT_BYTES = 256 * 1024 * 1024   # 256 MB RAM limit


def audit_bot_source(file_path: str):
    """
    Performs comprehensive static AST analysis on a bot source file.
    Returns: (passed: bool, message: str)
    """
    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}"

    file_size = os.path.getsize(file_path)
    if file_size > MAX_FILE_SIZE_BYTES:
        return False, f"File size {file_size / 1024:.1f} KB exceeds maximum limit of 100 KB"

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
    except Exception as e:
        return False, f"Could not read source file: {e}"

    # Check for forbidden substring tokens in raw text
    source_lower = source.lower()
    for token in FORBIDDEN_STRING_TOKENS:
        if token.lower() in source_lower:
            return False, f"Forbidden token detected in file: '{token}'"

    try:
        tree = ast.parse(source, filename=file_path)
    except SyntaxError as e:
        return False, f"Syntax Error: {e}"

    has_get_move = False
    valid_signature = False
    cumulative_literal_bytes = 0

    for node in ast.walk(tree):
        # 1. Check Module Imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                base_pkg = alias.name.split('.')[0]
                if alias.name == "chess.engine" or "engine" in alias.name:
                    return False, "FORBIDDEN: 'chess.engine' is prohibited. External engines are banned."
                if base_pkg not in ALLOWED_MODULES:
                    return False, f"FORBIDDEN: Module '{alias.name}' is not in allowed list."

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                base_pkg = node.module.split('.')[0]
                if node.module == "chess.engine" or "engine" in node.module:
                    return False, "FORBIDDEN: 'chess.engine' is prohibited."
                if base_pkg not in ALLOWED_MODULES:
                    return False, f"FORBIDDEN: Module '{node.module}' is not in allowed list."

        # 2. Check Banned Calls & Reflection
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in FORBIDDEN_CALLS:
                    return False, f"FORBIDDEN: Call to '{node.func.id}()' is banned on line {node.lineno}."

        # 3. Check Dunder Attribute Access (e.g., obj.__class__, obj.__subclasses__)
        elif isinstance(node, ast.Attribute):
            if node.attr in FORBIDDEN_DUNDER_ATTRS:
                return False, f"FORBIDDEN: Dunder reflection attribute '{node.attr}' on line {node.lineno}."

        # 4. Check Literal Constant Sizes
        elif isinstance(node, ast.Constant):
            val = node.value
            lit_size = 0
            if isinstance(val, (str, bytes)):
                lit_size = len(val)
            elif isinstance(val, (list, tuple, dict, set)):
                lit_size = len(str(val))

            if lit_size > MAX_SINGLE_LITERAL_BYTES:
                return False, (
                    f"FORBIDDEN: Literal constant of size {lit_size} bytes exceeds "
                    f"single-literal limit of {MAX_SINGLE_LITERAL_BYTES} bytes (line {node.lineno})."
                )
            cumulative_literal_bytes += lit_size

        # 5. Check for Hardcoded Opening Books (Dicts of FENs or book tables)
        elif isinstance(node, ast.Dict):
            fen_key_count = 0
            for k in node.keys:
                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                    s = k.value
                    if "/" in s and ("w" in s or "b" in s) and len(s) >= 15:
                        fen_key_count += 1
            if fen_key_count >= 5:
                return False, (
                    f"FORBIDDEN: Hardcoded opening book detected ({fen_key_count} FEN entries on line {node.lineno}). "
                    f"Bots must calculate dynamically from move 1 without embedded opening lookup dictionaries."
                )

        # 6. Interface Verification
        elif isinstance(node, ast.FunctionDef):
            if node.name == "get_move":
                has_get_move = True
                arg_names = [a.arg for a in node.args.args]
                if len(arg_names) == 2 and arg_names[0] == "board" and arg_names[1] == "time_limit":
                    valid_signature = True

    if cumulative_literal_bytes > MAX_CUMULATIVE_LITERAL_BYTES:
        return False, (
            f"FORBIDDEN: Cumulative data constants ({cumulative_literal_bytes} bytes) "
            f"exceed 20 KB limit ({MAX_CUMULATIVE_LITERAL_BYTES} bytes)."
        )

    if not has_get_move:
        return False, "Required function 'def get_move(board, time_limit=1.0)' not found."
    if not valid_signature:
        return False, "Function 'get_move' must have exact signature: (board: chess.Board, time_limit: float = 1.0)."

    return True, "AST Security Audit PASSED"


# ============================================================================
# 2. RUNTIME SANDBOX & PERSISTENT WORKER PROCESS
# ============================================================================

def _sandbox_worker_loop(file_path: str, in_queue: mp.Queue, out_queue: mp.Queue):
    """
    Child process worker loop.
    Persists across moves in a single game to maintain Transposition Tables & memory.
    """
    # 1. Enforce Memory Limit
    if HAS_RESOURCE:
        try:
            resource.setrlimit(resource.RLIMIT_AS, (MEMORY_LIMIT_BYTES, MEMORY_LIMIT_BYTES))
        except Exception:
            pass

    # 2. Restrict builtins inside sandbox
    # Disallow open and print at runtime
    import builtins
    def _banned_open(*args, **kwargs):
        raise PermissionError("File open() is banned in tournament sandbox.")
    def _banned_print(*args, **kwargs):
        pass  # Silent no-op for print
    builtins.open = _banned_open
    builtins.print = _banned_print

    # 3. Load Bot Module
    try:
        mod_name = f"bot_{os.path.splitext(os.path.basename(file_path))[0]}"
        spec = importlib.util.spec_from_file_location(mod_name, file_path)
        bot_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bot_mod)

        if not hasattr(bot_mod, "get_move"):
            out_queue.put(("ERROR", "Module missing get_move"))
            return
        get_move_fn = bot_mod.get_move
        out_queue.put(("READY", None))
    except Exception as e:
        out_queue.put(("CRASH_INIT", str(e)))
        return

    # 4. Service Move Requests
    while True:
        try:
            cmd, payload = in_queue.get()
            if cmd == "QUIT":
                break

            if cmd == "MOVE":
                fen, time_limit, is_chess960 = payload
                board = chess.Board(fen, chess960=is_chess960)

                cpu_start = time.process_time()
                wall_start = time.perf_counter()

                try:
                    move = get_move_fn(board, time_limit=time_limit)
                except Exception as e:
                    out_queue.put(("CRASH_MOVE", str(e), 0.0, 0.0))
                    continue

                cpu_elapsed = time.process_time() - cpu_start
                wall_elapsed = time.perf_counter() - wall_start

                move_uci = move.uci() if (move and isinstance(move, chess.Move)) else None
                out_queue.put(("OK", move_uci, cpu_elapsed, wall_elapsed))

        except Exception as e:
            out_queue.put(("CRASH_LOOP", str(e), 0.0, 0.0))
            break


class PersistentBotClient:
    """
    Manages a persistent bot worker process for an entire match.
    Enforces time controls, memory limits, and handles process termination.
    """
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.bot_name = os.path.splitext(os.path.basename(file_path))[0]
        self.proc = None
        self.in_q = None
        self.out_q = None
        self.is_alive = False

    def start(self, timeout=3.0):
        self.in_q = mp.Queue()
        self.out_q = mp.Queue()
        self.proc = mp.Process(
            target=_sandbox_worker_loop,
            args=(self.file_path, self.in_q, self.out_q),
            daemon=True
        )
        self.proc.start()

        # Wait for ready signal
        try:
            status, payload = self.out_q.get(timeout=timeout)
            if status == "READY":
                self.is_alive = True
                return True, "Ready"
            return False, f"Failed initialization: {payload}"
        except Exception as e:
            self.stop()
            return False, f"Timeout waiting for bot to initialize ({e})"

    def query_move(self, board: chess.Board, time_limit: float = 1.0):
        if not self.is_alive or not self.proc.is_alive():
            return None, "Bot process is not running", 0.0, 0.0

        fen = board.fen()
        is_960 = board.chess960

        self.in_q.put(("MOVE", (fen, time_limit, is_960)))

        # Hard cutoff: e.g. 0.375s for 0.25s time_limit, or 1.25s for 1.0s time_limit
        hard_limit = min(time_limit + 0.15, time_limit * 1.5)

        try:
            resp = self.out_q.get(timeout=hard_limit)
            status = resp[0]
            if status == "OK":
                move_uci = resp[1]
                cpu_t = resp[2]
                wall_t = resp[3]
                if not move_uci:
                    return None, "Bot returned None", cpu_t, wall_t
                try:
                    move = chess.Move.from_uci(move_uci)
                    return move, "OK", cpu_t, wall_t
                except Exception:
                    return None, f"Invalid UCI: {move_uci}", cpu_t, wall_t
            else:
                err_msg = resp[1]
                return None, f"Crash: {err_msg}", 0.0, 0.0
        except Exception:
            # Timeout exceeded! Forfeits this game
            self.stop()
            return None, f"Hard Timeout (> {hard_limit:.2f}s)", time_limit, hard_limit

    def stop(self):
        self.is_alive = False
        if self.in_q:
            try:
                self.in_q.put(("QUIT", None))
            except Exception:
                pass
        if self.proc and self.proc.is_alive():
            self.proc.terminate()
            self.proc.join(timeout=0.5)
            if self.proc.is_alive():
                self.proc.kill()
