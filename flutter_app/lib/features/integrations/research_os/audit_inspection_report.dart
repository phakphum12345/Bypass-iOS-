class AuditInspectionReport {
  const AuditInspectionReport({
    required this.status,
    required this.reason,
    required this.ledgerEventCount,
    required this.checkpointCount,
    required this.verifiedCheckpointCount,
    required this.externalAnchorStatus,
    required this.storageTrust,
    this.latestCheckpointHash,
  });

  final String status;
  final String reason;
  final int ledgerEventCount;
  final int checkpointCount;
  final int verifiedCheckpointCount;
  final String externalAnchorStatus;
  final String storageTrust;
  final String? latestCheckpointHash;

  factory AuditInspectionReport.fromJson(Map<String, dynamic> json) {
    final rawStatus = json['status'];
    if (rawStatus is! String ||
        !const {'PASS', 'FAIL', 'UNKNOWN'}.contains(rawStatus)) {
      throw const FormatException('Invalid audit inspection status.');
    }

    final reason = json['reason'];
    if (reason is! String || reason.isEmpty) {
      throw const FormatException('Missing audit inspection reason.');
    }

    int readCount(String key) {
      final value = json[key];
      if (value == null) return 0;
      if (value is! int || value < 0) {
        throw FormatException('Invalid audit inspection field: $key.');
      }
      return value;
    }

    String readLabel(String key, String fallback) {
      final value = json[key];
      if (value == null) return fallback;
      if (value is! String || value.isEmpty) {
        throw FormatException('Invalid audit inspection field: $key.');
      }
      return value;
    }

    final latestHash = json['latest_checkpoint_hash'];
    if (latestHash != null && latestHash is! String) {
      throw const FormatException('Invalid latest checkpoint hash.');
    }

    return AuditInspectionReport(
      status: rawStatus,
      reason: reason,
      ledgerEventCount: readCount('ledger_event_count'),
      checkpointCount: readCount('checkpoint_count'),
      verifiedCheckpointCount: readCount('verified_checkpoint_count'),
      externalAnchorStatus: readLabel('external_anchor_status', 'UNKNOWN'),
      storageTrust: readLabel(
        'storage_trust',
        'UNVERIFIED_LOCAL_DATABASE',
      ),
      latestCheckpointHash: latestHash as String?,
    );
  }
}
