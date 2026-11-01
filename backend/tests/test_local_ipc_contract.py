import json
import unittest

from backend.local_ipc_contract import (
    IPCContractError,
    MAX_MESSAGE_BYTES,
    validate_request,
    validate_request_bytes,
)


class LocalIPCContractTests(unittest.TestCase):
    def request(self, **overrides):
        value = {
            "schema_version": "1.0",
            "request_id": "req_1234567890abcdef",
            "method": "host.health.read",
            "params": {},
        }
        value.update(overrides)
        return value

    def test_accepts_narrow_health_request(self):
        result = validate_request(self.request())
        self.assertEqual(result["method"], "host.health.read")
        self.assertEqual(result["params"], {})

    def test_accepts_only_allowlisted_diagnostics_method(self):
        result = validate_request(self.request(method="host.diagnostics.read"))
        self.assertEqual(result["method"], "host.diagnostics.read")

    def test_rejects_extra_identity_or_authority_fields(self):
        for key in ("identity", "role", "ownership", "consent", "authorization"):
            with self.subTest(key=key):
                value = self.request()
                value[key] = "claimed"
                with self.assertRaises(IPCContractError):
                    validate_request(value)

    def test_rejects_device_identifiers_and_commands(self):
        for key in ("device_id", "udid", "serial", "command", "shell"):
            with self.subTest(key=key):
                value = self.request()
                value[key] = "not-accepted"
                with self.assertRaises(IPCContractError):
                    validate_request(value)

    def test_rejects_unknown_and_non_string_methods_and_nonempty_params(self):
        for method in ("device.unlock", ["host.health.read"], None):
            with self.subTest(method=method):
                with self.assertRaisesRegex(IPCContractError, "method_not_allowed"):
                    validate_request(self.request(method=method))
        with self.assertRaisesRegex(IPCContractError, "params_must_be_empty_object"):
            validate_request(self.request(params={"verbose": True}))

    def test_rejects_invalid_ids_schema_and_extra_fields(self):
        cases = [
            self.request(request_id="short"),
            self.request(schema_version="9.9"),
            {**self.request(), "unexpected": True},
        ]
        for value in cases:
            with self.subTest(value=value):
                with self.assertRaises(IPCContractError):
                    validate_request(value)

    def test_bytes_parser_enforces_size_and_json(self):
        good = json.dumps(self.request()).encode()
        self.assertEqual(validate_request_bytes(good)["request_id"], "req_1234567890abcdef")
        with self.assertRaisesRegex(IPCContractError, "invalid_message_size"):
            validate_request_bytes(b"x" * (MAX_MESSAGE_BYTES + 1))
        with self.assertRaisesRegex(IPCContractError, "invalid_json"):
            validate_request_bytes(b"{")

    def test_rejects_non_object_and_non_bytes(self):
        with self.assertRaisesRegex(IPCContractError, "request_must_be_object"):
            validate_request([])
        with self.assertRaises(IPCContractError):
            validate_request_bytes("not bytes")


if __name__ == "__main__":
    unittest.main()
