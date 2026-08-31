from __future__ import annotations

from .registry import COMMAND_GATES, run_command


def run_gate(name: str, phase_id: int | None = None):
    if name not in COMMAND_GATES:
        return {
            "gate": name,
            "passed": False,
            "error": f"Unknown gate: {name}",
        }

    factory = COMMAND_GATES[name]

    if name == "contract_validation":
        spec = factory(phase_id or 6)
    else:
        spec = factory()

    validator = spec.get("validator")

    if validator is not None:
        result = validator()

        return {
            "gate": name,
            "cwd": str(
                spec["cwd"].relative_to(spec["cwd"].anchor)
            ),
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


def run_gates(
    gates: list[str],
    phase_id: int | None = None,
):
    results = []

    for gate in gates:
        result = run_gate(
            gate,
            phase_id=phase_id,
        )
        results.append(result)

        if not result["passed"]:
            break

    return results
