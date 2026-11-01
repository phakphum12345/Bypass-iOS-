import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:bypass_architecture_reference/features/integrations/research_os/research_os_connection_page.dart';

void main() {
  testWidgets('connects, displays a read-only audit result, and disconnects',
      (tester) async {
    final httpClient = MockClient((request) async {
      expect(request.method, 'GET');
      expect(request.url.path, '/v1/audit/inspection');
      expect(request.headers['authorization'], 'Bearer read-only-test-token');
      return http.Response(jsonEncode({
        'status': 'PASS',
        'ledger_event_count': 3,
        'checkpoint_count': 1,
        'verified_checkpoint_count': 1,
        'latest_checkpoint_hash': 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
        'reason': 'audit_consistent',
        'external_anchor_status': 'UNKNOWN',
        'storage_trust': 'UNVERIFIED_LOCAL_DATABASE',
      }), 200);
    });

    await tester.pumpWidget(MaterialApp(
      home: ResearchOsConnectionPage(httpClient: httpClient),
    ));

    expect(find.text('Research OS API Base URL'), findsOneWidget);
    expect(find.text('Test & Inspect'), findsOneWidget);
    expect(find.text('NOT CONNECTED'), findsOneWidget);

    await tester.enterText(
      find.byType(TextField).at(0),
      'https://research.example.test',
    );
    await tester.enterText(
      find.byType(TextField).at(1),
      'read-only-test-token',
    );
    await tester.tap(find.text('Test & Inspect'));
    await tester.pumpAndSettle();

    expect(find.text('PASS'), findsOneWidget);
    expect(find.text('audit_consistent'), findsOneWidget);
    expect(find.text('3'), findsOneWidget);
    expect(find.text('UNKNOWN'), findsOneWidget);

    await tester.tap(find.text('Disconnect'));
    await tester.pumpAndSettle();

    expect(find.text('NOT CONNECTED'), findsOneWidget);
    expect(find.text('Never'), findsOneWidget);
    expect(tester.widget<TextField>(find.byType(TextField).at(0)).controller!.text, isEmpty);
    expect(tester.widget<TextField>(find.byType(TextField).at(1)).controller!.text, isEmpty);
    httpClient.close();
  });
}
