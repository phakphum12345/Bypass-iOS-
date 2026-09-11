enum EntitlementState {
  active,
  inactive,
  expired,
  revoked,
  unknown,
}

class EntitlementResult {
  const EntitlementResult({
    required this.state,
    required this.reason,
  });

  final EntitlementState state;
  final String reason;

  bool get isActive => state == EntitlementState.active;
}
