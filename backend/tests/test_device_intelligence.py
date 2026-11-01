import unittest

from backend.device_intelligence import build_diagnostic_report


class DeviceIntelligenceTests(unittest.TestCase):
    def test_report_is_unknown_without_a_trusted_adapter(self):
        report = build_diagnostic_report("opaque-device-001")
        self.assertEqual(report["overall_status"], "UNKNOWN")
        self.assertEqual(report["connection"]["status"], "UNKNOWN")
        self.assertEqual(report["connection"]["source"], "no_trusted_adapter")
        self.assertIsNone(report["connection"]["observed_at"])

    def test_device_attributes_are_not_invented(self):
        report = build_diagnostic_report("opaque-device-001")
        for attribute in ("platform", "model", "os_version"):
            self.assertEqual(report["device"][attribute]["status"], "UNKNOWN")
            self.assertIsNone(report["device"][attribute]["value"])

    def test_security_sensitive_states_are_not_inspected(self):
        report = build_diagnostic_report("opaque-device-001")
        self.assertEqual(
            report["security_states"],
            {
                "passcode": "NOT_INSPECTED",
                "activation_lock": "NOT_INSPECTED",
                "mdm_enrollment": "NOT_INSPECTED",
                "device_trust": "NOT_INSPECTED",
            },
        )

    def test_report_never_grants_authorization_or_claims_execution(self):
        report = build_diagnostic_report("opaque-device-001")
        self.assertFalse(report["operation_performed"])
        self.assertFalse(report["authorization_granted"])
        self.assertEqual(report["evidence"], [])

    def test_rejects_short_or_blank_reference(self):
        for reference in ("", "   ", "abc123"):
            with self.subTest(reference=reference):
                with self.assertRaises(ValueError):
                    build_diagnostic_report(reference)

    def test_rejects_path_and_control_characters(self):
        for reference in ("device/ref-123", "device\\nref-123", "../device-123"):
            with self.subTest(reference=reference):
                with self.assertRaises(ValueError):
                    build_diagnostic_report(reference)

    def test_rejects_non_string_reference(self):
        with self.assertRaises(ValueError):
            build_diagnostic_report(None)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
