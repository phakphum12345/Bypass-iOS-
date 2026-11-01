"""Phase 5 safe recovery guidance planner.

This module creates informational plans for official Apple/organization
recovery channels. It never connects to a device, changes device state,
removes security controls, or grants authorization.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RecoveryScenario(str, Enum):
    UNKNOWN = "unknown"
    FORGOTTEN_PASSCODE = "forgotten_passcode"
    DEVICE_UNAVAILABLE = "device_unavailable"
    ACTIVATION_LOCK = "activation_lock"
    ORGANIZATION_MANAGED = "organization_managed"


class RecoveryDisposition(str, Enum):
    GUIDANCE_ONLY = "GUIDANCE_ONLY"
    SECURITY_CONTROL_BLOCKED = "SECURITY_CONTROL_BLOCKED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class RecoveryStep:
    title: str
    instruction: str
    requires_human_action: bool = True


@dataclass(frozen=True)
class RecoveryPlan:
    scenario: RecoveryScenario
    disposition: RecoveryDisposition
    summary: str
    steps: tuple[RecoveryStep, ...]
    official_resource_url: str | None
    data_loss_warning: str | None = None
    requires_data_loss_acknowledgement: bool = False
    authorization_granted: bool = False
    operation_performed: bool = False


_APPLE_PASSCODE_URL = "https://support.apple.com/en-us/118430"
_APPLE_ACTIVATION_LOCK_URL = "https://support.apple.com/en-us/108934"
_APPLE_BUSINESS_URL = "https://support.apple.com/business-education"
_APPLE_IPHONE_URL = "https://support.apple.com/iphone"


def build_recovery_plan(scenario: RecoveryScenario | str) -> RecoveryPlan:
    """Return a fixed, informational plan; never infer ownership or authority."""
    try:
        selected = (
            scenario
            if isinstance(scenario, RecoveryScenario)
            else RecoveryScenario(scenario)
        )
    except (TypeError, ValueError):
        return RecoveryPlan(
            scenario=RecoveryScenario.UNKNOWN,
            disposition=RecoveryDisposition.UNKNOWN,
            summary="The recovery scenario is not recognized. No action is available.",
            steps=(
                RecoveryStep(
                    "Identify the message",
                    "Read the exact message displayed on the device and consult Apple Support.",
                ),
            ),
            official_resource_url=_APPLE_IPHONE_URL,
        )

    if selected == RecoveryScenario.FORGOTTEN_PASSCODE:
        return RecoveryPlan(
            scenario=selected,
            disposition=RecoveryDisposition.GUIDANCE_ONLY,
            summary=(
                "Use Apple's supported recovery process. Restoring a device "
                "erases its local data; this planner cannot remove or reveal a passcode."
            ),
            steps=(
                RecoveryStep(
                    "Check available passcode options",
                    "If the passcode was changed recently, review Apple's guidance for the previous-passcode option when available.",
                ),
                RecoveryStep(
                    "Prepare a trusted computer",
                    "On Windows, use the official Apple Devices app and follow Apple's recovery-mode instructions for the exact device model.",
                ),
                RecoveryStep(
                    "Review data-loss consequences",
                    "A restore erases local device data. Confirm that you understand this and check whether a usable backup exists before choosing Restore.",
                ),
                RecoveryStep(
                    "Complete Apple's restore process",
                    "Follow the on-screen instructions from Apple. Activation Lock may still require the Apple Account previously linked to the device.",
                ),
            ),
            official_resource_url=_APPLE_PASSCODE_URL,
            data_loss_warning=(
                "Restore erases local data on the device. Backup availability is not verified by this planner."
            ),
            requires_data_loss_acknowledgement=True,
        )

    if selected == RecoveryScenario.DEVICE_UNAVAILABLE:
        return RecoveryPlan(
            scenario=selected,
            disposition=RecoveryDisposition.GUIDANCE_ONLY,
            summary=(
                "Stop guessing passcodes and use Apple's supported on-device "
                "reset or recovery-mode process."
            ),
            steps=(
                RecoveryStep(
                    "Stop passcode attempts",
                    "Do not keep guessing. Wait for the displayed timer or use Apple's supported reset instructions.",
                ),
                RecoveryStep(
                    "Check on-device reset availability",
                    "If the device offers Apple's reset option, follow its requirements and use only the Apple Account belonging to the device owner.",
                ),
                RecoveryStep(
                    "Use recovery mode if needed",
                    "If on-device reset is unavailable, follow Apple's recovery-mode instructions using Apple Devices on Windows.",
                ),
                RecoveryStep(
                    "Review restore consequences",
                    "A restore erases local data. Check backup availability before proceeding; Activation Lock may remain enabled.",
                ),
            ),
            official_resource_url=_APPLE_PASSCODE_URL,
            data_loss_warning=(
                "A restore erases local data. This planner cannot inspect or verify backups."
            ),
            requires_data_loss_acknowledgement=True,
        )

    if selected == RecoveryScenario.ACTIVATION_LOCK:
        return RecoveryPlan(
            scenario=selected,
            disposition=RecoveryDisposition.SECURITY_CONTROL_BLOCKED,
            summary=(
                "Activation Lock is an anti-theft security control. This product "
                "cannot bypass, disable, or remove it."
            ),
            steps=(
                RecoveryStep(
                    "Use the linked Apple Account",
                    "Sign in with the Apple Account previously used to set up the device.",
                ),
                RecoveryStep(
                    "Recover account access",
                    "If you own the account but cannot sign in, use Apple's official account-recovery process.",
                ),
                RecoveryStep(
                    "Contact the previous owner",
                    "For a second-hand device, ask the previous owner to remove it from their account through Apple's official process.",
                ),
                RecoveryStep(
                    "Contact Apple with proof of purchase",
                    "If you have valid proof of purchase, contact Apple Support to ask whether assistance is available.",
                ),
            ),
            official_resource_url=_APPLE_ACTIVATION_LOCK_URL,
        )

    if selected == RecoveryScenario.ORGANIZATION_MANAGED:
        return RecoveryPlan(
            scenario=selected,
            disposition=RecoveryDisposition.SECURITY_CONTROL_BLOCKED,
            summary=(
                "Organization enrollment and management must be handled by "
                "the organization with verified authority. This product cannot "
                "remove or evade MDM."
            ),
            steps=(
                RecoveryStep(
                    "Contact the organization administrator",
                    "Ask the organization's IT or device-management administrator to verify the device's ownership and enrollment status.",
                ),
                RecoveryStep(
                    "Request an authorized release",
                    "If the organization confirms it has authority, ask its administrator to release the device through the official management service.",
                ),
                RecoveryStep(
                    "Verify release before setup",
                    "Proceed with normal Apple setup only after the organization confirms the release.",
                ),
                RecoveryStep(
                    "Resolve second-hand purchase issues",
                    "If the seller cannot provide an authorized release, seek a refund or resolution from the seller.",
                ),
            ),
            official_resource_url=_APPLE_BUSINESS_URL,
        )

    return RecoveryPlan(
        scenario=RecoveryScenario.UNKNOWN,
        disposition=RecoveryDisposition.UNKNOWN,
        summary=(
            "The issue is not yet identified. Record the exact on-screen message "
            "and use Apple's official support resources."
        ),
        steps=(
            RecoveryStep(
                "Record the exact message",
                "Write down the full message shown on the iPhone or iPad without including passwords, passcodes, or verification codes.",
            ),
            RecoveryStep(
                "Identify the model and software",
                "Note the device model and iOS/iPadOS version if known.",
            ),
            RecoveryStep(
                "Consult official support",
                "Use Apple's support resources to identify the supported next step.",
            ),
        ),
        official_resource_url=_APPLE_IPHONE_URL,
    )
