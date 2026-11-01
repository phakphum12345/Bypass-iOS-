import unittest

from backend.recovery_workflow import (
    RecoveryDisposition,
    RecoveryScenario,
    build_recovery_plan,
)


class RecoveryWorkflowTests(unittest.TestCase):
    def test_forgotten_passcode_requires_data_loss_acknowledgement(self):
        plan = build_recovery_plan(RecoveryScenario.FORGOTTEN_PASSCODE)
        self.assertEqual(plan.disposition, RecoveryDisposition.GUIDANCE_ONLY)
        self.assertTrue(plan.requires_data_loss_acknowledgement)
        self.assertIn("erases local data", plan.data_loss_warning)
        self.assertEqual(
            plan.official_resource_url, "https://support.apple.com/en-us/118430"
        )

    def test_device_unavailable_warns_about_restore_and_backup(self):
        plan = build_recovery_plan("device_unavailable")
        self.assertTrue(plan.requires_data_loss_acknowledgement)
        self.assertTrue(any("backup" in step.instruction.lower() for step in plan.steps))

    def test_activation_lock_is_a_security_stop_not_a_bypass_workflow(self):
        plan = build_recovery_plan("activation_lock")
        self.assertEqual(
            plan.disposition, RecoveryDisposition.SECURITY_CONTROL_BLOCKED
        )
        self.assertIn("cannot bypass", plan.summary)
        self.assertTrue(any("previous owner" in step.instruction.lower()
                            for step in plan.steps))

    def test_organization_management_requires_authorized_administrator(self):
        plan = build_recovery_plan("organization_managed")
        self.assertEqual(
            plan.disposition, RecoveryDisposition.SECURITY_CONTROL_BLOCKED
        )
        self.assertIn("cannot remove or evade MDM", plan.summary)
        self.assertTrue(any("administrator" in step.instruction.lower()
                            for step in plan.steps))

    def test_unknown_and_invalid_scenarios_remain_guidance_only(self):
        for scenario in (RecoveryScenario.UNKNOWN, "not-a-real-scenario", None):
            with self.subTest(scenario=scenario):
                plan = build_recovery_plan(scenario)
                self.assertEqual(plan.disposition, RecoveryDisposition.UNKNOWN)
                self.assertIsNotNone(plan.official_resource_url)

    def test_no_plan_grants_authorization_or_performs_operations(self):
        for scenario in RecoveryScenario:
            with self.subTest(scenario=scenario):
                plan = build_recovery_plan(scenario)
                self.assertFalse(plan.authorization_granted)
                self.assertFalse(plan.operation_performed)
                self.assertTrue(all(step.requires_human_action for step in plan.steps))


if __name__ == "__main__":
    unittest.main()
