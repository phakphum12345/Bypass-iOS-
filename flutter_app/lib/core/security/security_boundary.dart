import '../models/authorization.dart';
import '../models/decision.dart';
import '../models/entitlement.dart';

class SecurityBoundary {
  const SecurityBoundary();

  bool canClientOverrideAuthorization() => false;

  bool canClientOverrideEntitlement() => false;

  DecisionResult enforce({
    required AuthorizationResult authorization,
    required EntitlementResult entitlement,
  }) {
    if (!authorization.isAllowed) {
      return const DecisionResult(
        decision: Decision.deny,
        reason: 'Authorization is not ALLOWED.',
      );
    }

    if (!entitlement.isActive) {
      return const DecisionResult(
        decision: Decision.deny,
        reason: 'Entitlement is not ACTIVE.',
      );
    }

    return const DecisionResult(
      decision: Decision.allowed,
      reason: 'Authoritative security prerequisites are satisfied.',
    );
  }
}
