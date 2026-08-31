#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from tools.orchestrator.git_provider import LocalGitProvider
from tools.orchestrator.repair_provider import repair as repair_with_provider
from tools.orchestrator.mutation_provider import (
    apply as apply_mutation,
    dry_run as mutation_dry_run,
)
from tools.orchestrator.pipeline_state import transition
from tools.orchestrator.task_provider import (
    load_task,
    plan_task,
)


ROOT = Path(__file__).resolve().parents[2]
ORCH = ROOT / "tools" / "orchestrator"
REGISTRY = ORCH / "phase_registry.json"
POLICY = ORCH / "execution_policy.json"
DEFAULT_STATE = Path(
    "/tmp/bypass-ios-autonomous-pipeline.json"
)


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


def validate_plan_against_phase(
    plan: dict[str, Any],
    phase: dict[str, Any],
) -> dict[str, Any]:
    task_allowed = set(
        plan["allowed_paths"]
    )
    phase_allowed = set(
        phase.get(
            "allowed_paths",
            [],
        )
    )

    invalid_task_scope = sorted(
        task_allowed - phase_allowed
    )

    if invalid_task_scope:
        return {
            "passed": False,
            "error": (
                "Task allowed_paths exceed phase allowed_paths:\n"
                + "\n".join(
                    f"- {path}"
                    for path in invalid_task_scope
                )
            ),
        }

    return {
        "passed": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Guarded autonomous task pipeline"
    )

    parser.add_argument(
        "--phase",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--task",
        type=Path,
        required=False,
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

    parser.add_argument(
        "--commit-message",
        default=None,
    )
    parser.add_argument(
        "--test-repair-loop",
        action="store_true",
        help="Run deterministic local repair-loop validation.",
    )

    args = parser.parse_args()

    if not args.test_repair_loop and args.task is None:
        parser.error("--task is required unless --test-repair-loop is used")

    registry = load_json(REGISTRY)
    policy = load_json(POLICY)
    state = load_json(args.state)

    phase = phase_by_id(
        registry,
        args.phase,
    )

    if args.test_repair_loop:
        target = ROOT / "docs/architecture/.repair_loop_fixture.tmp"

        target.write_text(
            "FAIL\n",
            encoding="utf-8",
        )

        attempts = 0
        failures: list[dict[str, Any]] = []

        try:
            while attempts < 3:
                attempts += 1

                passed = (
                    target.read_text(
                        encoding="utf-8",
                    ).strip()
                    == "PASS"
                )

                if passed:
                    print(
                        f"[PASS] repair-loop gate on attempt {attempts}"
                    )
                    break

                failure = {
                    "gate": "deterministic_repair_fixture",
                    "passed": False,
                    "attempt": attempts,
                }
                failures.append(failure)

                print(
                    f"[FAIL] repair-loop gate "
                    f"attempt {attempts}/3"
                )

                repair_result = repair_with_provider(
                    repair_plan={
                        "phase": args.phase,
                        "allowed_paths": [
                            "docs/architecture/"
                        ],
                        "planned_files": [
                            "docs/architecture/.repair_loop_fixture.tmp"
                        ],
                        "changes": {
                            "docs/architecture/.repair_loop_fixture.tmp":
                                "PASS\n"
                        },
                    },
                    failures=[failure],
                    attempt=attempts,
                    max_attempts=3,
                )

                print(
                    "[REPAIR]",
                    repair_result,
                )

                if not repair_result["passed"]:
                    print("[FAIL] repair provider")
                    return 1

            final_pass = (
                target.read_text(
                    encoding="utf-8",
                ).strip()
                == "PASS"
            )

            print(
                "[PASS] repair-loop final ="
                if final_pass
                else "[FAIL] repair-loop final =",
                final_pass,
            )

            print("[PASS] attempts =", attempts)

            if not final_pass:
                return 1

            return 0

        finally:
            target.unlink(missing_ok=True)
    print("AUTONOMOUS TASK PIPELINE")
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
        error = (
            f"Dependencies incomplete for phase {args.phase}"
        )

        state["status"] = "failed"
        state["current_phase"] = args.phase
        state.setdefault(
            "failures",
            [],
        ).append({
            "stage": "planned",
            "error": error,
        })
        save_json(args.state, state)

        print(error)
        return 1

    # ----------------------------------------------------------
    # TASK / PLAN
    # ----------------------------------------------------------

    try:
        task = load_task(args.task)
        plan = plan_task(task)
    except Exception as exc:
        state["status"] = "failed"
        state["current_phase"] = args.phase
        state.setdefault(
            "failures",
            [],
        ).append({
            "stage": "planned",
            "error": str(exc),
        })
        save_json(args.state, state)
        print(f"[FAIL] task: {exc}")
        return 1

    if not plan["passed"]:
        state["status"] = "failed"
        state["current_phase"] = args.phase
        state.setdefault(
            "failures",
            [],
        ).append({
            "stage": "planned",
            "error": plan["error"],
        })
        save_json(args.state, state)
        print(
            "[FAIL] task plan:",
            plan["error"],
        )
        return 1

    phase_scope = validate_plan_against_phase(
        plan,
        phase,
    )

    if not phase_scope["passed"]:
        state["status"] = "failed"
        state["current_phase"] = args.phase
        state.setdefault(
            "failures",
            [],
        ).append({
            "stage": "planned",
            "error": phase_scope["error"],
        })
        save_json(args.state, state)
        print(
            "[FAIL] phase scope:",
            phase_scope["error"],
        )
        return 1

    state["current_phase"] = args.phase
    state["task_id"] = plan["task_id"]

    transition(
        state,
        "queued",
    )
    transition(
        state,
        "planned",
    )

    state["status"] = "planned"
    save_json(args.state, state)

    print("[PASS] task")
    print("[PASS] plan")
    print()

    # ----------------------------------------------------------
    # PREVIEW
    # ----------------------------------------------------------

    if not args.execute:
        mutation_preview = mutation_dry_run(
            task
        )

        if not mutation_preview["passed"]:
            print(
                "[FAIL] mutation plan:",
                mutation_preview["error"],
            )
            return 1

        print("[PASS] mutation dry-run")
        print("[LOCK] source mutation")
        print("[LOCK] commit")
        print("[LOCK] push")
        print("[LOCK] PR")
        print("[LOCK] merge")
        return 0

    # ----------------------------------------------------------
    # MUTATION
    # ----------------------------------------------------------

    if not policy.get(
        "allow_source_mutation",
        False,
    ):
        state["status"] = "planned"
        state["current_phase"] = args.phase
        save_json(args.state, state)

        print("[PASS] plan")
        print("[LOCK] source mutation disabled")
        return 0

    mutation_result = apply_mutation(
        task
    )

    if not mutation_result["passed"]:
        state["status"] = "failed"
        state["current_phase"] = args.phase
        state.setdefault(
            "failures",
            [],
        ).append({
            "stage": "mutated",
            "error": mutation_result["error"],
        })
        save_json(args.state, state)

        print(
            "[FAIL] mutation:",
            mutation_result["error"],
        )
        return 1

    transition(
        state,
        "generated",
    )
    transition(
        state,
        "mutated",
    )

    state["status"] = "mutated"
    state["mutation"] = {
        "changed_paths": mutation_result[
            "changed_paths"
        ],
    }

    save_json(args.state, state)

    print("[PASS] mutation")

    # ----------------------------------------------------------
    # VALIDATION / REPAIR LOOP
    # ----------------------------------------------------------

    max_attempts = int(
        policy.get(
            "max_repair_attempts",
            3,
        )
    )

    executor = [
        "python3",
        "-m",
        "tools.orchestrator.execution_engine",
        "--phase",
        str(args.phase),
        "--state",
        str(args.state),
        "--execute",
        "--allow-worktree-changes",
        "--validation-only",
    ]

    transition(
        state,
        "validating",
    )
    state["status"] = "validating"
    state["current_phase"] = args.phase
    save_json(
        args.state,
        state,
    )

    attempts = 0
    gate_results: list[dict[str, Any]] = []

    while True:
        validation = run(executor)

        print()
        print(validation["output"])

        # The execution engine returns success only when every
        # configured gate for the phase passes.
        if validation["passed"]:
            gate_results = [
                {
                    "gate": "execution_engine",
                    "passed": True,
                }
            ]
            break

        attempts += 1

        # Record the failed validation before attempting repair.
        state["status"] = "repairing"
        state["current_phase"] = args.phase
        state.setdefault(
            "attempts",
            {},
        )[str(args.phase)] = attempts

        failure = {
            "gate": "execution_engine",
            "passed": False,
            "output": validation["output"],
            "attempt": attempts,
        }

        state.setdefault(
            "failures",
            [],
        ).append(failure)

        save_json(
            args.state,
            state,
        )

        print(
            f"[FAIL] validation attempt {attempts}/{max_attempts}"
        )

        if attempts > max_attempts:
            state["status"] = "failed"
            save_json(
                args.state,
                state,
            )
            print(
                "[FAIL] maximum repair attempts exceeded"
            )
            return 1

        repair_plan = task.get(
            "repair",
            {},
        )

        if not repair_plan:
            state["status"] = "failed"
            state["current_phase"] = args.phase
            state.setdefault(
                "failures",
                [],
            ).append({
                "stage": "repairing",
                "error": (
                    "No explicit repair plan was supplied "
                    "for the failed validation."
                ),
            })
            save_json(
                args.state,
                state,
            )

            print(
                "[FAIL] no explicit repair plan"
            )
            return 1

        repair_result = repair_with_provider(
            repair_plan=repair_plan,
            failures=[failure],
            attempt=attempts,
            max_attempts=max_attempts,
        )

        state.setdefault(
            "repair",
            [],
        ).append({
            "attempt": attempts,
            **repair_result,
        })

        if not repair_result["passed"]:
            state["status"] = "failed"
            state["current_phase"] = args.phase
            state.setdefault(
                "failures",
                [],
            ).append({
                "stage": "repairing",
                "error": repair_result.get(
                    "error",
                    "Repair provider failed.",
                ),
            })

            save_json(
                args.state,
                state,
            )

            print(
                "[FAIL] repair:",
                repair_result.get(
                    "error",
                    "Repair provider failed.",
                ),
            )
            return 1

        print(
            f"[PASS] repair attempt {attempts}"
        )

        state["status"] = "validating"
        save_json(
            args.state,
            state,
        )

    state.setdefault(
        "gates",
        {},
    )[str(args.phase)] = gate_results

    # ----------------------------------------------------------
    # FINAL VALIDATION
    # ----------------------------------------------------------

    transition(
        state,
        "final_validated",
    )

    state["status"] = "final_validated"
    state["validation"] = {
        "passed": True,
    }
    state["current_phase"] = args.phase

    save_json(args.state, state)

    print("[PASS] final validation")

    # ----------------------------------------------------------
    # COMMIT
    # ----------------------------------------------------------

    git = LocalGitProvider()

    if not policy.get(
        "allow_git_commit",
        False,
    ):
        print("[LOCK] commit disabled")
        print("[LOCK] push disabled")
        print("[LOCK] PR disabled")
        print("[LOCK] merge disabled")
        return 0

    commit_result = git.commit(
        message=(
            args.commit_message
            or f"feat: autonomous phase {args.phase}"
        ),
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
        save_json(args.state, state)
        return 1

    transition(
        state,
        "committed",
    )

    state["status"] = "committed"
    state["commit"] = {
        "metadata": commit_result.metadata,
    }

    save_json(args.state, state)

    print("[PASS] commit")

    # ----------------------------------------------------------
    # REMOTE LIFECYCLE
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
        raise RuntimeError(
            branch_result["output"]
        )

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
        save_json(args.state, state)
        return 1

    transition(
        state,
        "pushed",
    )

    state["status"] = "pushed"
    save_json(args.state, state)

    print("[PASS] push")

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
        title=(
            f"feat: autonomous phase {args.phase}"
        ),
        body=(
            f"Autonomous execution for phase {args.phase}."
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
        save_json(args.state, state)
        return 1

    transition(
        state,
        "pr_open",
    )

    state["status"] = "pr_open"
    state["pr"] = {
        "output": pr_result.output,
    }
    save_json(args.state, state)

    print("[PASS] PR")

    ci_result = git.ci_status(
        branch,
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
        save_json(args.state, state)
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

    transition(
        state,
        "completed",
    )

    state["status"] = "completed"
    state["current_phase"] = None
    completed.add(args.phase)
    state["completed_phases"] = sorted(
        completed
    )

    save_json(args.state, state)

    print("[PASS] CI")
    print("=" * 60)
    print("AUTONOMOUS TASK PIPELINE: COMPLETED")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
