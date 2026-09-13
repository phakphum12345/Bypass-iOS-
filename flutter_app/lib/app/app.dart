import 'package:flutter/material.dart';
import '../features/dashboard/dashboard_page.dart';
import 'app_theme.dart';
import 'navigation.dart';

class DefensiveReferenceApp extends StatelessWidget {
  const DefensiveReferenceApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Defensive Device Service',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.dark(),
      initialRoute: AppNavigation.homeRoute,
      routes: AppNavigation.routes(),
      home: const DashboardPage(),
    );
  }
}
