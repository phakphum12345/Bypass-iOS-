import '../models/authorization.dart';
import '../models/entitlement.dart';

class EntitlementService {
  const EntitlementService();

  Entitlement resolve(
    EntitlementRequest request, {
    required AuthorizationResult authorization,
  }) {
    if (!authorization.isAuthorized) {
      return Entitlement(
        entitlementId: 'none',
        subject: request.subject,
        capability: request.capability,
        state: EntitlementState.inactive,
      );
    }

    return Entitlement(
      entitlementId: 'baseline-${request.capability}',
      subject: request.subject,
      capability: request.capability,
      state: EntitlementState.active,
    );
  }
}
