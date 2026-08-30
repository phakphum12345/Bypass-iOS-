import 'package:flutter_test/flutter_test.dart';

import 'package:bypass_architecture_reference/core/contracts/decision_pipeline_contract.dart';
import 'package:bypass_architecture_reference/core/engine/decision_engine.dart';
import 'package:bypass_architecture_reference/core/models/authorization.dart';
import 'package:bypass_architecture_reference/core/models/device.dart';
import 'package:bypass_architecture_reference/core/models/decision.dart';
import 'package:bypass_architecture_reference/core/models/entitlement.dart';
import 'package:bypass_architecture_reference/core/models/evidence.dart';
import 'package:bypass_architecture_reference/core/models/policy.dart';
import 'package:bypass_architecture_reference/core/pipeline/decision_pipeline.dart';
import 'package:bypass_architecture_reference/core/security/security_boundary.dart';
import 'package:bypass_architecture_reference/core/services/authorization_service.dart';
import 'package:bypass_architecture_reference/core/services/entitlement_service.dart';
import 'package:bypass_architecture_reference/core/services/evidence_service.dart';

Device makeDevice({
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

DecisionPipeline makePipeline() {
  return const DecisionPipeline(
    decisionEngine: DecisionEngine(),
    authorizationService: AuthorizationService(),
    entitlementService: EntitlementService(),
    evidenceService: EvidenceService(),
  );
}

DecisionPipelineInput makeInput({
  Device? device,
  Policy policy = Policy.baseline,
}) {
  const subject = 'test-subject';
  const capability = 'device_identity';

  return DecisionPipelineInput(
    policy: policy,
    device: device ?? makeDevice(),
    authorizationRequest: const AuthorizationRequest(
      subject: subject,
      capability: capability,
    ),
    entitlementRequest: const EntitlementRequest(
      subject: subject,
      capability: capability,
    ),
    evidenceRequest: const EvidenceRequest(
      subject: subject,
    ),
  );
}

void main() {
  test('authorized device passes the complete decision pipeline', () {
    final result = makePipeline().execute(makeInput());

    expect(result.authorization.state, AuthorizationState.authorized);
    expect(result.authorization.isAuthorized, isTrue);

    expect(result.entitlement.state, EntitlementState.active);
    expect(result.entitlement.isActive, isTrue);

    expect(result.decision.allowed, isTrue);

    expect(result.evidence.type, EvidenceType.execution);
    expect(result.evidence.verified, isTrue);
  });

  test('denied authorization cannot produce active entitlement', () {
    final result = makePipeline().execute(
      makeInput(
        device: makeDevice(authorization: 'UNAUTHORIZED'),
      ),
    );

    expect(result.authorization.state, AuthorizationState.denied);
    expect(result.authorization.isAuthorized, isFalse);

    expect(result.entitlement.state, EntitlementState.inactive);
    expect(result.entitlement.isActive, isFalse);

    expect(result.decision.allowed, isFalse);
    expect(result.decision.decision, isNot(Decision.eligible));

    expect(result.evidence.verified, isFalse);
  });

  test('authorization failure remains a decision denial', () {
    final result = makePipeline().execute(
      makeInput(
        device: makeDevice(authorization: 'UNAUTHORIZED'),
      ),
    );

    expect(result.authorization.isAuthorized, isFalse);
    expect(result.decision.allowed, isFalse);
    expect(result.evidence.verified, isFalse);
  });

  test('unsupported device cannot become eligible through entitlement', () {
    final result = makePipeline().execute(
      makeInput(
        device: makeDevice(capabilities: const []),
      ),
    );

    expect(result.authorization.isAuthorized, isTrue);
    expect(result.entitlement.isActive, isTrue);

    expect(result.decision.decision, Decision.unsupported);
    expect(result.decision.allowed, isFalse);
    expect(result.evidence.verified, isFalse);
  });

  test('security boundary rejects client authorization override', () {
    const boundary = SecurityBoundary();

    expect(boundary.canClientOverrideAuthorization(), isFalse);
  });

  test('security boundary allows execution only for authoritative eligibility',
      () {
    const boundary = SecurityBoundary();

    const authorized = AuthorizationResult(
      state: AuthorizationState.authorized,
      subject: 'authorized-subject',
      reason: 'authorized',
    );

    const denied = AuthorizationResult(
      state: AuthorizationState.denied,
      subject: 'denied-subject',
      reason: 'denied',
    );

    const activeEntitlement = Entitlement(
      entitlementId: 'entitled',
      subject: 'authorized-subject',
      capability: 'device_identity',
      state: EntitlementState.active,
    );

    const inactiveEntitlement = Entitlement(
      entitlementId: 'none',
      subject: 'authorized-subject',
      capability: 'device_identity',
      state: EntitlementState.inactive,
    );

    const eligible = DecisionResult(
      decision: Decision.eligible,
      reason: 'eligible',
    );

    const unsupported = DecisionResult(
      decision: Decision.unsupported,
      reason: 'unsupported',
    );

    expect(
      boundary.allowsExecution(
        authorization: authorized,
        entitlement: activeEntitlement,
        decision: eligible,
      ),
      isTrue,
    );

    expect(
      boundary.allowsExecution(
        authorization: denied,
        entitlement: activeEntitlement,
        decision: eligible,
      ),
      isFalse,
    );

    expect(
      boundary.allowsExecution(
        authorization: authorized,
        entitlement: inactiveEntitlement,
        decision: eligible,
      ),
      isFalse,
    );

    expect(
      boundary.allowsExecution(
        authorization: authorized,
        entitlement: activeEntitlement,
        decision: unsupported,
      ),
      isFalse,
    );
  });

  test('baseline policy forbids client override', () {
    expect(Policy.baseline.requiresServerAuthorization, isTrue);
    expect(Policy.baseline.allowsClientOverride, isFalse);
  });
}
