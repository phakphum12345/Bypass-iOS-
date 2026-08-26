import 'package:flutter/material.dart';

import 'core/engine/decision_engine.dart';
import 'core/models/device.dart';

void main() {
  runApp(const ArchitectureReferenceApp());
}

class ArchitectureReferenceApp extends StatelessWidget {
  const ArchitectureReferenceApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Device Service Architecture',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.indigo,
        ),
        useMaterial3: true,
      ),
      home: const DashboardPage(),
    );
  }
}

class DashboardPage extends StatelessWidget {
  const DashboardPage({super.key});

  static const device = Device(
    deviceId: 'research-device-001',
    platform: 'iOS',
    model: 'Research Device',
    hardwareClass: 'mobile',
    osVersion: 'Research',
    firmwareVersion: 'Research',
    capabilities: <String>[
      'device_identity',
      'capability_detection',
      'service_eligibility',
      'audit_evidence',
    ],
    authorizationState: 'AUTHORIZED',
    serviceState: 'READY',
  );

  @override
  Widget build(BuildContext context) {
    const engine = DecisionEngine();
    final decision = engine.evaluate(device);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Device Service Architecture'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _card(
            context,
            'Research OS',
            'Device Service Architecture',
          ),
          const SizedBox(height: 16),
          _card(
            context,
            'Eligibility Decision',
            decision.decision.name,
          ),
          const SizedBox(height: 16),
          _card(
            context,
            'Device',
            '${device.platform} · ${device.model}\n'
                'ID: ${device.deviceId}',
          ),
        ],
      ),
    );
  }

  Widget _card(
    BuildContext context,
    String title,
    String body,
  ) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 10),
            Text(body),
          ],
        ),
      ),
    );
  }
}
