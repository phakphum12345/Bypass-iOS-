import 'package:flutter/material.dart';
import '../features/dashboard/dashboard_page.dart';

class AppNavigation {
  const AppNavigation._();

  static const homeRoute = '/';

  static Map<String, WidgetBuilder> routes() {
    return {
      homeRoute: (_) => const DashboardPage(),
    };
  }
}
