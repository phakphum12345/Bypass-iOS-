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
SPECS = ORCH / "specs"
DEFAULT_STATE = Path("/tmp/bypass-ios-execution-state.json")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n")


def run(cmd: list[str], cwd: Path) -> dict[str, Any]:
    result = subprocess.run(
        cmd,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return {
        "command": cmd,
        "returncode": result.returncode,
        "passed": result.returncode == 0,
        "output": result.stdout,
    }


def phase_by_id(registry: dict[str, Any], phase_id: int) -> dict[str, Any]:
    for phase in registry["phases"]:
        if phase["id"] == phase_id:
            return phase
    raise RuntimeError(f"Unknown phase: {phase_id}")


def load_spec(phase_id: int) -> dict[str, Any]:
    matches = sorted(SPECS.glob(f"phase_{phase_id}_*.json"))
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected one spec for phase {phase_id}, found {len(matches)}"
        )
    spec = load_json(matches[0])
    if spec.get("phase") != phase_id:
        raise RuntimeError("Specification phase mismatch")
    return spec


def dependencies_complete(
    phase: dict[str, Any],
    state: dict[str, Any],
) -> bool:
    completed = set(state.get("completed_phases", []))
    return all(
        dep in completed
        for dep in phase.get("depends_on", [])
    )


def run_gates(phase_id: int) -> list[dict[str, Any]]:
    result = run(
        [
            "python3",
            "-m",
            "tools.orchestrator.gates.runner",
        ],
        ROOT,
    )
    return [{
        "gate": "phase_gates",
        "phase": phase_id,
        **result,
    }]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Guarded autonomous execution engine"
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
    state = load_json(args.state)
    phase = phase_by_id(registry, args.phase)
    spec = load_spec(args.phase)

    print("=" * 60)
    print("GUARDED AUTONOMOUS EXECUTION ENGINE")
    print("=" * 60)
    print(f"Project : {registry['project']}")
    print(f"Phase   : {phase['id']} — {phase['name']}")
    print(f"State   : {args.state}")
    print(f"Mode    : {'execute' if args.execute else 'verify'}")
    print()

    if not dependencies_complete(phase, state):
        raise RuntimeError(
            f"Phase {args.phase} dependencies are incomplete."
        )

    if spec.get("contract") != phase.get("contract"):
        raise RuntimeError("Spec/registry contract mismatch")

    print("[PASS] dependencies")
    print("[PASS] contract")
    print("[PASS] specification")

    gates = run_gates(args.phase)

    for gate in gates:
        print(
            f"[{'PASS' if gate['passed'] else 'FAIL'}] "
            f"{gate['gate']}"
        )

    passed = all(g["passed"] for g in gates)

    if not passed:
        state["status"] = "failed"
        save_json(args.state, state)
        return 1

    if args.execute:
        state.setdefault("completed_phases", [])
        if args.phase not in state["completed_phases"]:
            state["completed_phases"].append(args.phase)

        state["completed_phases"] = sorted(
            state["completed_phases"]
        )
        state["current_phase"] = None
        state["status"] = "completed"

        state.setdefault("gates", {})
        state["gates"][str(args.phase)] = {
            "phase_gates": True,
        }

        state.setdefault("history", []).append({
            "phase": args.phase,
            "result": "COMPLETED",
            "mode": "guarded_execution",
        })

        save_json(args.state, state)

    print()
    print("=" * 60)
    print("EXECUTION RESULT: PASSED")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
