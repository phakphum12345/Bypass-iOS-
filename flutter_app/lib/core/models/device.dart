class Device {
  const Device({
    required this.deviceId,
    required this.platform,
    required this.model,
    required this.osVersion,
    required this.capabilities,
  });

  final String deviceId;
  final String platform;
  final String model;
  final String osVersion;
  final List<String> capabilities;
}
