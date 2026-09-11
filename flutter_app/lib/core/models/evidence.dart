class Evidence {
  const Evidence({
    required this.eventId,
    required this.correlationId,
    required this.deviceId,
    required this.result,
    required this.timestamp,
  });

  final String eventId;
  final String correlationId;
  final String deviceId;
  final String result;
  final DateTime timestamp;
}
