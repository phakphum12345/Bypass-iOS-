enum Decision {
  allowed,
  deny,
}

class DecisionResult {
  const DecisionResult({
    required this.decision,
    required this.reason,
  });

  final Decision decision;
  final String reason;

  bool get isAllowed => decision == Decision.allowed;
}
