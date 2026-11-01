import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:bypass_architecture_reference/core/models/decision_request.dart';
import 'package:bypass_architecture_reference/core/services/decision_service.dart';

void main() {
  const request = DecisionRequest(
    correlationId: 'corr-test',
    deviceId: 'opaque-device-ref',
    serviceId: 'diagnostics',
    action: 'inspect',
  );

  test('refuses to call API when base URL is not configured', () async {
    final service = DecisionService(client: MockClient((_) async {
      fail('HTTP client must not be called');
    }));
    await expectLater(
      service.requestDecision(request),
      throwsA(isA<DecisionApiException>()),
    );
    service.close();
  });

  test('accepts a valid server deny response', () async {
    final service = DecisionService(
      baseUrl: 'http://127.0.0.1:8080',
      client: MockClient((http.Request req) async {
        expect(req.url.path, '/v1/decisions');
        expect(jsonDecode(req.body), request.toJson());
        return http.Response(jsonEncode({
          'correlation_id': 'corr-test',
          'decision': 'DENY',
          'authorization': 'DENY',
          'entitlement': 'UNKNOWN',
          'reason': 'deny-only test backend',
        }), 200);
      }),
    );
    final result = await service.requestDecision(request);
    expect(result.decision.isAllowed, isFalse);
    expect(result.authorization.isAllowed, isFalse);
    expect(result.entitlement.isActive, isFalse);
    service.close();
  });

  test('rejects mismatched correlation IDs', () async {
    final service = DecisionService(
      baseUrl: 'https://api.example.test',
      client: MockClient((_) async => http.Response(jsonEncode({
        'correlation_id': 'another-request',
        'decision': 'ALLOWED',
        'authorization': 'ALLOWED',
        'entitlement': 'ACTIVE',
      }), 200)),
    );
    await expectLater(
      service.requestDecision(request),
      throwsA(isA<DecisionApiException>()),
    );
    service.close();
  });

  test('rejects incomplete decision response fields', () async {
    final service = DecisionService(
      baseUrl: 'https://api.example.test',
      client: MockClient((_) async => http.Response(jsonEncode({
        'correlation_id': 'corr-test',
        'decision': 'DENY',
        'authorization': 'DENY',
      }), 200)),
    );
    await expectLater(
      service.requestDecision(request),
      throwsA(isA<DecisionApiException>()),
    );
    service.close();
  });

  test('rejects unexpected decision response fields', () async {
    final service = DecisionService(
      baseUrl: 'https://api.example.test',
      client: MockClient((_) async => http.Response(jsonEncode({
        'correlation_id': 'corr-test',
        'decision': 'DENY',
        'authorization': 'DENY',
        'entitlement': 'UNKNOWN',
        'client_override': true,
      }), 200)),
    );
    await expectLater(
      service.requestDecision(request),
      throwsA(isA<DecisionApiException>()),
    );
    service.close();
  });

  test('rejects malformed JSON', () async {
    final service = DecisionService(
      baseUrl: 'https://api.example.test',
      client: MockClient((_) async => http.Response('not-json', 200)),
    );
    await expectLater(
      service.requestDecision(request),
      throwsA(isA<DecisionApiException>()),
    );
    service.close();
  });

  test('rejects non-success HTTP status', () async {
    final service = DecisionService(
      baseUrl: 'https://api.example.test',
      client: MockClient((_) async => http.Response('{}', 503)),
    );
    await expectLater(
      service.requestDecision(request),
      throwsA(isA<DecisionApiException>()),
    );
    service.close();
  });

  test('rejects a client-side plain HTTP endpoint outside loopback', () async {
    final service = DecisionService(
      baseUrl: 'http://api.example.test',
      client: MockClient((_) async {
        fail('HTTP client must not be called');
      }),
    );
    await expectLater(
      service.requestDecision(request),
      throwsA(isA<DecisionApiException>()),
    );
    service.close();
  });
}
