import '../models/authorization.dart';
import '../models/device.dart';
import '../models/policy.dart';

class AuthorizationService {
  const AuthorizationService();

  AuthorizationResult authorize(
    AuthorizationRequest request, {
    required Device device,
    required Policy policy,
  }) {
    if (!policy.requiresServerAuthorization) {
      return AuthorizationResult(
        state: AuthorizationState.authorized,
        subject: request.subject,
        reason: 'Server authorization is not required by this policy.',
      );
    }

    if (device.authorizationState == 'AUTHORIZED') {
      return AuthorizationResult(
        state: AuthorizationState.authorized,
        subject: request.subject,
        reason: 'Device authorization is present.',
        evidenceId: 'authorization-device-present',
      );
    }

    return AuthorizationResult(
      state: AuthorizationState.denied,
      subject: request.subject,
      reason: 'Server-side authorization is required.',
      evidenceId: 'authorization-required',
    );
  }
}
