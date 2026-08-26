class Device {
  final String deviceId;
  final String platform;
  final String model;
  final String hardwareClass;
  final String osVersion;
  final String firmwareVersion;
  final List<String> capabilities;
  final String authorizationState;
  final String serviceState;

  const Device({
    required this.deviceId,
    required this.platform,
    required this.model,
    required this.hardwareClass,
    required this.osVersion,
    required this.firmwareVersion,
    required this.capabilities,
    required this.authorizationState,
    required this.serviceState,
  });
}
