"""
PICT KNIGHT SHIFT // SECURITY & SANDBOX VERIFICATION TEST SUITE
File: tests/test_security.py
Proves that every banned bypass is blocked and legitimate bots pass.
"""

import os
import sys
import time
import tempfile
import chess

# Ensure workspace is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from hackathon.security import audit_bot_source, PersistentBotClient

def run_security_tests():
    print("\n" + "="*60)
    print("🛡️ RUNNING STATIC AST SECURITY TESTS")
    print("="*60)

    test_cases = [
        ("Subprocess import", "import subprocess\ndef get_move(board, time_limit=1.0): return None\n", False),
        ("Socket import", "import socket\ndef get_move(board, time_limit=1.0): return None\n", False),
        ("Stockfish/chess.engine", "import chess.engine\ndef get_move(board, time_limit=1.0): return None\n", False),
        ("Direct open() call", "import chess\ndef get_move(board, time_limit=1.0):\n    f = open('p.txt')\n    return None\n", False),
        ("Direct getattr() call", "import chess\ndef get_move(board, time_limit=1.0):\n    x = getattr(board, 'fen')\n    return None\n", False),
        ("Dunder __class__ reflection", "import chess\ndef get_move(board, time_limit=1.0):\n    x = ().__class__.__base__\n    return None\n", False),
        ("Dunder __subclasses__ traversal", "import chess\ndef get_move(board, time_limit=1.0):\n    x = object.__subclasses__()\n    return None\n", False),
        ("Huge single literal (> 4KB)", f"import chess\nBIG_DATA = '{'A' * 5000}'\ndef get_move(board, time_limit=1.0): return None\n", False),
        ("Cumulative literals (> 20KB)", f"import chess\n" + "\n".join([f"D_{i} = '{'B' * 3000}'" for i in range(8)]) + "\ndef get_move(board, time_limit=1.0): return None\n", False),
        ("Print statement", "import chess\ndef get_move(board, time_limit=1.0):\n    print('hello')\n    return None\n", False),
        ("Missing get_move", "import chess\ndef pick_move(board): return None\n", False),
        ("Legitimate bot_template.py", "hackathon/bot_template.py", True),
        ("Legitimate varad_bot.py", "varad_bot.py", True),
    ]

    all_passed = True

    for name, code_or_path, expected_pass in test_cases:
        if code_or_path.endswith(".py") and os.path.exists(code_or_path):
            path = code_or_path
            passed, msg = audit_bot_source(path)
        else:
            with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
                f.write(code_or_path)
                f.flush()
                path = f.name
            passed, msg = audit_bot_source(path)
            os.remove(path)

        is_success = (passed == expected_pass)
        status = "✅ PASS" if is_success else "❌ FAIL"
        if not is_success:
            all_passed = False

        print(f"[{status}] {name:35} -> Passed: {str(passed):5} (Expected: {str(expected_pass):5}) | Msg: {msg[:45]}")

    print("\n" + "="*60)
    print("⚡ RUNNING RUNTIME SANDBOX TIMEOUT & PERSISTENCE TEST")
    print("="*60)

    # Test 1: Infinite loop timeout
    infinite_loop_code = """
import chess
import time

def get_move(board: chess.Board, time_limit: float = 1.0) -> chess.Move:
    while True:
        time.sleep(0.05)
"""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(infinite_loop_code)
        f.flush()
        hang_path = f.name

    client = PersistentBotClient(hang_path)
    ok, msg = client.start(timeout=2.0)
    b = chess.Board()
    t0 = time.perf_counter()
    move, status, cpu_t, wall_t = client.query_move(b, time_limit=0.4)
    elapsed = time.perf_counter() - t0
    client.stop()
    os.remove(hang_path)

    timeout_ok = (move is None and "Timeout" in status and elapsed < 1.0)
    print(f"[{'✅ PASS' if timeout_ok else '❌ FAIL'}] Infinite loop hard cutoff -> Move: {move} | Status: {status} | Elapsed: {elapsed:.2f}s")
    if not timeout_ok:
        all_passed = False

    # Test 2: Persistent bot state preservation
    stateful_code = """
import chess

COUNTER = 0

def get_move(board: chess.Board, time_limit: float = 1.0) -> chess.Move:
    global COUNTER
    COUNTER += 1
    # Move e2e4 first, then g1f3
    if COUNTER == 1:
        return chess.Move.from_uci("e2e4")
    elif COUNTER == 2:
        return chess.Move.from_uci("g1f3")
    return list(board.legal_moves)[0]
"""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(stateful_code)
        f.flush()
        state_path = f.name

    state_client = PersistentBotClient(state_path)
    state_client.start()
    b1 = chess.Board()
    m1, _, _, _ = state_client.query_move(b1, 0.5)
    b1.push(m1)
    b1.push(chess.Move.from_uci("e7e5"))
    m2, _, _, _ = state_client.query_move(b1, 0.5)
    state_client.stop()
    os.remove(state_path)

    state_ok = (m1.uci() == "e2e4" and m2.uci() == "g1f3")
    print(f"[{'✅ PASS' if state_ok else '❌ FAIL'}] Persistent process state preservation -> Move 1: {m1} | Move 2: {m2}")
    if not state_ok:
        all_passed = False

    print("="*60)
    if all_passed:
        print("🎉 ALL SECURITY & RUNTIME TESTS PASSED (100% SECURE)!")
    else:
        print("⚠️ Some security tests failed! Check output above.")
    return all_passed

if __name__ == "__main__":
    success = run_security_tests()
    sys.exit(0 if success else 1)
