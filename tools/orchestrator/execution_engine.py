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
MAX_RETRIES = 3


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n")


def run(
    command: list[str],
    cwd: Path,
) -> dict[str, Any]:
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return {
        "command": command,
        "cwd": str(cwd.relative_to(ROOT)),
        "returncode": result.returncode,
        "passed": result.returncode == 0,
        "output": result.stdout,
    }


def phase_by_id(
    registry: dict[str, Any],
    phase_id: int,
) -> dict[str, Any]:
    for phase in registry.get("phases", []):
        if phase["id"] == phase_id:
            return phase
    raise RuntimeError(f"Unknown phase: {phase_id}")


def load_spec(phase_id: int) -> dict[str, Any]:
    matches = sorted(SPECS.glob(f"phase_{phase_id}_*.json"))

    if len(matches) != 1:
        raise RuntimeError(
            f"Expected one spec for phase {phase_id}, "
            f"found {len(matches)}"
        )

    spec = load_json(matches[0])

    if spec.get("phase") != phase_id:
        raise RuntimeError(
            f"Specification phase mismatch: "
            f"expected {phase_id}, got {spec.get('phase')}"
        )

    return spec


def dependencies_complete(
    phase: dict[str, Any],
    state: dict[str, Any],
) -> bool:
    completed = set(state.get("completed_phases", []))
    return all(
        dependency in completed
        for dependency in phase.get("depends_on", [])
    )


def changed_paths() -> list[str]:
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


def validate_paths(
    spec: dict[str, Any],
) -> None:
    violations = [
        path
        for path in changed_paths()
        if not path_allowed(
            path,
            spec.get("allowed_paths", []),
        )
    ]

    if violations:
        raise RuntimeError(
            "Allowed-path violation:\n"
            + "\n".join(
                f"  FORBIDDEN: {path}"
                for path in violations
            )
        )


def run_phase_gate(
    gate: str,
) -> dict[str, Any]:
    flutter_app = ROOT / "flutter_app"

    commands: dict[str, tuple[list[str], Path]] = {
        "dart_format": (
            [
                "dart",
                "format",
                "--output=none",
                "--set-exit-if-changed",
                "lib",
                "test",
            ],
            flutter_app,
        ),
        "flutter_analyze": (
            ["flutter", "analyze"],
            flutter_app,
        ),
        "flutter_test": (
            ["flutter", "test"],
            flutter_app,
        ),
        "git_diff_check": (
            ["git", "diff", "--check"],
            ROOT,
        ),
    }

    if gate == "contract_validation":
        command = [
            "python3",
            "-c",
            (
                "from tools.orchestrator.gates.contract "
                "import contract_validation; "
                "r = contract_validation(); "
                "print(r); "
                "raise SystemExit(0 if r['passed'] else 1)"
            ),
        ]
        result = run(command, ROOT)
    elif gate in commands:
        command, cwd = commands[gate]
        result = run(command, cwd)
    else:
        return {
            "gate": gate,
            "passed": False,
            "returncode": 1,
            "error": f"Unsupported gate: {gate}",
            "output": "",
        }

    result["gate"] = gate
    return result


def run_gates(
    phase: dict[str, Any],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    for gate in phase.get("gates", []):
        result = run_phase_gate(gate)
        results.append(result)

        print(
            f"[{'PASS' if result['passed'] else 'FAIL'}] "
            f"{gate}"
        )

        if not result["passed"]:
            print(result.get("output", "").rstrip())
            break

    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Guarded autonomous execution engine v2"
    )
    parser.add_argument(
        "--phase",
        type=int,
        required=True,
    )
    parser.add_argument(
        "--state",
        type=Path,
        default=DEFAULT_STATE,
    )
    parser.add_argument(
        "--execute",
        action="store_true",
    )
    args = parser.parse_args()

    registry = load_json(REGISTRY)
    state = load_json(args.state)
    phase = phase_by_id(
        registry,
        args.phase,
    )
    spec = load_spec(args.phase)

    print("=" * 60)
    print("GUARDED AUTONOMOUS EXECUTION ENGINE v2")
    print("=" * 60)
    print(f"Project : {registry['project']}")
    print(f"Phase   : {phase['id']} — {phase['name']}")
    print(f"State   : {args.state}")
    print(f"Mode    : {'execute' if args.execute else 'verify'}")
    print()

    if spec.get("contract") != phase.get("contract"):
        raise RuntimeError(
            "Spec/registry contract mismatch"
        )

    if not dependencies_complete(phase, state):
        raise RuntimeError(
            f"Phase {args.phase} dependencies are incomplete"
        )

    print("[PASS] dependencies")
    print("[PASS] contract")
    print("[PASS] specification")

    validate_paths(spec)
    print("[PASS] allowed-path guard")

    if not changed_paths():
        print("[PASS] working tree clean")
    else:
        raise RuntimeError(
            "Working tree is not clean"
        )

    results = run_gates(phase)

    passed = (
        len(results) == len(phase.get("gates", []))
        and all(
            result["passed"]
            for result in results
        )
    )

    state.setdefault("attempts", {})
    state.setdefault("gates", {})
    state.setdefault("history", [])

    attempt = int(
        state["attempts"].get(
            str(args.phase),
            0,
        )
    )

    if passed:
        if args.execute:
            completed = set(
                state.get(
                    "completed_phases",
                    [],
                )
            )
            completed.add(args.phase)

            state["completed_phases"] = sorted(
                completed
            )
            state["current_phase"] = None
            state["status"] = "completed"

            state["gates"][str(args.phase)] = {
                result["gate"]: result["passed"]
                for result in results
            }

            state["history"].append({
                "phase": args.phase,
                "result": "COMPLETED",
                "mode": "guarded_execution_v2",
                "attempt": attempt + 1,
                "gates": [
                    {
                        "gate": result["gate"],
                        "passed": result["passed"],
                    }
                    for result in results
                ],
            })

            save_json(args.state, state)

        print()
        print("=" * 60)
        print("EXECUTION RESULT: PASSED")
        print("=" * 60)

        return 0

    attempt += 1

    state["attempts"][str(args.phase)] = attempt
    state["status"] = (
        "retryable"
        if attempt < MAX_RETRIES
        else "failed"
    )
    state["current_phase"] = args.phase

    state["gates"][str(args.phase)] = {
        result["gate"]: result["passed"]
        for result in results
    }

    state["history"].append({
        "phase": args.phase,
        "result": "FAILED",
        "mode": "guarded_execution_v2",
        "attempt": attempt,
        "gates": [
            {
                "gate": result["gate"],
                "passed": result["passed"],
            }
            for result in results
        ],
    })

    save_json(args.state, state)

    print()
    print("=" * 60)
    print(
        f"EXECUTION RESULT: FAILED "
        f"(attempt {attempt}/{MAX_RETRIES})"
    )
    print("=" * 60)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
