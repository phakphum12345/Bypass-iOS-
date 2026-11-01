import json
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from backend.decision_api.server import DecisionHandler


class DecisionApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), DecisionHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.server.server_port

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def request(self, method, path, body=None, content_type="application/json"):
        connection = HTTPConnection("127.0.0.1", self.port, timeout=2)
        encoded = None if body is None else json.dumps(body)
        headers = {} if encoded is None else {"Content-Type": content_type}
        connection.request(method, path, body=encoded, headers=headers)
        response = connection.getresponse()
        payload = response.read()
        connection.close()
        return response.status, json.loads(payload) if payload else None

    def test_health_is_explicitly_deny_only(self):
        status, body = self.request("GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(body, {"status": "ok", "decision_mode": "deny_only"})

    def test_valid_request_is_denied_without_trusted_providers(self):
        request = {
            "correlation_id": "corr-1",
            "device_id": "opaque-device-ref",
            "service_id": "diagnostics",
            "action": "inspect",
        }
        status, body = self.request("POST", "/v1/decisions", request)
        self.assertEqual(status, 200)
        self.assertEqual(body["correlation_id"], "corr-1")
        self.assertEqual(body["decision"], "DENY")
        self.assertEqual(body["authorization"], "DENY")
        self.assertEqual(body["entitlement"], "UNKNOWN")
        self.assertIn("No operation was executed", body["reason"])

    def test_client_cannot_submit_authorization_or_entitlement(self):
        request = {
            "correlation_id": "corr-2",
            "device_id": "opaque-device-ref",
            "service_id": "diagnostics",
            "action": "inspect",
            "authorization": "ALLOWED",
            "entitlement": "ACTIVE",
        }
        status, body = self.request("POST", "/v1/decisions", request)
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "request_fields_must_match_contract")

    def test_missing_field_is_rejected(self):
        status, body = self.request("POST", "/v1/decisions", {
            "correlation_id": "corr-3",
            "device_id": "opaque-device-ref",
            "service_id": "diagnostics",
        })
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "request_fields_must_match_contract")

    def test_empty_field_is_rejected(self):
        status, body = self.request("POST", "/v1/decisions", {
            "correlation_id": "corr-4",
            "device_id": " ",
            "service_id": "diagnostics",
            "action": "inspect",
        })
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "required_fields_must_be_non_empty_strings")

    def test_unknown_route_is_not_found(self):
        status, body = self.request("POST", "/v1/execute", {})
        self.assertEqual(status, 404)
        self.assertEqual(body["error"], "not_found")


if __name__ == "__main__":
    unittest.main()
