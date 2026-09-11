import 'package:flutter/material.dart';

import '../../core/contracts/decision_contract.dart';
import '../../core/services/decision_service.dart';
import 'widgets/decision_card.dart';
import 'widgets/device_card.dart';
import 'widgets/security_gate_card.dart';

class DashboardPage extends StatefulWidget {
  const DashboardPage({super.key});

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  final DecisionService _decisionService = const DecisionService();

  DecisionResponse? _response;

  void _evaluateDecision() {
    // Demonstration only: this represents a response already evaluated
    // by the authoritative server. The client does not manufacture access.
    final response = _decisionService.parseAuthoritativeResponse({
      'correlation_id': 'demo-correlation',
      'decision': 'DENY',
      'authorization': 'DENY',
      'entitlement': 'UNKNOWN',
      'reason': 'Awaiting authoritative server decision.',
    });

    setState(() {
      _response = response;
    });
  }

  void _viewEvidence() {
    showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Evidence'),
        content: Text(
          _response == null
              ? 'No authoritative decision has been evaluated.'
              : 'Correlation ID: ${_response!.correlationId}\n'
                  'Decision: ${_response!.decision.decision.name}\n'
                  'Reason: ${_response!.decision.reason}',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final response = _response;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Security Dashboard'),
        actions: [
          TextButton.icon(
            onPressed: _viewEvidence,
            icon: const Icon(Icons.receipt_long),
            label: const Text('View Evidence'),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Device Security Overview',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 8),
            Text(
              'Authoritative security state supplied by the server.',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: 24),

            const DeviceCard(),

            const SizedBox(height: 16),

            Row(
              children: [
                Expanded(
                  child: SecurityGateCard(
                    title: 'Identity',
                    status: 'VALIDATED',
                    icon: Icons.badge_outlined,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: SecurityGateCard(
                    title: 'Capability',
                    status: 'AVAILABLE',
                    icon: Icons.extension_outlined,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: SecurityGateCard(
                    title: 'Policy',
                    status: 'EVALUATED',
                    icon: Icons.policy_outlined,
                  ),
                ),
              ],
            ),

            const SizedBox(height: 16),

            Row(
              children: [
                Expanded(
                  child: SecurityGateCard(
                    title: 'Authorization',
                    status: response?.authorization.state.name.toUpperCase() ??
                        'UNKNOWN',
                    icon: Icons.lock_outline,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: SecurityGateCard(
                    title: 'Entitlement',
                    status: response?.entitlement.state.name.toUpperCase() ??
                        'UNKNOWN',
                    icon: Icons.verified_user_outlined,
                  ),
                ),
              ],
            ),

            const SizedBox(height: 24),

            DecisionCard(response: response),

            const SizedBox(height: 24),

            Row(
              children: [
                FilledButton.icon(
                  onPressed: _evaluateDecision,
                  icon: const Icon(Icons.fact_check_outlined),
                  label: const Text('Evaluate Decision'),
                ),
                const SizedBox(width: 12),
                OutlinedButton.icon(
                  onPressed: _viewEvidence,
                  icon: const Icon(Icons.receipt_long),
                  label: const Text('View Evidence'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
