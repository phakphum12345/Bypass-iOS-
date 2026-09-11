import '../models/authorization.dart';
import '../models/decision.dart';
import '../models/entitlement.dart';

class DecisionResponse {
  const DecisionResponse({
    required this.correlationId,
    required this.decision,
    required this.authorization,
    required this.entitlement,
    this.reason,
  });

  final String correlationId;
  final DecisionResult decision;
  final AuthorizationResult authorization;
  final EntitlementResult entitlement;
  final String? reason;

  factory DecisionResponse.fromJson(Map<String, dynamic> json) {
    final authorizationValue =
        (json['authorization'] ?? 'UNKNOWN').toString();

    final entitlementValue =
        (json['entitlement'] ?? 'UNKNOWN').toString();

    final decisionValue =
        (json['decision'] ?? 'DENY').toString();

    final authorization = switch (authorizationValue) {
      'ALLOWED' => const AuthorizationResult(
          state: AuthorizationState.allowed,
          reason: 'Authoritative authorization granted.',
        ),
      'DENY' => const AuthorizationResult(
          state: AuthorizationState.denied,
          reason: 'Authoritative authorization denied.',
        ),
      _ => const AuthorizationResult(
          state: AuthorizationState.unknown,
          reason: 'Authorization state is unknown.',
        ),
    };

    final entitlement = switch (entitlementValue) {
      'ACTIVE' => const EntitlementResult(
          state: EntitlementState.active,
          reason: 'Authoritative entitlement is active.',
        ),
      'INACTIVE' => const EntitlementResult(
          state: EntitlementState.inactive,
          reason: 'Entitlement is inactive.',
        ),
      'EXPIRED' => const EntitlementResult(
          state: EntitlementState.expired,
          reason: 'Entitlement has expired.',
        ),
      'REVOKED' => const EntitlementResult(
          state: EntitlementState.revoked,
          reason: 'Entitlement has been revoked.',
        ),
      _ => const EntitlementResult(
          state: EntitlementState.unknown,
          reason: 'Entitlement state is unknown.',
        ),
    };

    final allowed =
        decisionValue == 'ALLOWED' &&
        authorization.isAllowed &&
        entitlement.isActive;

    return DecisionResponse(
      correlationId: (json['correlation_id'] ?? '').toString(),
      authorization: authorization,
      entitlement: entitlement,
      decision: DecisionResult(
        decision: allowed ? Decision.allowed : Decision.deny,
        reason: allowed
            ? 'Server-authoritative decision permits the workflow.'
            : (json['reason'] ?? 'Security prerequisites were not satisfied.')
                .toString(),
      ),
      reason: json['reason']?.toString(),
    );
  }
}
