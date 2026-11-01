import unittest

from backend.agent_lifecycle import AgentLifecycle, AgentState


class AgentLifecycleTests(unittest.TestCase):
    def test_happy_start_and_stop_sequence(self):
        lifecycle = AgentLifecycle()
        lifecycle.transition(AgentState.STARTING)
        lifecycle.transition(AgentState.RUNNING)
        self.assertTrue(lifecycle.health()["ready"])
        lifecycle.transition(AgentState.STOPPING)
        lifecycle.transition(AgentState.STOPPED)
        self.assertFalse(lifecycle.health()["ready"])

    def test_failed_start_is_not_ready_and_requires_reset(self):
        lifecycle = AgentLifecycle()
        lifecycle.transition(AgentState.STARTING)
        lifecycle.transition(AgentState.FAILED, failure_code="startup_error")
        report = lifecycle.health()
        self.assertEqual(report["state"], "FAILED")
        self.assertFalse(report["ready"])
        self.assertFalse(report["authorization_granted"])
        lifecycle.transition(AgentState.STOPPED)

    def test_invalid_transitions_are_rejected(self):
        lifecycle = AgentLifecycle()
        with self.assertRaisesRegex(ValueError, "invalid_agent_transition"):
            lifecycle.transition(AgentState.RUNNING)
        lifecycle.transition(AgentState.STARTING)
        lifecycle.transition(AgentState.RUNNING)
        with self.assertRaisesRegex(ValueError, "invalid_agent_transition"):
            lifecycle.transition(AgentState.STARTING)

    def test_failure_requires_safe_code(self):
        lifecycle = AgentLifecycle()
        lifecycle.transition(AgentState.STARTING)
        with self.assertRaisesRegex(ValueError, "failure_code_required"):
            lifecycle.transition(AgentState.FAILED)
        with self.assertRaisesRegex(ValueError, "failure_code_required"):
            lifecycle.transition(AgentState.FAILED, failure_code="private path C:\\Users")

    def test_health_never_claims_operations_or_authorization(self):
        report = AgentLifecycle().health()
        self.assertFalse(report["operation_performed"])
        self.assertFalse(report["authorization_granted"])
        self.assertFalse(report["ready"])


if __name__ == "__main__":
    unittest.main()
