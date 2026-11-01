import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:bypass_architecture_reference/features/integrations/research_os/research_os_audit_client.dart';

void main() {
  const passReport = {
    'status': 'PASS',
    'ledger_event_count': 4,
    'checkpoint_count': 2,
    'verified_checkpoint_count': 2,
    'latest_checkpoint_hash': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    'reason': 'audit_consistent',
    'external_anchor_status': 'UNKNOWN',
    'storage_trust': 'UNVERIFIED_LOCAL_DATABASE',
  };

  test('calls only the read-only inspection endpoint with bearer header', () async {
    final client = ResearchOsAuditClient(
      client: MockClient((request) async {
        expect(request.method, 'GET');
        expect(request.url.path, '/v1/audit/inspection');
        expect(request.url.query, isEmpty);
        expect(request.headers['authorization'], 'Bearer read-only-secret');
        expect(request.headers['accept'], 'application/json');
        return http.Response(jsonEncode(passReport), 200);
      }),
    );

    final report = await client.inspect(
      baseUrl: 'https://research.example.test',
      bearerToken: 'read-only-secret',
    );

    expect(report.status, 'PASS');
    expect(report.ledgerEventCount, 4);
    expect(report.checkpointCount, 2);
    expect(report.externalAnchorStatus, 'UNKNOWN');
    client.close();
  });

  test('requires a scoped credential for remote HTTPS connections', () async {
    final client = ResearchOsAuditClient(
      client: MockClient((_) async {
        fail('An unauthenticated remote request must never be sent.');
      }),
    );

    await expectLater(
      client.inspect(baseUrl: 'https://research.example.test'),
      throwsA(isA<ResearchOsApiException>()),
    );
    client.close();
  });

  test('accepts an unavailable UNKNOWN response without inventing counts', () async {
    final client = ResearchOsAuditClient(
      client: MockClient((_) async => http.Response(jsonEncode({
        'status': 'UNKNOWN',
        'reason': 'audit_inspection_not_configured',
        'external_anchor_status': 'UNKNOWN',
        'storage_trust': 'UNVERIFIED_LOCAL_DATABASE',
      }), 503)),
    );

    final report = await client.inspect(
      baseUrl: 'http://localhost',
    );

    expect(report.status, 'UNKNOWN');
    expect(report.ledgerEventCount, 0);
    expect(report.reason, 'audit_inspection_not_configured');
    client.close();
  });

  test('rejects public plain HTTP before making a request', () async {
    final client = ResearchOsAuditClient(
      client: MockClient((_) async {
        fail('An insecure remote endpoint must never be called.');
      }),
    );

    await expectLater(
      client.inspect(baseUrl: 'http://research.example.test'),
      throwsA(isA<ResearchOsApiException>()),
    );
    client.close();
  });

  test('rejects URL user information, query strings, and fragments', () async {
    final client = ResearchOsAuditClient(
      client: MockClient((_) async {
        fail('An unsafe URL must never be called.');
      }),
    );

    for (final url in [
      'https://user:secret@research.example.test',
      'https://research.example.test?token=secret',
      'https://research.example.test#fragment',
    ]) {
      await expectLater(
        client.inspect(baseUrl: url, bearerToken: 'read-only-secret'),
        throwsA(isA<ResearchOsApiException>()),
      );
    }
    client.close();
  });

  test('rejects credentials containing whitespace', () async {
    final client = ResearchOsAuditClient(
      client: MockClient((_) async {
        fail('Invalid credentials must never be sent.');
      }),
    );

    await expectLater(
      client.inspect(
        baseUrl: 'https://research.example.test',
        bearerToken: 'secret\nforged',
      ),
      throwsA(isA<ResearchOsApiException>()),
    );
    client.close();
  });

  test('rejects an invalid response status instead of treating it as PASS', () async {
    final client = ResearchOsAuditClient(
      client: MockClient((_) async => http.Response(jsonEncode({
        ...passReport,
        'status': 'CONNECTED',
      }), 200)),
    );

    await expectLater(
      client.inspect(
        baseUrl: 'https://research.example.test',
        bearerToken: 'read-only-secret',
      ),
      throwsA(isA<ResearchOsApiException>()),
    );
    client.close();
  });
}
