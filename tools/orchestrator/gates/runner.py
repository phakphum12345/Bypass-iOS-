from __future__ import annotations

from .registry import COMMAND_GATES, ROOT, run_command


def run_gate(
    name: str,
    phase_id: int | None = None,
):
    factory = COMMAND_GATES.get(name)

    if factory is None:
        return {
            "gate": name,
            "passed": False,
            "error": f"Unknown gate: {name}",
        }

    if name == "contract_validation":
        spec = factory(phase_id or 6)
    else:
        spec = factory()

    validator = spec.get("validator")

    if validator is not None:
        result = validator()

        return {
            "gate": name,
            "cwd": str(spec["cwd"].relative_to(ROOT)),
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
