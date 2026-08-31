#!/usr/bin/env python3

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from tools.orchestrator.providers import ProviderResult


ROOT = Path(__file__).resolve().parents[2]


def run(
    command: list[str],
) -> ProviderResult:
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    return ProviderResult(
        passed=result.returncode == 0,
        output=result.stdout,
        metadata={
            "command": command,
            "returncode": result.returncode,
        },
    )


def clean_check() -> ProviderResult:
    result = run([
        "git",
        "status",
        "--porcelain",
    ])

    if not result.passed:
        return result

    clean = not result.output.strip()

    return ProviderResult(
        passed=clean,
        output=result.output,
        metadata={
            "clean": clean,
        },
    )


def validate_allowed_paths(
    allowed_paths: list[str],
) -> ProviderResult:
    status = run([
        "git",
        "status",
        "--porcelain",
    ])

    if not status.passed:
        return status

    violations: list[str] = []

    for line in status.output.splitlines():
        if len(line) < 4:
            continue

        path = line[3:].strip()

        if not any(
            path.rstrip("/").startswith(
                allowed.rstrip("/")
            )
            for allowed in allowed_paths
        ):
            violations.append(path)

    return ProviderResult(
        passed=not violations,
        output=(
            "Allowed paths validated."
            if not violations
            else "Forbidden paths:\n"
            + "\n".join(
                f"- {path}"
                for path in violations
            )
        ),
        metadata={
            "violations": violations,
        },
    )


def commit(
    message: str,
    allowed_paths: list[str],
    validation_passed: bool,
    execute: bool = False,
) -> ProviderResult:
    if not validation_passed:
        return ProviderResult(
            passed=False,
            error="Commit blocked: final validation failed.",
        )

    scope = validate_allowed_paths(
        allowed_paths
    )

    if not scope.passed:
        return ProviderResult(
            passed=False,
            error=scope.output,
            metadata=scope.metadata,
        )

    status = run([
        "git",
        "status",
        "--porcelain",
    ])

    if not status.passed:
        return status

    if not status.output.strip():
        return ProviderResult(
            passed=False,
            error="Commit blocked: working tree is clean.",
        )

    add = run([
        "git",
        "add",
        "--",
        *[
            line[3:].strip()
            for line in status.output.splitlines()
            if len(line) >= 4
        ],
    ])

    if not add.passed:
        return add

    diff_check = run([
        "git",
        "diff",
        "--cached",
        "--check",
    ])

    if not diff_check.passed:
        return diff_check

    if not execute:
        return ProviderResult(
            passed=True,
            output="Commit dry-run passed.",
            metadata={
                "dry_run": True,
                "message": message,
            },
        )

    return run([
        "git",
        "commit",
        "-m",
        message,
    ])


def push(
    branch: str,
    execute: bool = False,
) -> ProviderResult:
    command = [
        "git",
        "push",
        "-u",
        "origin",
        branch,
    ]

    if not execute:
        return ProviderResult(
            passed=True,
            output="Push dry-run passed.",
            metadata={
                "dry_run": True,
                "command": command,
            },
        )

    return run(command)


def open_pr(
    branch: str,
    base: str,
    title: str,
    body: str,
    execute: bool = False,
) -> ProviderResult:
    command = [
        "gh",
        "pr",
        "create",
        "--head",
        branch,
        "--base",
        base,
        "--title",
        title,
        "--body",
        body,
    ]

    if not execute:
        return ProviderResult(
            passed=True,
            output="PR dry-run passed.",
            metadata={
                "dry_run": True,
                "command": command,
            },
        )

    return run(command)


def ci_status(
    branch: str,
    execute: bool = False,
) -> ProviderResult:
    command = [
        "gh",
        "pr",
        "checks",
        branch,
        "--watch",
    ]

    if not execute:
        return ProviderResult(
            passed=True,
            output="CI dry-run passed.",
            metadata={
                "dry_run": True,
                "command": command,
            },
        )

    return run(command)


class LocalGitProvider:
    def commit(
        self,
        message: str,
        allowed_paths: list[str],
        validation_passed: bool,
        execute: bool = False,
    ) -> ProviderResult:
        return commit(
            message,
            allowed_paths,
            validation_passed,
            execute,
        )

    def push(
        self,
        branch: str,
        execute: bool = False,
    ) -> ProviderResult:
        return push(
            branch,
            execute,
        )

    def open_pr(
        self,
        branch: str,
        base: str,
        title: str,
        body: str,
        execute: bool = False,
    ) -> ProviderResult:
        return open_pr(
            branch,
            base,
            title,
            body,
            execute,
        )

    def ci_status(
        self,
        branch: str,
        execute: bool = False,
    ) -> ProviderResult:
        return ci_status(
            branch,
            execute,
        )
