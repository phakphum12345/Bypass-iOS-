import 'package:flutter/material.dart';

import '../features/dashboard/dashboard_page.dart';
import '../features/device/device_page.dart';
import '../features/capabilities/capabilities_page.dart';
import '../features/policy/policy_page.dart';
import '../features/authorization/authorization_page.dart';
import '../features/entitlement/entitlement_page.dart';
import '../features/evidence/evidence_page.dart';
import '../features/audit/audit_page.dart';

class AppNavigation {
  const AppNavigation._();

  static const homeRoute = '/';
  static const deviceRoute = '/device';
  static const capabilitiesRoute = '/capabilities';
  static const policyRoute = '/policy';
  static const authorizationRoute = '/authorization';
  static const entitlementRoute = '/entitlement';
  static const evidenceRoute = '/evidence';
  static const auditRoute = '/audit';

  static Map<String, WidgetBuilder> routes() {
    return {
      homeRoute: (_) => const DashboardPage(),
      deviceRoute: (_) => const DevicePage(),
      capabilitiesRoute: (_) => const CapabilitiesPage(),
      policyRoute: (_) => const PolicyPage(),
      authorizationRoute: (_) => const AuthorizationPage(),
      entitlementRoute: (_) => const EntitlementPage(),
      evidenceRoute: (_) => const EvidencePage(),
      auditRoute: (_) => const AuditPage(),
    };
  }
}
