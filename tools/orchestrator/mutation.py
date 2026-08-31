#!/usr/bin/env python3

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable

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
            raise RuntimeError(result.stdout)

        changed.update(
            line.strip()
            for line in result.stdout.splitlines()
            if line.strip()
        )

    return sorted(changed)


def path_allowed(
    path: str,
    allowed_paths: list[str],
) -> bool:
    normalized = path.rstrip("/") + "/"

    return any(
        normalized.startswith(
            allowed.rstrip("/") + "/"
        )
        for allowed in allowed_paths
    )


def validate_mutation(
    allowed_paths: list[str],
) -> tuple[bool, list[str]]:
    changed = git_changed_paths()

    violations = [
        path
        for path in changed
        if not path_allowed(path, allowed_paths)
    ]

    return not violations, violations


def snapshot() -> set[str]:
    return set(git_changed_paths())


def mutation_delta(
    before: set[str],
    after: set[str],
) -> list[str]:
    return sorted(after - before)


def run_mutation(
    mutator: Callable[[], None],
    allowed_paths: list[str],
) -> dict:
    before = snapshot()

    mutator()

    after = snapshot()

    ok, violations = validate_mutation(
        allowed_paths
    )

    if not ok:
        raise RuntimeError(
            "Mutation violated allowed paths:\n"
            + "\n".join(
                f"- {path}"
                for path in violations
            )
        )

    return {
        "changed_paths": mutation_delta(before, after),
        "allowed": True,
    }
