import '../contracts/decision_pipeline_contract.dart';
import '../contracts/decision_pipeline_result.dart';
import '../engine/decision_engine.dart';
import '../services/authorization_service.dart';
import '../services/entitlement_service.dart';
import '../services/evidence_service.dart';

class DecisionPipeline {
  final DecisionEngine decisionEngine;
  final AuthorizationService authorizationService;
  final EntitlementService entitlementService;
  final EvidenceService evidenceService;

  const DecisionPipeline({
    required this.decisionEngine,
    required this.authorizationService,
    required this.entitlementService,
    required this.evidenceService,
  });

  DecisionPipelineResult execute(DecisionPipelineInput input) {
    final authorization =
        authorizationService.authorize(
      input.authorizationRequest,
    );

    final entitlement =
        entitlementService.resolve(
      input.entitlementRequest,
    );

    final decision = decisionEngine.evaluate(
      input.policy,
      input.device,
      authorization,
      entitlement,
    );

    final evidence = evidenceService.record(
      input.evidenceRequest,
      decision,
    );

    return DecisionPipelineResult(
      authorization: authorization,
      entitlement: entitlement,
      decision: decision,
      evidence: evidence,
    );
  }
}
