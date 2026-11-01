import json
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from backend.decision_api.server import DecisionHandler


class DeviceDiagnosticsApiTests(unittest.TestCase):
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

    def get(self, path):
        connection = HTTPConnection("127.0.0.1", self.port, timeout=2)
        connection.request("GET", path)
        response = connection.getresponse()
        payload = response.read()
        connection.close()
        return response.status, json.loads(payload) if payload else None

    def test_diagnostics_endpoint_returns_conservative_unknown_report(self):
        status, report = self.get("/v1/devices/opaque-device-001/diagnostics")
        self.assertEqual(status, 200)
        self.assertEqual(report["schema_version"], "1.0")
        self.assertEqual(report["overall_status"], "UNKNOWN")
        self.assertEqual(report["connection"]["status"], "UNKNOWN")
        self.assertEqual(report["security_states"]["activation_lock"], "NOT_INSPECTED")
        self.assertFalse(report["operation_performed"])
        self.assertFalse(report["authorization_granted"])

    def test_diagnostics_endpoint_rejects_non_opaque_reference(self):
        status, body = self.get("/v1/devices/short/diagnostics")
        self.assertEqual(status, 400)
        self.assertEqual(
            body["error"],
            "device_reference_must_be_an_opaque_8_to_64_char_token",
        )

    def test_diagnostics_endpoint_does_not_claim_device_attributes(self):
        status, report = self.get("/v1/devices/opaque-device-001/diagnostics")
        self.assertEqual(status, 200)
        for attribute in ("platform", "model", "os_version"):
            self.assertIsNone(report["device"][attribute]["value"])
            self.assertEqual(report["device"][attribute]["status"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
