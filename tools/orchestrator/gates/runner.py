from __future__ import annotations

from .registry import COMMAND_GATES, run_command


def run_gate(name: str):
    if name not in COMMAND_GATES:
        return {
            "gate": name,
            "passed": False,
            "error": f"Unknown gate: {name}",
        }

    spec = COMMAND_GATES[name]()

    validator = spec.get("validator")

    if validator is not None:
        result = validator()

        return {
            "gate": name,
            "cwd": str(spec["cwd"].relative_to(spec["cwd"].anchor)),
            **result,
        }

    result = run_command(
        spec["command"],
        spec["cwd"],
    )

    return {
        "gate": name,
        **result,
    }


def run_gates(gates: list[str]):
    results = []

    for gate in gates:
        result = run_gate(gate)
        results.append(result)

        if not result["passed"]:
            break

    return results
