"""Read-only device diagnostic report primitives.

No platform adapter is configured in Phase 2. Consequently, the report is
conservative and does not claim that a device was detected or inspected.
"""
from __future__ import annotations

import re
from typing import Any

_DEVICE_REFERENCE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{7,63}$")


def build_diagnostic_report(device_reference: str) -> dict[str, Any]:
    """Return a fail-closed report without querying or modifying a device."""
    if not isinstance(device_reference, str) or not _DEVICE_REFERENCE.fullmatch(
        device_reference
    ):
        raise ValueError("device_reference_must_be_an_opaque_8_to_64_char_token")

    return {
        "schema_version": "1.0",
        "device_reference": device_reference,
        "overall_status": "UNKNOWN",
        "connection": {
            "status": "UNKNOWN",
            "source": "no_trusted_adapter",
            "observed_at": None,
        },
        "device": {
            "platform": {"status": "UNKNOWN", "value": None},
            "model": {"status": "UNKNOWN", "value": None},
            "os_version": {"status": "UNKNOWN", "value": None},
        },
        "security_states": {
            "passcode": "NOT_INSPECTED",
            "activation_lock": "NOT_INSPECTED",
            "mdm_enrollment": "NOT_INSPECTED",
            "device_trust": "NOT_INSPECTED",
        },
        "evidence": [],
        "operation_performed": False,
        "authorization_granted": False,
        "limitations": [
            "No trusted read-only device adapter is configured.",
            "This report does not establish device ownership or authorization.",
            "Security-sensitive states are deliberately not inspected.",
        ],
    }
