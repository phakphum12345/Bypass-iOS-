import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:bypass_architecture_reference/features/dashboard/dashboard_page.dart';

Widget buildTestApp() {
  return const MaterialApp(
    home: DashboardPage(),
  );
}

void main() {
  testWidgets('dashboard renders security overview', (tester) async {
    await tester.pumpWidget(buildTestApp());
    await tester.pumpAndSettle();

    expect(find.text('Device Security Overview'), findsOneWidget);
    expect(find.text('Device Status'), findsOneWidget);
    expect(find.text('Identity'), findsOneWidget);
    expect(find.text('Capability'), findsOneWidget);
    expect(find.text('Policy'), findsOneWidget);
    expect(find.text('Authorization'), findsOneWidget);
    expect(find.text('Entitlement'), findsOneWidget);
    expect(find.text('Authoritative Decision'), findsOneWidget);
  });

  testWidgets('dashboard starts with unknown security decision', (tester) async {
    await tester.pumpWidget(buildTestApp());
    await tester.pumpAndSettle();

    expect(find.text('UNKNOWN'), findsNWidgets(3));
    expect(
      find.text('No authoritative decision available.'),
      findsOneWidget,
    );
  });

  testWidgets('evaluate decision displays authoritative deny', (tester) async {
    await tester.pumpWidget(buildTestApp());
    await tester.pumpAndSettle();

    final evaluateButton = find.text('Evaluate Decision');
    expect(evaluateButton, findsOneWidget);

    await tester.ensureVisible(evaluateButton);
    await tester.tap(evaluateButton);
    await tester.pumpAndSettle();

    expect(find.text('DENY'), findsOneWidget);
    expect(
      find.text('Awaiting authoritative server decision.'),
      findsOneWidget,
    );
  });

  testWidgets('view evidence opens evidence dialog', (tester) async {
    await tester.pumpWidget(buildTestApp());
    await tester.pumpAndSettle();

    final viewEvidenceButtons = find.text('View Evidence');
    expect(viewEvidenceButtons, findsNWidgets(2));

    await tester.ensureVisible(viewEvidenceButtons.last);
    await tester.tap(viewEvidenceButtons.last);
    await tester.pumpAndSettle();

    expect(find.text('Evidence'), findsOneWidget);
    expect(find.text('Close'), findsOneWidget);
  });
}
