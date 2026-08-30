import '../models/authorization.dart';
import '../models/decision.dart';
import '../models/entitlement.dart';
import '../models/policy.dart';

class SecurityBoundary {
  const SecurityBoundary();

  bool canClientOverrideAuthorization() {
    return false;
  }

  bool requiresServerAuthorization(Policy policy) {
    return policy.requiresServerAuthorization;
  }

  bool allowsExecution({
    required AuthorizationResult authorization,
    required Entitlement entitlement,
    required DecisionResult decision,
  }) {
    return authorization.isAuthorized &&
        entitlement.isActive &&
        decision.allowed;
  }

  String describe() {
    return 'Authorization is enforced outside the client decision surface.';
  }
}
