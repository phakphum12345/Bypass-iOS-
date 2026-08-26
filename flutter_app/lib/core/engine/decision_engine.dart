import '../models/decision.dart';
import '../models/device.dart';

class DecisionEngine {
  const DecisionEngine();

  DecisionResult evaluate(Device device) {
    if (device.authorizationState != 'AUTHORIZED') {
      return const DecisionResult(
        decision: Decision.requiresAuthorization,
        reason: 'Device authorization is required.',
      );
    }

    if (device.serviceState != 'READY') {
      return const DecisionResult(
        decision: Decision.requiresSupport,
        reason: 'Device service is not ready.',
      );
    }

    if (device.capabilities.isEmpty) {
      return const DecisionResult(
        decision: Decision.unsupported,
        reason: 'No supported device capabilities were detected.',
      );
    }

    return const DecisionResult(
      decision: Decision.eligible,
      reason: 'Device satisfies the current architecture eligibility policy.',
    );
  }
}
