#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from tools.orchestrator.git_provider import LocalGitProvider
from tools.orchestrator.pipeline_state import transition


ROOT = Path(__file__).resolve().parents[2]
ORCH = ROOT / "tools" / "orchestrator"
REGISTRY = ORCH / "phase_registry.json"
POLICY = ORCH / "execution_policy.json"
DEFAULT_STATE = Path("/tmp/bypass-ios-autonomous-pipeline.json")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )


def save_json(
    path: Path,
    state: dict[str, Any],
) -> None:
    path.write_text(
        json.dumps(
            state,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def run(
    command: list[str],
) -> dict[str, Any]:
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
    for phase in registry.get("phases", []):
        if phase.get("id") == phase_id:
            return phase

    raise RuntimeError(
        f"Unknown registered phase: {phase_id}"
    )


def dependencies_complete(
    phase: dict[str, Any],
    completed: set[int],
) -> bool:
    return all(
        dependency in completed
        for dependency in phase.get(
            "depends_on",
            [],
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Guarded autonomous phase pipeline"
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
    policy = load_json(POLICY)
    state = load_json(args.state)

    phase = phase_by_id(
        registry,
        args.phase,
    )

    completed = set(
        state.get(
            "completed_phases",
            [],
        )
    )

    if not dependencies_complete(
        phase,
        completed,
    ):
        raise RuntimeError(
            f"Dependencies incomplete for phase {args.phase}"
        )

    print("=" * 60)
    print("AUTONOMOUS PHASE PIPELINE")
    print("=" * 60)
    print(
        f"Project : {registry.get('project', 'unknown')}"
    )
    print(
        f"Phase   : {phase['id']} — {phase['name']}"
    )
    print(
        f"Mode    : {'execute' if args.execute else 'preview'}"
    )

    # ----------------------------------------------------------
    # QUEUED -> PLANNED
    # ----------------------------------------------------------

    state["current_phase"] = args.phase

    transition(
        state,
        "queued",
    )
    transition(
        state,
        "planned",
    )

    state["status"] = "planned"
    save_json(
        args.state,
        state,
    )

    print("[PASS] queued")
    print("[PASS] planned")

    if not args.execute:
        print("[LOCK] mutation disabled")
        print("[LOCK] commit disabled")
        print("[LOCK] push disabled")
        print("[LOCK] PR disabled")
        print("[LOCK] merge disabled")
        return 0

    # ----------------------------------------------------------
    # EXECUTION ENGINE
    # ----------------------------------------------------------

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
        state["current_phase"] = args.phase
        state.setdefault(
            "failures",
            [],
        ).append({
            "stage": "validation",
            "error": result["output"],
        })
        save_json(
            args.state,
            state,
        )
        return 1

    # ----------------------------------------------------------
    # FINAL VALIDATION
    # ----------------------------------------------------------

    transition(
        state,
        "final_validated",
    )

    state["status"] = "final_validated"
    state["current_phase"] = args.phase

    state.setdefault(
        "validation",
        {},
    )["passed"] = True

    save_json(
        args.state,
        state,
    )

    print("[PASS] final validation")

    # ----------------------------------------------------------
    # COMMIT
    # ----------------------------------------------------------

    git = LocalGitProvider()

    allow_commit = bool(
        policy.get(
            "allow_git_commit",
            False,
        )
    )

    if not allow_commit:
        print("[LOCK] commit disabled")
        print("[LOCK] push disabled")
        print("[LOCK] PR disabled")
        print("[LOCK] merge disabled")

        # Important: phase is NOT completed here.
        # It remains final_validated until commit is enabled.
        return 0

    commit_message = (
        f"feat: autonomous phase {args.phase} execution"
    )

    commit_result = git.commit(
        message=commit_message,
        allowed_paths=phase.get(
            "allowed_paths",
            [],
        ),
        validation_passed=True,
        execute=True,
    )

    if not commit_result.passed:
        state["status"] = "failed"
        state["current_phase"] = args.phase
        state.setdefault(
            "failures",
            [],
        ).append({
            "stage": "committed",
            "error": (
                commit_result.error
                or commit_result.output
            ),
        })
        save_json(
            args.state,
            state,
        )
        return 1

    transition(
        state,
        "committed",
    )

    state["status"] = "committed"
    state["commit"] = {
        "message": commit_message,
        "metadata": commit_result.metadata,
    }

    save_json(
        args.state,
        state,
    )

    print("[PASS] commit")

    # ----------------------------------------------------------
    # PUSH
    # ----------------------------------------------------------

    if not policy.get(
        "allow_git_push",
        False,
    ):
        print("[LOCK] push disabled")
        print("[LOCK] PR disabled")
        print("[LOCK] merge disabled")
        return 0

    branch_result = run([
        "git",
        "branch",
        "--show-current",
    ])

    if not branch_result["passed"]:
        state["status"] = "failed"
        state["current_phase"] = args.phase
        state.setdefault(
            "failures",
            [],
        ).append({
            "stage": "pushed",
            "error": branch_result["output"],
        })
        save_json(
            args.state,
            state,
        )
        return 1

    branch = branch_result["output"].strip()

    push_result = git.push(
        branch,
        execute=True,
    )

    if not push_result.passed:
        state["status"] = "failed"
        state["current_phase"] = args.phase
        state.setdefault(
            "failures",
            [],
        ).append({
            "stage": "pushed",
            "error": (
                push_result.error
                or push_result.output
            ),
        })
        save_json(
            args.state,
            state,
        )
        return 1

    transition(
        state,
        "pushed",
    )

    state["status"] = "pushed"
    save_json(
        args.state,
        state,
    )

    print("[PASS] push")

    # ----------------------------------------------------------
    # PR
    # ----------------------------------------------------------

    if not policy.get(
        "allow_pull_request",
        False,
    ):
        print("[LOCK] PR disabled")
        print("[LOCK] merge disabled")
        return 0

    pr_result = git.open_pr(
        branch=branch,
        base=policy.get(
            "default_base",
            "main",
        ),
        title=f"feat: autonomous phase {args.phase}",
        body=(
            "Autonomous pipeline execution "
            f"for phase {args.phase}."
        ),
        execute=True,
    )

    if not pr_result.passed:
        state["status"] = "failed"
        state["current_phase"] = args.phase
        state.setdefault(
            "failures",
            [],
        ).append({
            "stage": "pr_open",
            "error": (
                pr_result.error
                or pr_result.output
            ),
        })
        save_json(
            args.state,
            state,
        )
        return 1

    transition(
        state,
        "pr_open",
    )

    state["status"] = "pr_open"
    save_json(
        args.state,
        state,
    )

    print("[PASS] PR")

    # ----------------------------------------------------------
    # CI
    # ----------------------------------------------------------

    ci_result = git.ci_status(
        branch=branch,
        execute=True,
    )

    if not ci_result.passed:
        state["status"] = "failed"
        state["current_phase"] = args.phase
        state.setdefault(
            "failures",
            [],
        ).append({
            "stage": "ci_running",
            "error": (
                ci_result.error
                or ci_result.output
            ),
        })
        save_json(
            args.state,
            state,
        )
        return 1

    transition(
        state,
        "ci_running",
    )
    transition(
        state,
        "ci_passed",
    )

    state["status"] = "ci_passed"

    # ----------------------------------------------------------
    # COMPLETED
    # ----------------------------------------------------------

    transition(
        state,
        "completed",
    )

    state["status"] = "completed"
    state["current_phase"] = None

    completed.add(
        args.phase
    )
    state["completed_phases"] = sorted(
        completed
    )

    save_json(
        args.state,
        state,
    )

    print("[PASS] CI")
    print()
    print("=" * 60)
    print("AUTONOMOUS PHASE PIPELINE: COMPLETED")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
