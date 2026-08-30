enum AuthorizationState {
  unknown,
  pending,
  authorized,
  denied,
  expired,
}

class AuthorizationRequest {
  final String subject;
  final String capability;

  const AuthorizationRequest({
    required this.subject,
    required this.capability,
  });
}

class AuthorizationResult {
  final AuthorizationState state;
  final String subject;
  final String reason;
  final String? evidenceId;

  const AuthorizationResult({
    required this.state,
    required this.subject,
    required this.reason,
    this.evidenceId,
  });

  bool get isAuthorized => state == AuthorizationState.authorized;
}
