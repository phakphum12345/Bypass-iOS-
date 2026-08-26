import 'package:flutter_test/flutter_test.dart';

import 'package:bypass_architecture_reference/core/engine/decision_engine.dart';
import 'package:bypass_architecture_reference/core/models/decision.dart';
import 'package:bypass_architecture_reference/core/models/device.dart';

void main() {
  test('authorized ready device is eligible', () {
    const device = Device(
      deviceId: 'test-device',
      platform: 'iOS',
      model: 'Research Device',
      hardwareClass: 'mobile',
      osVersion: 'Research',
      firmwareVersion: 'Research',
      capabilities: <String>['device_identity'],
      authorizationState: 'AUTHORIZED',
      serviceState: 'READY',
    );

    const engine = DecisionEngine();
    final result = engine.evaluate(device);

    expect(result.decision, Decision.eligible);
    expect(result.allowed, isTrue);
  });

  test('unauthorized device requires authorization', () {
    const device = Device(
      deviceId: 'test-device',
      platform: 'iOS',
      model: 'Research Device',
      hardwareClass: 'mobile',
      osVersion: 'Research',
      firmwareVersion: 'Research',
      capabilities: <String>['device_identity'],
      authorizationState: 'UNAUTHORIZED',
      serviceState: 'READY',
    );

    const engine = DecisionEngine();
    final result = engine.evaluate(device);

    expect(result.decision, Decision.requiresAuthorization);
    expect(result.allowed, isFalse);
  });
}
