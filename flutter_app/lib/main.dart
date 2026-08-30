import 'package:flutter/material.dart';

import 'core/contracts/decision_pipeline_contract.dart';
import 'core/engine/decision_engine.dart';
import 'core/models/authorization.dart';
import 'core/models/decision.dart';
import 'core/models/device.dart';
import 'core/models/entitlement.dart';
import 'core/models/evidence.dart';
import 'core/models/policy.dart';
import 'core/pipeline/decision_pipeline.dart';
import 'core/security/security_boundary.dart';
import 'core/services/authorization_service.dart';
import 'core/services/entitlement_service.dart';
import 'core/services/evidence_service.dart';

void main() {
  runApp(const ArchitectureReferenceApp());
}

class ArchitectureReferenceApp extends StatelessWidget {
  const ArchitectureReferenceApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Bypass-iOS Architecture Reference',
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

  static const pipeline = DecisionPipeline(
    decisionEngine: DecisionEngine(),
    authorizationService: AuthorizationService(),
    entitlementService: EntitlementService(),
    evidenceService: EvidenceService(),
  );

  static const securityBoundary = SecurityBoundary();

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

  static const stages = <String>[
    'Identity',
    'Capability',
    'Policy',
    'Authorization',
    'Entitlement',
    'Execution',
    'Evidence',
  ];

  @override
  Widget build(BuildContext context) {
    const subject = 'research-device-001';
    const capability = 'device_identity';

    final result = pipeline.execute(
      DecisionPipelineInput(
        policy: Policy.baseline,
        device: device,
        authorizationRequest: AuthorizationRequest(
          subject: subject,
          capability: capability,
        ),
        entitlementRequest: EntitlementRequest(
          subject: subject,
          capability: capability,
        ),
        evidenceRequest: EvidenceRequest(
          subject: subject,
        ),
      ),
    );

    final executionAllowed = securityBoundary.allowsExecution(
      authorization: result.authorization,
      entitlement: result.entitlement,
      decision: result.decision,
    );

    return Scaffold(
      appBar: AppBar(
        title: const Text('Bypass-iOS Architecture'),
        actions: const [
          Padding(
            padding: EdgeInsets.only(right: 16),
            child: Center(
              child: Text('v1.0.0'),
            ),
          ),
        ],
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
          children: [
            _DecisionCard(result: result.decision),
            const SizedBox(height: 16),
            _ExecutionGate(
              allowed: executionAllowed,
              authorization: result.authorization,
              entitlement: result.entitlement,
              decision: result.decision,
            ),
            const SizedBox(height: 16),
            _SectionCard(
              title: 'Architecture flow',
              icon: Icons.account_tree_outlined,
              child: Column(
                children: [
                  for (var i = 0; i < stages.length; i++) ...[
                    _StageRow(
                      number: i + 1,
                      title: stages[i],
                    ),
                    if (i < stages.length - 1)
                      const Padding(
                        padding: EdgeInsets.only(left: 20),
                        child: Align(
                          alignment: Alignment.centerLeft,
                          child: SizedBox(
                            height: 18,
                            child: VerticalDivider(width: 1),
                          ),
                        ),
                      ),
                  ],
                ],
              ),
            ),
            const SizedBox(height: 16),
            _SectionCard(
              title: 'Device context',
              icon: Icons.devices_other_outlined,
              child: Column(
                children: [
                  _InfoRow('Platform', device.platform),
                  _InfoRow('Model', device.model),
                  _InfoRow('Hardware', device.hardwareClass),
                  _InfoRow('OS', device.osVersion),
                  _InfoRow('Firmware', device.firmwareVersion),
                  _InfoRow('Device ID', device.deviceId),
                  _InfoRow(
                    'Capabilities',
                    '${device.capabilities.length} detected',
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            _SectionCard(
              title: 'Security boundaries',
              icon: Icons.shield_outlined,
              child: const Column(
                children: [
                  _BoundaryRow(
                    title: 'Server-side authorization',
                    detail: 'Authorization is evaluated outside the client UI.',
                  ),
                  _BoundaryRow(
                    title: 'Client decision boundary',
                    detail:
                        'A denied decision cannot be converted into allowed state.',
                  ),
                  _BoundaryRow(
                    title: 'Research boundary',
                    detail:
                        'This reference implementation does not bypass platform security controls.',
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            _SectionCard(
              title: 'Evidence',
              icon: Icons.fact_check_outlined,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Decision reason',
                    style: Theme.of(context).textTheme.labelLarge,
                  ),
                  const SizedBox(height: 6),
                  Text(result.decision.reason),
                  const SizedBox(height: 12),
                  const Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      Chip(label: Text('Authentication')),
                      Chip(label: Text('Authorization')),
                      Chip(label: Text('Replay Protection')),
                      Chip(label: Text('Audit')),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ExecutionGate extends StatelessWidget {
  const _ExecutionGate({
    required this.allowed,
    required this.authorization,
    required this.entitlement,
    required this.decision,
  });

  final bool allowed;
  final AuthorizationResult authorization;
  final Entitlement entitlement;
  final DecisionResult decision;

  @override
  Widget build(BuildContext context) {
    return _SectionCard(
      title: 'Execution gate',
      icon: allowed ? Icons.lock_open_outlined : Icons.lock_outline,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _InfoRow(
            'Authorization',
            authorization.isAuthorized ? 'Authorized' : 'Denied',
          ),
          _InfoRow(
            'Entitlement',
            entitlement.isActive ? 'Active' : 'Inactive',
          ),
          _InfoRow(
            'Decision',
            decision.allowed ? 'Eligible' : 'Blocked',
          ),
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: allowed ? () {} : null,
              icon: Icon(
                allowed ? Icons.play_arrow_outlined : Icons.block_outlined,
              ),
              label: Text(
                allowed ? 'Execute' : 'Execution blocked',
              ),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            allowed
                ? 'Execution passed the security boundary.'
                : 'Execution is blocked by the security boundary.',
          ),
        ],
      ),
    );
  }
}

class _DecisionCard extends StatelessWidget {
  const _DecisionCard({required this.result});

  final DecisionResult result;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final allowed = result.allowed;

    return Card(
      elevation: 0,
      color: allowed ? scheme.primaryContainer : scheme.errorContainer,
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(
              allowed ? Icons.verified_outlined : Icons.block_outlined,
              size: 34,
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Eligibility decision',
                    style: Theme.of(context).textTheme.labelLarge,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    _label(result.decision),
                    style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    allowed
                        ? 'Execution is eligible.'
                        : 'Execution is not eligible.',
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _label(Decision decision) {
    switch (decision) {
      case Decision.eligible:
        return 'Eligible';
      case Decision.ineligible:
        return 'Ineligible';
      case Decision.unsupported:
        return 'Unsupported';
      case Decision.requiresAuthorization:
        return 'Requires authorization';
      case Decision.requiresOwnerAction:
        return 'Requires owner action';
      case Decision.requiresSupport:
        return 'Requires support';
    }
  }
}

class _SectionCard extends StatelessWidget {
  const _SectionCard({
    required this.title,
    required this.icon,
    required this.child,
  });

  final String title;
  final IconData icon;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, size: 22),
                const SizedBox(width: 10),
                Text(
                  title,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            child,
          ],
        ),
      ),
    );
  }
}

class _StageRow extends StatelessWidget {
  const _StageRow({
    required this.number,
    required this.title,
  });

  final int number;
  final String title;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    return Row(
      children: [
        CircleAvatar(
          radius: 16,
          backgroundColor: scheme.primary,
          foregroundColor: scheme.onPrimary,
          child: Text('$number'),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Text(
            title,
            style: Theme.of(context).textTheme.bodyLarge,
          ),
        ),
        Icon(
          Icons.check_circle_outline,
          size: 20,
          color: scheme.primary,
        ),
      ],
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow(this.label, this.value);

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 105,
            child: Text(
              label,
              style: Theme.of(context).textTheme.labelMedium,
            ),
          ),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }
}

class _BoundaryRow extends StatelessWidget {
  const _BoundaryRow({
    required this.title,
    required this.detail,
  });

  final String title;
  final String detail;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.lock_outline, size: 20),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: Theme.of(context).textTheme.titleSmall,
                ),
                const SizedBox(height: 3),
                Text(detail),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
