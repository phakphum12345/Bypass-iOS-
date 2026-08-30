import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:bypass_architecture_reference/core/engine/decision_engine.dart';
import 'package:bypass_architecture_reference/core/models/decision.dart';
import 'package:bypass_architecture_reference/core/models/device.dart';
import 'package:bypass_architecture_reference/main.dart';

Device testDevice({
  String authorization = 'AUTHORIZED',
  String service = 'READY',
  List<String> capabilities = const ['device_identity'],
}) {
  return Device(
    deviceId: 'test-device',
    platform: 'iOS',
    model: 'Research Device',
    hardwareClass: 'mobile',
    osVersion: 'Research',
    firmwareVersion: 'Research',
    capabilities: capabilities,
    authorizationState: authorization,
    serviceState: service,
  );
}

void main() {
  test('authorized ready device is eligible', () {
    const engine = DecisionEngine();
    final result = engine.evaluate(testDevice());

    expect(result.decision, Decision.eligible);
    expect(result.allowed, isTrue);
  });

  test('unauthorized device requires authorization', () {
    const engine = DecisionEngine();
    final result = engine.evaluate(
      testDevice(authorization: 'UNAUTHORIZED'),
    );

    expect(result.decision, Decision.requiresAuthorization);
    expect(result.allowed, isFalse);
  });

  test('not ready device requires support', () {
    const engine = DecisionEngine();
    final result = engine.evaluate(
      testDevice(service: 'NOT_READY'),
    );

    expect(result.decision, Decision.requiresSupport);
    expect(result.allowed, isFalse);
  });

  test('device without capabilities is unsupported', () {
    const engine = DecisionEngine();
    final result = engine.evaluate(
      testDevice(capabilities: const []),
    );

    expect(result.decision, Decision.unsupported);
    expect(result.allowed, isFalse);
  });

  test('denied decisions remain denied', () {
    const engine = DecisionEngine();

    final results = [
      engine.evaluate(
        testDevice(authorization: 'UNAUTHORIZED'),
      ),
      engine.evaluate(
        testDevice(service: 'NOT_READY'),
      ),
      engine.evaluate(
        testDevice(capabilities: const []),
      ),
    ];

    for (final result in results) {
      expect(result.allowed, isFalse);
      expect(result.decision, isNot(Decision.eligible));
    }
  });

  testWidgets('final dashboard renders architecture and evidence',
      (tester) async {
    await tester.pumpWidget(const ArchitectureReferenceApp());

    expect(find.text('Bypass-iOS Architecture'), findsOneWidget);
    expect(find.text('Eligibility decision'), findsOneWidget);
    expect(find.text('Eligible'), findsWidgets);
    expect(find.text('Identity'), findsOneWidget);
    expect(find.text('Capability'), findsOneWidget);
    expect(find.text('Policy'), findsOneWidget);
    expect(find.text('Authorization'), findsWidgets);
    expect(find.text('Entitlement'), findsWidgets);
    expect(find.text('Execution'), findsWidgets);
    expect(find.text('Evidence'), findsWidgets);

    await tester.scrollUntilVisible(
      find.text('Security boundaries'),
      500,
      scrollable: find.byType(Scrollable),
    );

    expect(find.text('Security boundaries'), findsOneWidget);
    expect(find.text('Server-side authorization'), findsOneWidget);
  });
}
