#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.path_guard import (
    git_changed_paths,
    path_allowed,
    validate_allowed_paths,
)


ALLOWED = [
    "flutter_app/lib/core/security/",
    "flutter_app/lib/core/pipeline/",
    "flutter_app/test/",
    "docs/architecture/",
]


def test_changed_paths_includes_untracked():
    test_file = ROOT / "tools/orchestrator/tests/__path_guard_untracked__.tmp"

    try:
        test_file.touch()

        changed = git_changed_paths()

        assert (
            "tools/orchestrator/tests/__path_guard_untracked__.tmp"
            in changed
        )
    finally:
        test_file.unlink(missing_ok=True)


def test_allowed_path():
    assert path_allowed(
        "flutter_app/lib/core/security/security_boundary.dart",
        ALLOWED,
    )


def test_forbidden_path():
    assert not path_allowed(
        "tools/orchestrator/path_guard.py",
        ALLOWED,
    )


def test_validate_current_paths():
    ok, violations = validate_allowed_paths(ALLOWED)

    assert ".gitignore" in violations
    assert "tools/orchestrator/path_guard.py" in violations
    assert not ok


def main():
    tests = [
        test_changed_paths_includes_untracked,
        test_allowed_path,
        test_forbidden_path,
        test_validate_current_paths,
    ]

    for test in tests:
        test()
        print(f"PASS: {test.__name__}")

    print("PATH GUARD UNIT TEST: PASS")


if __name__ == "__main__":
    main()
