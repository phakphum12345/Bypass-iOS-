import 'package:flutter/material.dart';

import '../../../core/contracts/decision_contract.dart';

class DecisionCard extends StatelessWidget {
  const DecisionCard({
    super.key,
    required this.response,
  });

  final DecisionResponse? response;

  @override
  Widget build(BuildContext context) {
    final decision = response?.decision.decision.name.toUpperCase() ?? 'UNKNOWN';
    final reason =
        response?.decision.reason ?? 'No authoritative decision available.';

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Authoritative Decision',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 16),
            Text(
              decision,
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 8),
            Text(reason),
            const SizedBox(height: 16),
            const Text(
              'The client cannot override this decision.',
            ),
          ],
        ),
      ),
    );
  }
}
