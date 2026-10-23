import 'package:bypass_architecture_reference/features/dashboard/dashboard_page.dart';
import 'package:bypass_architecture_reference/features/recovery/recovery_guide_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('dashboard opens the official recovery assistant', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: DashboardPage()));
    await tester.pumpAndSettle();

    final recoveryButton = find.text('Recovery Assistant');
    await tester.ensureVisible(recoveryButton);
    await tester.tap(recoveryButton);
    await tester.pumpAndSettle();

    expect(find.text('Official Recovery Assistant'), findsOneWidget);
    expect(find.text('Safe, owner-authorized recovery'), findsOneWidget);
    expect(
      find.textContaining('does not connect to or inspect a device'),
      findsOneWidget,
    );
  });

  testWidgets('activation lock guidance points to official Apple support',
      (tester) async {
    await tester.pumpWidget(
      const MaterialApp(home: RecoveryGuidePage()),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byType(DropdownButtonFormField<String>));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Activation Lock / Apple Account').last);
    await tester.pumpAndSettle();

    expect(find.text('Activation Lock is an anti-theft protection. It cannot be removed by this app or by restoring the device.'), findsOneWidget);
    expect(
      find.text('https://support.apple.com/en-us/108934'),
      findsOneWidget,
    );
    expect(find.text('Copy official link'), findsOneWidget);
  });

  testWidgets('passcode recovery warns that restore erases local data',
      (tester) async {
    await tester.pumpWidget(
      const MaterialApp(home: RecoveryGuidePage()),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byType(DropdownButtonFormField<String>));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Forgot the screen passcode').last);
    await tester.pumpAndSettle();

    expect(find.textContaining('erases data on the device'), findsOneWidget);
    expect(
      find.text('https://support.apple.com/en-us/118430'),
      findsOneWidget,
    );
  });
}
