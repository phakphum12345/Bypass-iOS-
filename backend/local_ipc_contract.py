"""Transport-neutral, fail-closed message contract for future local IPC.

This validates message shape only. It does not authenticate peers, establish
enrollment, open sockets/pipes, or authorize operations.
"""
from __future__ import annotations

import json
import re
from typing import Any

SCHEMA_VERSION = "1.0"
MAX_MESSAGE_BYTES = 16 * 1024
_ALLOWED_METHODS = {"host.health.read", "host.diagnostics.read"}
_REQUEST_ID = re.compile(r"^[A-Za-z0-9_-]{16,80}$")
_FORBIDDEN_KEYS = {
    "identity", "role", "ownership", "consent", "entitlement",
    "authorization", "device_id", "udid", "serial", "command", "shell",
}


class IPCContractError(ValueError):
    """Raised when an IPC envelope violates the narrow read-only contract."""


def validate_request_bytes(raw: bytes) -> dict[str, Any]:
    """Decode and validate one bounded JSON request envelope."""
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_MESSAGE_BYTES:
        raise IPCContractError("invalid_message_size")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise IPCContractError("invalid_json") from None
    return validate_request(payload)


def validate_request(payload: Any) -> dict[str, Any]:
    """Accept only a minimal request; all authority remains server-side."""
    if not isinstance(payload, dict):
        raise IPCContractError("request_must_be_object")
    if set(payload) != {"schema_version", "request_id", "method", "params"}:
        raise IPCContractError("request_fields_must_match_contract")
    if payload["schema_version"] != SCHEMA_VERSION:
        raise IPCContractError("unsupported_schema_version")
    request_id = payload["request_id"]
    if not isinstance(request_id, str) or not _REQUEST_ID.fullmatch(request_id):
        raise IPCContractError("invalid_request_id")
    method = payload["method"]
    if not isinstance(method, str) or method not in _ALLOWED_METHODS:
        raise IPCContractError("method_not_allowed")
    params = payload["params"]
    if not isinstance(params, dict) or params:
        raise IPCContractError("params_must_be_empty_object")
    if _contains_forbidden_key(payload):
        raise IPCContractError("authority_or_device_fields_forbidden")
    return {
        "schema_version": SCHEMA_VERSION,
        "request_id": request_id,
        "method": method,
        "params": {},
    }


def _contains_forbidden_key(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            (isinstance(key, str) and key.lower() in _FORBIDDEN_KEYS)
            or _contains_forbidden_key(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_forbidden_key(item) for item in value)
    return False
