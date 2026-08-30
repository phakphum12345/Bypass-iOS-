import '../models/authorization.dart';
import '../models/decision.dart';
import '../models/entitlement.dart';
import '../models/evidence.dart';

class DecisionPipelineResult {
  final Authorization authorization;
  final Entitlement entitlement;
  final Decision decision;
  final Evidence evidence;

  const DecisionPipelineResult({
    required this.authorization,
    required this.entitlement,
    required this.decision,
    required this.evidence,
  });
}
