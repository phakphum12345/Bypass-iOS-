#!/usr/bin/env python3

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def git_changed_paths() -> list[str]:
    commands = [
        ["git", "diff", "--name-only"],
        ["git", "diff", "--cached", "--name-only"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ]

    changed: set[str] = set()

    for command in commands:
        result = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError(
                "Unable to inspect git working-tree changes:\n"
                + result.stdout
            )

        changed.update(
            line.strip()
            for line in result.stdout.splitlines()
            if line.strip()
        )

    return sorted(changed)


def path_allowed(path: str, allowed_paths: list[str]) -> bool:
    normalized = path.rstrip("/") + "/"

    for allowed in allowed_paths:
        prefix = allowed.rstrip("/") + "/"

        if normalized.startswith(prefix):
            return True

    return False


def validate_allowed_paths(
    allowed_paths: list[str],
) -> tuple[bool, list[str]]:
    changed = git_changed_paths()

    violations = [
        path
        for path in changed
        if not path_allowed(path, allowed_paths)
    ]

    return not violations, violations
