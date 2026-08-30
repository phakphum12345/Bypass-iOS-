enum EntitlementState {
  unknown,
  inactive,
  active,
  revoked,
  expired,
}

class EntitlementRequest {
  final String subject;
  final String capability;

  const EntitlementRequest({
    required this.subject,
    required this.capability,
  });
}

class Entitlement {
  final String entitlementId;
  final String subject;
  final String capability;
  final EntitlementState state;
  final DateTime? expiresAt;

  const Entitlement({
    required this.entitlementId,
    required this.subject,
    required this.capability,
    required this.state,
    this.expiresAt,
  });

  bool get isActive {
    if (state != EntitlementState.active) {
      return false;
    }

    if (expiresAt == null) {
      return true;
    }

    return expiresAt!.isAfter(DateTime.now());
  }
}
