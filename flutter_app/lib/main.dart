import 'package:flutter/material.dart';

import 'features/dashboard/dashboard_page.dart';

void main() {
  runApp(const DefensiveReferenceApp());
}

class DefensiveReferenceApp extends StatelessWidget {
  const DefensiveReferenceApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Defensive Device Service',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        useMaterial3: true,
      ),
      home: const DashboardPage(),
    );
  }
}
