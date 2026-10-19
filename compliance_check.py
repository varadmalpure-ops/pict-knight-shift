"""
PICT KNIGHT SHIFT // OFFICIAL AST COMPLIANCE CHECKER
File: compliance_check.py
Validates varad_bot.py against all hackathon hard rules.
"""

import ast
import os
import inspect

ALLOWED_IMPORTS = {
    "chess", "chess.polyglot", "math", "random", "time", "copy",
    "collections", "itertools", "functools", "typing", "dataclasses", "enum"
}

FORBIDDEN_IDENTIFIERS = {
    "subprocess", "os.system", "os.popen", "ctypes", "shutil",
    "urllib", "requests", "socket", "http", "chess.engine", "Stockfish"
}

FORBIDDEN_CALLS = {"eval", "exec", "compile", "open", "__import__"}

def run_compliance(file_path: str = "varad_bot.py") -> bool:
    print("\n" + "="*60)
    print(f"🔍 RUNNING AST COMPLIANCE AUDIT ON: {file_path}")
    print("="*60)

    # 1. File Size Check
    if not os.path.exists(file_path):
        print(f"❌ FAIL: File not found: {file_path}")
        return False

    size_kb = os.path.getsize(file_path) / 1024
    if size_kb > 150:
        print(f"❌ FAIL: File size exceeds 150 KB ({size_kb:.2f} KB)")
        return False
    print(f"✅ [RULE D - PASS] File size: {size_kb:.2f} KB (Limit: 150 KB)")

    # 2. Parse Source Code
    with open(file_path, "r", encoding="utf-8") as f:
        source_code = f.read()

    try:
        tree = ast.parse(source_code, filename=file_path)
    except SyntaxError as e:
        print(f"❌ FAIL: Syntax error: {e}")
        return False

    # 3. Import & Identifier Checks
    violations = []
    found_get_move = False
    get_move_args = []

    for node in ast.walk(tree):
        # Imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                base = alias.name.split('.')[0]
                full = alias.name
                if full == "chess.engine":
                    violations.append(f"Forbidden import: {full}")
                elif base not in ALLOWED_IMPORTS:
                    violations.append(f"Unapproved import: {full}")

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                base = node.module.split('.')[0]
                if node.module == "chess.engine" or "engine" in node.module:
                    violations.append(f"Forbidden import from: {node.module}")
                elif base not in ALLOWED_IMPORTS:
                    violations.append(f"Unapproved import from: {node.module}")

        # Function Calls
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in FORBIDDEN_CALLS:
                    violations.append(f"Forbidden call: {node.func.id}() on line {node.lineno}")

        # Function Definition for get_move
        elif isinstance(node, ast.FunctionDef):
            if node.name == "get_move":
                found_get_move = True
                get_move_args = [arg.arg for arg in node.args.args]

    # Check forbidden strings in entire source text
    lower_source = source_code.lower()
    for forbidden in FORBIDDEN_IDENTIFIERS:
        if forbidden.lower() in lower_source:
            violations.append(f"Forbidden token/string detected in file: '{forbidden}'")

    if not found_get_move:
        violations.append("Missing required interface: get_move()")
    else:
        # Check signature
        if len(get_move_args) != 2 or get_move_args[0] != "board" or get_move_args[1] != "time_limit":
            violations.append(f"Incorrect get_move signature: found ({', '.join(get_move_args)}), expected (board, time_limit)")

    # 4. Report
    if violations:
        print("\n❌ COMPLIANCE AUDIT FAILED:")
        for v in violations:
            print(f"   🚫 {v}")
        return False

    print("✅ [RULE A - PASS] Only approved imports used (no sys, os, subprocess, etc.)")
    print("✅ [RULE B - PASS] No forbidden names, calls, or tokens (no eval, exec, compile, open, network)")
    print(f"✅ [RULE C - PASS] Interface valid: def get_move(board, time_limit=1.0) -> chess.Move")
    print("="*60)
    print("🎉 COMPLIANCE RESULT: 100% PASS (ELIGIBLE FOR TOURNAMENT)")
    print("="*60)
    return True

if __name__ == "__main__":
    success = run_compliance("varad_bot.py")
    exit(0 if success else 1)
