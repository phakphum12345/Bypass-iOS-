import 'package:flutter/material.dart';
import '../features/dashboard/dashboard_page.dart';
import '../features/integrations/research_os/research_os_connection_page.dart';

class AppNavigation {
  const AppNavigation._();

  static const homeRoute = '/';
  static const researchOsAuditRoute = '/integrations/research-os-audit';

  static Map<String, WidgetBuilder> routes() {
    return {
      homeRoute: (_) => const DashboardPage(),
      researchOsAuditRoute: (_) => const ResearchOsConnectionPage(),
    };
  }
}
