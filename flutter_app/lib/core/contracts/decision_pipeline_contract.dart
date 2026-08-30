import '../models/authorization.dart';

import '../models/device.dart';

import '../models/entitlement.dart';

import '../models/evidence.dart';

import '../models/policy.dart';

class DecisionPipelineInput {
  final Policy policy;

  final Device device;

  final AuthorizationRequest authorizationRequest;

  final EntitlementRequest entitlementRequest;

  final EvidenceRequest evidenceRequest;

  const DecisionPipelineInput({
    required this.policy,
    required this.device,
    required this.authorizationRequest,
    required this.entitlementRequest,
    required this.evidenceRequest,
  });
}
