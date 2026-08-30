enum EvidenceType {
  deviceIdentity,
  capability,
  policy,
  authorization,
  entitlement,
  execution,
}

class EvidenceRequest {
  final String subject;

  const EvidenceRequest({
    required this.subject,
  });
}

class Evidence {
  final String evidenceId;
  final EvidenceType type;
  final String subject;
  final String summary;
  final DateTime timestamp;
  final bool verified;

  const Evidence({
    required this.evidenceId,
    required this.type,
    required this.subject,
    required this.summary,
    required this.timestamp,
    required this.verified,
  });
}
