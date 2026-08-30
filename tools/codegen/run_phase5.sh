#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

echo
echo "============================================================"
echo " PHASE 5 — AUTOMATED CODE GENERATION / VALIDATION"
echo "============================================================"

echo
echo "===== BRANCH ====="
git branch --show-current

echo
echo "===== VALIDATOR ====="
python3 tools/codegen/validators/validate_generated.py

echo
echo "===== GENERATOR ====="
python3 tools/codegen/generate.py

echo
echo "===== FORMAT CHECK ====="
dart format --output=none --set-exit-if-changed flutter_app/lib flutter_app/test

echo
echo "===== GIT DIFF CHECK ====="
git diff --check

echo
echo "============================================================"
echo " PHASE 5 COMPLETE — ALL CHECKS PASSED"
echo "============================================================"
