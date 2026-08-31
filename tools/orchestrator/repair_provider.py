#!/usr/bin/env python3

from __future__ import annotations

from typing import Any

from tools.orchestrator.mutation_provider import apply as apply_mutation
from tools.orchestrator.mutation_provider import validate_plan


def validate_repair(
    repair_plan: dict[str, Any],
) -> dict[str, Any]:
    required = [
        "phase",
        "allowed_paths",
        "planned_files",
        "changes",
    ]

    missing = [
        key
        for key in required
        if key not in repair_plan
    ]

    if missing:
        return {
            "passed": False,
            "error": (
                "Repair plan missing fields: "
                + ", ".join(missing)
            ),
        }

    result = validate_plan(repair_plan)

    if not result["passed"]:
        return result

    return {
        "passed": True,
    }


def repair(
    repair_plan: dict[str, Any],
    failures: list[dict[str, Any]],
    attempt: int,
    max_attempts: int = 3,
) -> dict[str, Any]:
    if attempt < 1:
        return {
            "passed": False,
            "error": "Repair attempt must be >= 1.",
        }

    if attempt > max_attempts:
        return {
            "passed": False,
            "error": (
                f"Repair attempt {attempt} exceeds "
                f"maximum {max_attempts}."
            ),
        }

    validation = validate_repair(repair_plan)

    if not validation["passed"]:
        return validation

    result = apply_mutation(repair_plan)

    if not result["passed"]:
        return {
            "passed": False,
            "error": result.get(
                "error",
                "Repair mutation failed.",
            ),
        }

    return {
        "passed": True,
        "attempt": attempt,
        "max_attempts": max_attempts,
        "failures_received": len(failures),
        "changed_paths": result.get(
            "changed_paths",
            [],
        ),
    }
