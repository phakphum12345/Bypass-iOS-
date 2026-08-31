from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]

PHASE_CONTRACTS = {
    3: "docs/architecture/PHASE_3_CONTRACT.md",
    4: "docs/architecture/PHASE_4_CONTRACT.md",
    5: "docs/architecture/PHASE_5_CONTRACT.md",
    6: "docs/architecture/PHASE_6_CONTRACT.md",
    7: "docs/architecture/PHASE_7_CONTRACT.md",
    8: "docs/architecture/PHASE_8_CONTRACT.md",
    9: "docs/architecture/PHASE_9_RELEASE_CONTRACT.md",
}

PHASE6_REQUIRED_RULES = [
    "Client state cannot grant authorization.",
    "Denied authorization remains denied.",
    "Entitlement cannot exceed authorization.",
    "Evidence cannot grant authorization.",
    "UI state cannot override the security boundary.",
    "Execution eligibility depends on the authoritative decision.",
]


def validate_contract_for_phase(phase_id: int):
    contract_rel = PHASE_CONTRACTS.get(phase_id)

    if contract_rel is None:
        return {
            "passed": False,
            "output": f"No contract mapping for phase {phase_id}.",
        }

    contract = ROOT / contract_rel

    if not contract.is_file():
        return {
            "passed": False,
            "output": f"Missing contract: {contract_rel}",
        }

    text = contract.read_text()

    if not text.strip():
        return {
            "passed": False,
            "output": f"Empty contract: {contract_rel}",
        }

    # Phase 6 retains its explicit defensive security rules.
    if phase_id == 6:
        missing = [
            rule
            for rule in PHASE6_REQUIRED_RULES
            if rule not in text
        ]

        if missing:
            return {
                "passed": False,
                "output": (
                    "Missing Phase 6 rules:\n"
                    + "\n".join(
                        f"- {rule}" for rule in missing
                    )
                ),
            }

        if (
            "No platform-security bypass behavior is implemented."
            not in text
        ):
            return {
                "passed": False,
                "output": (
                    "Phase 6 defensive research boundary is missing."
                ),
            }

    return {
        "passed": True,
        "output": (
            f"Contract validation passed for phase {phase_id}: "
            f"{contract_rel}"
        ),
    }


def contract_validation(phase_id: int = 6):
    result = validate_contract_for_phase(phase_id)

    return {
        "command": [
            "contract-validation",
            str(phase_id),
        ],
        "cwd": ROOT,
        "validator": lambda: validate_contract_for_phase(phase_id),
        **result,
    }
