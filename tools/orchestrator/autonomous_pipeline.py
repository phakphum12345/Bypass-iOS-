#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ORCH = ROOT / "tools" / "orchestrator"
REGISTRY = ORCH / "phase_registry.json"
POLICY = ORCH / "execution_policy.json"
DEFAULT_STATE = Path("/tmp/bypass-ios-autonomous-pipeline.json")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n")


def run(command: list[str]) -> dict[str, Any]:
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return {
        "command": command,
        "returncode": result.returncode,
        "passed": result.returncode == 0,
        "output": result.stdout,
    }


def phase_by_id(
    registry: dict[str, Any],
    phase_id: int,
) -> dict[str, Any]:
    for phase in registry["phases"]:
        if phase["id"] == phase_id:
            return phase
    raise RuntimeError(f"Unknown registered phase: {phase_id}")


def dependencies_complete(
    phase: dict[str, Any],
    completed: set[int],
) -> bool:
    return all(
        dependency in completed
        for dependency in phase.get("depends_on", [])
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Guarded autonomous phase pipeline"
    )
    parser.add_argument("--phase", type=int, required=True)
    parser.add_argument(
        "--state",
        type=Path,
        default=DEFAULT_STATE,
    )
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    registry = load_json(REGISTRY)
    policy = load_json(POLICY)
    state = load_json(args.state)

    phase = phase_by_id(
        registry,
        args.phase,
    )

    if not dependencies_complete(
        phase,
        set(state.get("completed_phases", [])),
    ):
        raise RuntimeError(
            f"Dependencies incomplete for phase {args.phase}"
        )

    print("=" * 60)
    print("AUTONOMOUS PHASE PIPELINE")
    print("=" * 60)
    print(f"Project : {registry['project']}")
    print(f"Phase   : {phase['id']} — {phase['name']}")
    print(
        f"Mode    : {'execute' if args.execute else 'preview'}"
    )

    if not args.execute:
        print()
        print("[PASS] dependency plan")
        print("[LOCK] mutation disabled")
        print("[LOCK] commit disabled")
        print("[LOCK] push disabled")
        print("[LOCK] PR disabled")
        print("[LOCK] merge disabled")
        return 0

    executor = [
        "python3",
        "-m",
        "tools.orchestrator.execution_engine",
        "--phase",
        str(args.phase),
        "--state",
        str(args.state),
        "--execute",
    ]

    result = run(executor)

    print()
    print(result["output"])

    if not result["passed"]:
        state["status"] = "failed"
        save_json(args.state, state)
        return 1

    state["status"] = "validated"
    state["current_phase"] = None
    save_json(args.state, state)

    print("=" * 60)
    print("AUTONOMOUS PHASE PIPELINE: PASSED")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
