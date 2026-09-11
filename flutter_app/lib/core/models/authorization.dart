enum AuthorizationState {
  allowed,
  denied,
  unknown,
}

class AuthorizationResult {
  const AuthorizationResult({
    required this.state,
    required this.reason,
  });

  final AuthorizationState state;
  final String reason;

  bool get isAllowed => state == AuthorizationState.allowed;
}
