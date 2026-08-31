#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.orchestrator.mutation import (
    run_mutation,
    validate_mutation,
)


ROOT = Path(__file__).resolve().parents[2]


def path_allowed(
    path: str,
    allowed_paths: list[str],
) -> bool:
    normalized = path.rstrip("/") + "/"

    return any(
        normalized.startswith(
            prefix.rstrip("/") + "/"
        )
        for prefix in allowed_paths
    )


def validate_plan(
    plan: dict[str, Any],
) -> dict[str, Any]:
    allowed_paths = plan.get(
        "allowed_paths",
        [],
    )
    planned_files = plan.get(
        "planned_files",
        [],
    )
    changes = plan.get(
        "changes",
        {},
    )

    if not isinstance(allowed_paths, list):
        return {
            "passed": False,
            "error": "allowed_paths must be a list.",
        }

    if not isinstance(planned_files, list):
        return {
            "passed": False,
            "error": "planned_files must be a list.",
        }

    if not isinstance(changes, dict):
        return {
            "passed": False,
            "error": "changes must be an object.",
        }

    planned_set = set(planned_files)
    change_set = set(changes)

    missing_changes = sorted(
        planned_set - change_set
    )

    unexpected_changes = sorted(
        change_set - planned_set
    )

    if missing_changes:
        return {
            "passed": False,
            "error": (
                "Planned files missing content:\n"
                + "\n".join(
                    f"- {path}"
                    for path in missing_changes
                )
            ),
        }

    if unexpected_changes:
        return {
            "passed": False,
            "error": (
                "Changes contain unplanned files:\n"
                + "\n".join(
                    f"- {path}"
                    for path in unexpected_changes
                )
            ),
        }

    violations = [
        path
        for path in planned_files
        if not path_allowed(
            path,
            allowed_paths,
        )
    ]

    if violations:
        return {
            "passed": False,
            "error": (
                "Planned files violate allowed paths:\n"
                + "\n".join(
                    f"- {path}"
                    for path in violations
                )
            ),
        }

    return {
        "passed": True,
    }


def apply(
    plan: dict[str, Any],
) -> dict[str, Any]:
    validation = validate_plan(plan)

    if not validation["passed"]:
        return validation

    allowed_paths = plan["allowed_paths"]
    changes = plan["changes"]

    paths = [
        ROOT / relative
        for relative in changes
    ]

    def mutate() -> None:
        for relative, content in changes.items():
            path = ROOT / relative

            path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            path.write_text(
                content,
                encoding="utf-8",
            )

    try:
        result = run_mutation(
            mutate,
            allowed_paths,
        )
    except RuntimeError as exc:
        return {
            "passed": False,
            "error": str(exc),
        }

    return {
        "passed": True,
        "changed_paths": result["changed_paths"],
        "allowed": result["allowed"],
    }


def dry_run(
    plan: dict[str, Any],
) -> dict[str, Any]:
    validation = validate_plan(plan)

    if not validation["passed"]:
        return validation

    return {
        "passed": True,
        "dry_run": True,
        "planned_files": plan["planned_files"],
        "changed_paths": [],
    }


def main() -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Guarded explicit mutation provider"
    )

    parser.add_argument(
        "--plan",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--execute",
        action="store_true",
    )

    args = parser.parse_args()

    plan = json.loads(
        args.plan.read_text(
            encoding="utf-8",
        )
    )

    result = (
        apply(plan)
        if args.execute
        else dry_run(plan)
    )

    print(
        json.dumps(
            result,
            indent=2,
        )
    )

    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
