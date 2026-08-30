#!/usr/bin/env python3

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.gates.runner import run_gates


ROOT = Path(__file__).resolve().parents[2]
ORCHESTRATOR_DIR = ROOT / "tools" / "orchestrator"

REGISTRY_FILE = ORCHESTRATOR_DIR / "phase_registry.json"
STATE_FILE = ORCHESTRATOR_DIR / "state.json"
POLICY_FILE = ORCHESTRATOR_DIR / "policies.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(data, indent=2) + "\n"
    )


def phase_by_id(registry: dict[str, Any], phase_id: int):
    for phase in registry["phases"]:
        if phase["id"] == phase_id:
            return phase

    raise RuntimeError(f"Unknown phase: {phase_id}")


def dependencies_complete(
    phase: dict[str, Any],
    state: dict[str, Any],
) -> bool:
    completed = set(state.get("completed_phases", []))
    return all(
        dependency in completed
        for dependency in phase.get("depends_on", [])
    )


def validate_contract(phase: dict[str, Any]) -> bool:
    contract = ROOT / phase["contract"]

    if not contract.is_file():
        return False

    return contract.read_text().strip() != ""


def clean_tree() -> bool:
    import subprocess

    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    return result.returncode == 0 and not result.stdout.strip()


def execute_phase(
    phase: dict[str, Any],
    state: dict[str, Any],
    policy: dict[str, Any],
    dry_run: bool = True,
):
    phase_id = phase["id"]

    print("=" * 60)
    print(f"PHASE {phase_id} — {phase['name']}")
    print("=" * 60)

    if not dependencies_complete(phase, state):
        raise RuntimeError(
            f"Phase {phase_id} dependencies are incomplete."
        )

    print("[PASS] dependencies")

    if not validate_contract(phase):
        raise RuntimeError(
            f"Missing or empty contract: {phase['contract']}"
        )

    print(f"[PASS] contract: {phase['contract']}")

    if policy.get("require_clean_tree", True) and not clean_tree():
        raise RuntimeError("Working tree is not clean.")

    print("[PASS] git working tree")

    if dry_run:
        print()
        print("EXECUTION MODE: DRY-RUN")
        print("Generation : SKIPPED")
        print("Mutation   : SKIPPED")
        print("Commit     : SKIPPED")
        print("Push       : SKIPPED")
        print("Merge      : SKIPPED")

        return {
            "phase": phase_id,
            "status": "planned",
            "dry_run": True,
            "gates": [],
        }

    results = run_gates(phase["gates"])

    passed = (
        len(results) == len(phase["gates"])
        and all(result["passed"] for result in results)
    )

    return {
        "phase": phase_id,
        "status": "passed" if passed else "failed",
        "dry_run": False,
        "gates": results,
    }


def main():
    registry = load_json(REGISTRY_FILE)
    state = load_json(STATE_FILE)
    policy = load_json(POLICY_FILE)

    phase = phase_by_id(
        registry,
        state["current_phase"],
    )

    print("=" * 60)
    print("AUTONOMOUS PHASE EXECUTOR")
    print("=" * 60)
    print(f"Project : {registry['project']}")
    print(f"Mode    : {policy['mode']}")
    print(f"Phase   : {phase['id']} — {phase['name']}")
    print()

    result = execute_phase(
        phase,
        state,
        policy,
        dry_run=True,
    )

    print()
    print("=" * 60)
    print(
        "EXECUTOR RESULT:",
        result["status"].upper(),
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
