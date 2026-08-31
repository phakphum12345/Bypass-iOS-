#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


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


def validate_task(
    task: dict[str, Any],
) -> dict[str, Any]:
    required = [
        "id",
        "phase",
        "objective",
        "allowed_paths",
    ]

    missing = [
        key
        for key in required
        if key not in task
    ]

    if missing:
        return {
            "passed": False,
            "error": (
                "Missing task fields: "
                + ", ".join(missing)
            ),
        }

    if not isinstance(task["allowed_paths"], list):
        return {
            "passed": False,
            "error": "allowed_paths must be a list.",
        }

    planned_files = task.get(
        "planned_files",
        [],
    )

    if not isinstance(planned_files, list):
        return {
            "passed": False,
            "error": "planned_files must be a list.",
        }

    violations = [
        path
        for path in planned_files
        if not path_allowed(
            path,
            task["allowed_paths"],
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
        "task": task,
    }


def load_task(
    path: Path,
) -> dict[str, Any]:
    try:
        task = json.loads(
            path.read_text(
                encoding="utf-8",
            )
        )
    except Exception as exc:
        raise RuntimeError(
            f"Unable to load task: {exc}"
        ) from exc

    result = validate_task(task)

    if not result["passed"]:
        raise RuntimeError(result["error"])

    return result["task"]


def plan_task(
    task: dict[str, Any],
) -> dict[str, Any]:
    result = validate_task(task)

    if not result["passed"]:
        return result

    return {
        "passed": True,
        "task_id": task["id"],
        "phase": task["phase"],
        "objective": task["objective"],
        "allowed_paths": task["allowed_paths"],
        "planned_files": task.get(
            "planned_files",
            [],
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Guarded autonomous task provider"
    )

    parser.add_argument(
        "--task",
        type=Path,
        required=True,
    )

    args = parser.parse_args()

    result = plan_task(
        load_task(args.task)
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
