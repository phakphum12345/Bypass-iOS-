#!/usr/bin/env python3

import json
import subprocess
import sys
from pathlib import Path

from tools.orchestrator.lifecycle import is_terminal_state


ROOT = Path(__file__).resolve().parents[2]
ORCHESTRATOR_DIR = ROOT / "tools" / "orchestrator"

REGISTRY_FILE = ORCHESTRATOR_DIR / "phase_registry.json"
STATE_FILE = ORCHESTRATOR_DIR / "state.json"
POLICY_FILE = ORCHESTRATOR_DIR / "policies.json"


def load_json(path: Path):
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        raise RuntimeError(f"Unable to load {path}: {exc}") from exc


def run_command(*args):
    result = subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return result.returncode, result.stdout.strip()


def check_clean_tree():
    code, output = run_command("git", "status", "--porcelain")

    if code != 0:
        raise RuntimeError(f"git status failed:\n{output}")

    return output == "", output


def find_phase(registry, phase_id):
    for phase in registry["phases"]:
        if phase["id"] == phase_id:
            return phase
    return None


def validate_dependencies(phase, completed):
    missing = [
        dependency
        for dependency in phase.get("depends_on", [])
        if dependency not in completed
    ]
    return missing


def main():
    registry = load_json(REGISTRY_FILE)
    state = load_json(STATE_FILE)
    policies = load_json(POLICY_FILE)

    print("=" * 60)
    print("AUTONOMOUS PROJECT ORCHESTRATOR")
    print("=" * 60)

    print(f"Project : {registry['project']}")
    print(f"Mode    : {policies['mode']}")

    current_phase_id = state["current_phase"]
    completed = set(state.get("completed_phases", []))

    if is_terminal_state(registry, state):
        print("\n===== TERMINAL STATE =====")
        print("  All registered phases are completed.")
        print("  Current phase : none")
        print("  Project       : COMPLETE")
        print("\n" + "=" * 60)
        print("PROJECT COMPLETE — NO FURTHER PHASE")
        print("=" * 60)
        return 0

    phase = find_phase(registry, current_phase_id)

    if phase is None:
        print(f"\nERROR: Phase {current_phase_id} is not registered.")
        return 1

    print(f"\nCurrent phase : {current_phase_id}")
    print(f"Name          : {phase['name']}")
    print(f"Type          : {phase['type']}")

    print("\n===== COMPLETED PHASES =====")

    for phase_id in sorted(completed):
        print(f"  Phase {phase_id} ✓")

    print("\n===== CONTRACT =====")

    contract = ROOT / phase["contract"]

    if not contract.is_file():
        print(f"  ERROR: missing contract: {phase['contract']}")
        return 1

    print(f"  {phase['contract']} ✓")

    print("\n===== DEPENDENCIES =====")

    missing = validate_dependencies(phase, completed)

    if missing:
        print("  ERROR: missing dependencies:")
        for dependency in missing:
            print(f"    Phase {dependency}")
        return 1

    for dependency in phase.get("depends_on", []):
        print(f"  Phase {dependency} ✓")

    print("\n===== GIT =====")

    clean, status = check_clean_tree()

    if policies.get("require_clean_tree", True):
        if not clean:
            print("  ERROR: working tree is not clean.")
            print(status)
            return 1

        print("  Working tree clean ✓")

    code, branch = run_command("git", "branch", "--show-current")

    if code != 0:
        print("  ERROR: unable to determine current branch.")
        return 1

    print(f"  Branch: {branch}")

    print("\n===== MUTATION POLICY =====")

    print(
        f"  Source mutation : "
        f"{'ENABLED' if policies['allow_source_mutation'] else 'DISABLED'}"
    )
    print(
        f"  Commit          : "
        f"{'ENABLED' if policies['allow_git_commit'] else 'DISABLED'}"
    )
    print(
        f"  Push            : "
        f"{'ENABLED' if policies['allow_git_push'] else 'DISABLED'}"
    )
    print(
        f"  Pull Request    : "
        f"{'ENABLED' if policies['allow_pull_request'] else 'DISABLED'}"
    )
    print(
        f"  Merge           : "
        f"{'ENABLED' if policies['allow_merge'] else 'DISABLED'}"
    )

    print("\n===== ALLOWED PATHS =====")

    for path in phase.get("allowed_paths", []):
        print(f"  {path}")

    print("\n===== REQUIRED GATES =====")

    for gate in phase.get("gates", []):
        print(f"  - {gate}")

    print("\n===== PLAN =====")
    print(f"  NEXT PHASE : {phase['id']} — {phase['name']}")
    print(f"  CONTRACT   : {phase['contract']}")
    print(f"  RETRIES    : {phase.get('max_retries', 0)}")

    print("\n===== EXECUTION =====")

    if policies["mode"] != "plan_only":
        print("  ERROR: this v1 engine only supports plan_only mode.")
        return 1

    print("  Generation : SKIPPED")
    print("  Validation : SKIPPED")
    print("  Repair     : SKIPPED")
    print("  Commit     : SKIPPED")
    print("  Push       : SKIPPED")
    print("  PR         : SKIPPED")
    print("  Merge      : SKIPPED")

    print("\n" + "=" * 60)
    print("PLAN READY — NO REPOSITORY MUTATION")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
