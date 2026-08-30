import '../models/authorization.dart';
import '../models/decision.dart';
import '../models/device.dart';
import '../models/entitlement.dart';
import '../models/evidence.dart';
import '../models/policy.dart';

class EvidenceService {
  const EvidenceService();

  Evidence record({
    required EvidenceRequest request,
    required Device device,
    required Policy policy,
    required AuthorizationResult authorization,
    required Entitlement entitlement,
    required DecisionResult decision,
  }) {
    return Evidence(
      evidenceId: 'decision-${request.subject}',
      type: EvidenceType.execution,
      subject: request.subject,
      summary: decision.reason,
      timestamp: DateTime.now(),
      verified: decision.allowed &&
          authorization.isAuthorized &&
          entitlement.isActive &&
          device.deviceId.isNotEmpty &&
          policy.policyId.isNotEmpty,
    );
  }
}
