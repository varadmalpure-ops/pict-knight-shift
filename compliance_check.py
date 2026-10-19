"""
PICT KNIGHT SHIFT // OFFICIAL AST COMPLIANCE CHECKER
File: compliance_check.py
Validates any bot against all hackathon hard rules using hackathon.security.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from hackathon.security import audit_bot_source

def run_compliance(file_path: str = "varad_bot.py") -> bool:
    print("\n" + "="*60)
    print(f"🔍 RUNNING OFFICIAL COMPLIANCE AUDIT ON: {file_path}")
    print("="*60)

    passed, msg = audit_bot_source(file_path)
    if passed:
        print(f"✅ {msg}")
        print("🎉 COMPLIANCE RESULT: 100% PASS (ELIGIBLE FOR TOURNAMENT)")
        print("="*60)
        return True
    else:
        print(f"❌ COMPLIANCE REJECTED: {msg}")
        print("="*60)
        return False

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "varad_bot.py"
    success = run_compliance(target)
    sys.exit(0 if success else 1)
