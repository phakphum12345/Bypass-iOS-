import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:bypass_architecture_reference/app/app.dart';

void main() {
  testWidgets('application uses the defensive reference app shell',
      (tester) async {
    await tester.pumpWidget(const DefensiveReferenceApp());
    await tester.pumpAndSettle();

    expect(find.byType(MaterialApp), findsOneWidget);
    expect(find.text('Device Status'), findsOneWidget);
  });

  testWidgets('application exposes the dashboard as the home route',
      (tester) async {
    await tester.pumpWidget(const DefensiveReferenceApp());
    await tester.pumpAndSettle();

    expect(find.text('Device Status'), findsOneWidget);
    expect(find.text('Authorization'), findsOneWidget);
    expect(find.text('Entitlement'), findsOneWidget);
  });
}
