#!/usr/bin/env python3

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.executor import load_json
from tools.orchestrator.gates.runner import run_gates


ORCHESTRATOR_DIR = ROOT / "tools" / "orchestrator"
REGISTRY_FILE = ORCHESTRATOR_DIR / "phase_registry.json"
STATE_FILE = ORCHESTRATOR_DIR / "state.json"
POLICY_FILE = ORCHESTRATOR_DIR / "policies.json"


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(data, indent=2) + "\n"
    )


def dependencies_complete(
    phase: dict[str, Any],
    completed: set[int],
) -> bool:
    return all(
        dependency in completed
        for dependency in phase.get("depends_on", [])
    )


def record_history(
    state: dict[str, Any],
    phase_id: int,
    result: str,
    mode: str,
    gates: list[dict[str, Any]] | None = None,
) -> None:
    entry: dict[str, Any] = {
        "phase": phase_id,
        "result": result,
        "mode": mode,
    }

    if gates is not None:
        entry["gates"] = [
            {
                "gate": gate["gate"],
                "passed": gate["passed"],
            }
            for gate in gates
        ]

    state.setdefault("history", []).append(entry)


def validate_phase(
    phase: dict[str, Any],
) -> tuple[bool, list[dict[str, Any]]]:
    gates = phase.get("gates", [])

    if not gates:
        return True, []

    results = run_gates(gates)

    passed = (
        len(results) == len(gates)
        and all(result["passed"] for result in results)
    )

    return passed, results


def run_phase_plan(
    phase: dict[str, Any],
    state: dict[str, Any],
    policy: dict[str, Any],
) -> bool:
    phase_id = phase["id"]

    print()
    print("=" * 60)
    print(f"PHASE {phase_id} — {phase['name']}")
    print("=" * 60)

    contract = ROOT / phase["contract"]

    if contract.exists():
        print(
            f"[PASS] contract: {phase['contract']}"
        )
    else:
        print(
            f"[FAIL] contract: {phase['contract']}"
        )
        return False

    print("[PASS] dependencies")

    mode = policy["mode"]

    if mode == "plan_only":
        print()
        print("MODE: plan_only")
        print("Generation : SKIPPED")
        print("Mutation   : SKIPPED")
        print("Commit     : SKIPPED")
        print("Push       : SKIPPED")
        print("PR         : SKIPPED")
        print("Merge      : SKIPPED")

        record_history(
            state=state,
            phase_id=phase_id,
            result="PLANNED",
            mode=mode,
        )

        return True

    print()
    print(f"MODE: {mode}")

    print("Generation : NOT IMPLEMENTED")
    print("Mutation   : NOT IMPLEMENTED")
    print("Commit     : NOT IMPLEMENTED")
    print("Push       : NOT IMPLEMENTED")
    print("PR         : NOT IMPLEMENTED")
    print("Merge      : NOT IMPLEMENTED")

    print()
    print(
        "[STOP] Execution mode is not yet supported "
        "by the autonomous loop."
    )

    return False


def main() -> int:
    registry = load_json(REGISTRY_FILE)
    state = load_json(STATE_FILE)
    policy = load_json(POLICY_FILE)

    phases = sorted(
        registry["phases"],
        key=lambda phase: phase["id"],
    )

    completed = set(
        state.get("completed_phases", [])
    )

    print("=" * 60)
    print("AUTONOMOUS PHASE LOOP")
    print("=" * 60)
    print(f"Project : {registry['project']}")
    print(f"Mode    : {policy['mode']}")
    print(
        "Completed:",
        ", ".join(map(str, sorted(completed))) or "none",
    )

    for phase in phases:
        phase_id = phase["id"]

        if phase_id in completed:
            print(
                f"[SKIP] Phase {phase_id} — "
                "already completed"
            )
            continue

        if not dependencies_complete(
            phase,
            completed,
        ):
            print()
            print(
                f"[STOP] Phase {phase_id} — "
                "dependencies are not complete"
            )

            state["status"] = "blocked"
            state["current_phase"] = phase_id

            save_json(
                STATE_FILE,
                state,
            )

            return 1

        state["current_phase"] = phase_id
        state["status"] = "running"

        save_json(
            STATE_FILE,
            state,
        )

        if not run_phase_plan(
            phase,
            state,
            policy,
        ):
            state["status"] = "failed"

            save_json(
                STATE_FILE,
                state,
            )

            return 1

        if policy["mode"] == "plan_only":
            print()
            print(
                f"[PLAN] Phase {phase_id} "
                "validated for execution path."
            )

            # IMPORTANT:
            # A planned phase is NOT a completed phase.
            # Stop here so the loop can never advance past
            # an unexecuted phase.
            state["status"] = "planned"
            state["current_phase"] = phase_id

            save_json(
                STATE_FILE,
                state,
            )

            print()
            print("=" * 60)
            print("PLAN STOP — WAITING FOR REAL EXECUTION")
            print("=" * 60)
            print(
                f"Phase {phase_id} is planned but NOT completed."
            )
            print(
                "The next phase will not start until this "
                "phase passes real execution gates."
            )

            return 0

        # Real execution will only mark a phase complete
        # after generation/mutation and all required gates pass.
        #
        # This branch intentionally stops until the real
        # execution engine is implemented.
        state["status"] = "failed"

        save_json(
            STATE_FILE,
            state,
        )

        return 1

    state["status"] = "planned"
    state["current_phase"] = None

    save_json(
        STATE_FILE,
        state,
    )

    print()
    print("=" * 60)
    print("AUTONOMOUS PHASE LOOP PLAN COMPLETE")
    print("=" * 60)
    print(
        "Completed phases :",
        ", ".join(
            map(
                str,
                sorted(
                    state.get(
                        "completed_phases",
                        [],
                    )
                ),
            )
        ),
    )
    print(
        "Planned phases   :",
        ", ".join(
            map(
                str,
                [
                    entry["phase"]
                    for entry in state.get(
                        "history",
                        []
                    )
                    if entry.get("result") == "PLANNED"
                ],
            )
        ) or "none",
    )
    print("Mode             :", policy["mode"])
    print("Mutation         : DISABLED")
    print("Commit           : DISABLED")
    print("Push             : DISABLED")
    print("Merge            : DISABLED")
    print()
    print("RESULT: PLAN COMPLETE")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
