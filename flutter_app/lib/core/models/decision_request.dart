class DecisionRequest {
  const DecisionRequest({
    required this.correlationId,
    required this.deviceId,
    required this.serviceId,
    required this.action,
  });

  final String correlationId;
  final String deviceId;
  final String serviceId;
  final String action;

  Map<String, String> toJson() => {
        'correlation_id': correlationId,
        'device_id': deviceId,
        'service_id': serviceId,
        'action': action,
      };
}
