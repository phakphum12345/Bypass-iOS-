import unittest
from unittest.mock import patch

from backend.host_diagnostics import collect_host_diagnostics


class HostDiagnosticsTests(unittest.TestCase):
    def test_report_contains_only_allowlisted_host_facts(self):
        report = collect_host_diagnostics()
        self.assertEqual(report["schema_version"], "1.0")
        self.assertIn(report["host"]["os_family"], {"Windows", "Linux", "Darwin", "OTHER"})
        self.assertIn("architecture", report["host"])
        self.assertIn("runtime", report["host"])
        self.assertEqual(report["evidence"]["collection_mode"], "read_only_allowlist")

    def test_never_claims_attached_device_inspection_or_authorization(self):
        report = collect_host_diagnostics()
        self.assertEqual(report["capabilities"]["attached_device_inspection"], "NOT_CONFIGURED")
        self.assertEqual(report["capabilities"]["security_control_changes"], "NOT_SUPPORTED")
        self.assertFalse(report["operation_performed"])
        self.assertFalse(report["authorization_granted"])

    def test_report_excludes_sensitive_host_identifiers_and_environment(self):
        report = collect_host_diagnostics()
        serialized = repr(report).lower()
        for forbidden in ("hostname", "username", "serial_number", "hardware_uuid",
                          "mac_address", "ip_address", "home_directory", "environment"):
            self.assertNotIn(forbidden, serialized)

    @patch("backend.host_diagnostics.platform.system", return_value="Plan9")
    def test_unknown_os_is_reported_conservatively(self, _mock_system):
        report = collect_host_diagnostics()
        self.assertEqual(report["host"]["os_family"], "OTHER")
        self.assertIsNone(report["host"]["os_release"])
        self.assertEqual(report["host"]["architecture"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
