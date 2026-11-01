"""Allowlisted, read-only workstation diagnostics.

The collector intentionally excludes hostnames, usernames, serial numbers,
hardware UUIDs, MAC/IP addresses, filesystem paths, environment variables,
installed software inventories, and attached-device security state.
"""
from __future__ import annotations

import platform
import sys
from typing import Any

SCHEMA_VERSION = "1.0"
AGENT_VERSION = "0.1.0"
ALLOWED_OS = {"Windows", "Linux", "Darwin"}


def collect_host_diagnostics() -> dict[str, Any]:
    """Return a minimal host report; never probes attached mobile devices."""
    system = platform.system()
    supported = system in ALLOWED_OS
    return {
        "schema_version": SCHEMA_VERSION,
        "agent": {
            "name": "authorized-device-management-host-agent",
            "version": AGENT_VERSION,
            "status": "AVAILABLE",
        },
        "host": {
            "os_family": system if supported else "OTHER",
            "os_release": platform.release() if supported else None,
            "architecture": platform.machine() if supported else "UNKNOWN",
            "runtime": {
                "name": "CPython",
                "version": platform.python_version(),
            },
        },
        "capabilities": {
            "host_diagnostics": "AVAILABLE",
            "attached_device_inspection": "NOT_CONFIGURED",
            "remote_command_execution": "NOT_SUPPORTED",
            "security_control_changes": "NOT_SUPPORTED",
        },
        "evidence": {
            "source": "local_runtime",
            "collection_mode": "read_only_allowlist",
        },
        "operation_performed": False,
        "authorization_granted": False,
        "limitations": [
            "Reports workstation runtime facts only.",
            "Does not inspect attached phones or tablets.",
            "Does not inspect or change Activation Lock, passcodes, or MDM.",
            "Does not establish device ownership or authorize an action.",
        ],
    }
