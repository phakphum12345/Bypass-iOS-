"""Local, deny-only HTTP API spine for the defensive reference app."""
from __future__ import annotations

import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from backend.device_intelligence import build_diagnostic_report

MAX_BODY_BYTES = 64 * 1024
REQUIRED_FIELDS = ("correlation_id", "device_id", "service_id", "action")


def evaluate_decision(request: dict[str, Any]) -> dict[str, str]:
    """No trusted providers exist yet, so every request must be denied."""
    return {
        "correlation_id": request["correlation_id"],
        "decision": "DENY",
        "authorization": "DENY",
        "entitlement": "UNKNOWN",
        "reason": (
            "No trusted identity, policy, authorization, or entitlement "
            "provider is configured. No operation was executed."
        ),
    }


def _allowed_origins() -> set[str]:
    return {
        item.strip()
        for item in os.environ.get("DECISION_API_ALLOWED_ORIGINS", "").split(",")
        if item.strip()
    }


class DecisionHandler(BaseHTTPRequestHandler):
    server_version = "DefensiveDecisionAPI/0.1"

    def _send(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        origin = self.headers.get("Origin")
        if origin and origin in _allowed_origins():
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        origin = self.headers.get("Origin")
        if not origin or origin not in _allowed_origins():
            self._send(403, {"error": "origin_not_allowed"})
            return
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "300")
        self.end_headers()

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send(200, {"status": "ok", "decision_mode": "deny_only"})
            return

        match = re.fullmatch("/v1/devices/([^/]+)/diagnostics", self.path)
        if match:
            try:
                report = build_diagnostic_report(match.group(1))
            except ValueError as error:
                self._send(400, {"error": str(error)})
                return
            self._send(200, report)
            return

        self._send(404, {"error": "not_found"})

    def do_POST(self) -> None:
        if self.path != "/v1/decisions":
            self._send(404, {"error": "not_found"})
            return
        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip()
        if content_type != "application/json":
            self._send(415, {"error": "content_type_must_be_application_json"})
            return
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            self._send(400, {"error": "invalid_content_length"})
            return
        if length <= 0 or length > MAX_BODY_BYTES:
            self._send(413 if length > MAX_BODY_BYTES else 400, {"error": "invalid_body_size"})
            return
        try:
            payload = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send(400, {"error": "invalid_json"})
            return
        if not isinstance(payload, dict):
            self._send(400, {"error": "request_must_be_object"})
            return
        if set(payload) != set(REQUIRED_FIELDS):
            self._send(400, {"error": "request_fields_must_match_contract"})
            return
        if any(not isinstance(payload[field], str) or not payload[field].strip()
               for field in REQUIRED_FIELDS):
            self._send(400, {"error": "required_fields_must_be_non_empty_strings"})
            return
        self._send(200, evaluate_decision(payload))

    def log_message(self, format: str, *args: Any) -> None:
        # Do not log request paths: the diagnostics route contains an opaque device reference.
        return


def main() -> None:
    host = os.environ.get("DECISION_API_HOST", "127.0.0.1")
    if host not in {"127.0.0.1", "::1", "localhost"}:
        raise SystemExit("This development server must bind to loopback only.")
    port = int(os.environ.get("DECISION_API_PORT", "0"))
    if not 0 <= port <= 65535:
        raise SystemExit("DECISION_API_PORT must be between 0 and 65535.")
    server = ThreadingHTTPServer((host, port), DecisionHandler)
    print(f"DECISION_API_URL=http://{host}:{server.server_port}", flush=True)
    print("DECISION_API_MODE=DENY_ONLY", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
