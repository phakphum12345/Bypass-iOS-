from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[3]


REQUIRED_RULES = [
    "Client state cannot grant authorization.",
    "Denied authorization remains denied.",
    "Entitlement cannot exceed authorization.",
    "Evidence cannot grant authorization.",
    "UI state cannot override the security boundary.",
    "Execution eligibility depends on the authoritative decision.",
]


def validate_phase6_contract():
    contract = ROOT / "docs/architecture/PHASE_6_CONTRACT.md"

    if not contract.is_file():
        return {
            "passed": False,
            "output": f"Missing contract: {contract}",
        }

    text = contract.read_text()

    missing = [
        rule for rule in REQUIRED_RULES
        if rule not in text
    ]

    if missing:
        return {
            "passed": False,
            "output": "Missing Phase 6 rules:\n"
            + "\n".join(f"- {rule}" for rule in missing),
        }

    if "No platform-security bypass behavior is implemented." not in text:
        return {
            "passed": False,
            "output": (
                "Phase 6 defensive research boundary is missing."
            ),
        }

    return {
        "passed": True,
        "output": "Phase 6 contract validation passed.",
    }


def contract_validation():
    result = validate_phase6_contract()

    return {
        "command": ["phase6-contract-validation"],
        "cwd": ROOT,
        "validator": validate_phase6_contract,
        **result,
    }
