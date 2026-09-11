import 'package:flutter_test/flutter_test.dart';

import '../lib/core/models/authorization.dart';
import '../lib/core/models/entitlement.dart';
import '../lib/core/models/decision.dart';
import '../lib/core/security/security_boundary.dart';

void main() {
  const boundary = SecurityBoundary();

  test('client cannot override authorization', () {
    expect(boundary.canClientOverrideAuthorization(), isFalse);
  });

  test('client cannot override entitlement', () {
    expect(boundary.canClientOverrideEntitlement(), isFalse);
  });

  test('unknown authorization is denied', () {
    const authorization = AuthorizationResult(
      state: AuthorizationState.unknown,
      reason: 'unknown',
    );

    const entitlement = EntitlementResult(
      state: EntitlementState.active,
      reason: 'active',
    );

    final result = boundary.enforce(
      authorization: authorization,
      entitlement: entitlement,
    );

    expect(result.decision, Decision.deny);
  });

  test('active entitlement and allowed authorization permit workflow', () {
    const authorization = AuthorizationResult(
      state: AuthorizationState.allowed,
      reason: 'allowed',
    );

    const entitlement = EntitlementResult(
      state: EntitlementState.active,
      reason: 'active',
    );

    final result = boundary.enforce(
      authorization: authorization,
      entitlement: entitlement,
    );

    expect(result.decision, Decision.allowed);
  });
}
