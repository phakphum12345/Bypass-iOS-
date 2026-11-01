import 'dart:convert';

import 'package:http/http.dart' as http;

import 'audit_inspection_report.dart';

class ResearchOsApiException implements Exception {
  const ResearchOsApiException(this.message);

  final String message;

  @override
  String toString() => 'ResearchOsApiException: $message';
}

class ResearchOsAuditClient {
  ResearchOsAuditClient({
    http.Client? client,
    this.timeout = const Duration(seconds: 10),
  }) : _client = client ?? http.Client(),
       _ownsClient = client == null;

  final http.Client _client;
  final bool _ownsClient;
  final Duration timeout;

  Future<AuditInspectionReport> inspect({
    required String baseUrl,
    String? bearerToken,
  }) async {
    final base = _validateBaseUrl(baseUrl);
    final token = bearerToken?.trim();
    final isLoopback =
        const {'localhost', '127.0.0.1', '::1'}
            .contains(base.host.toLowerCase());

    if (!isLoopback && (token == null || token.isEmpty)) {
      throw const ResearchOsApiException(
        'A scoped read-only credential is required for remote Research OS connections.',
      );
    }
    if (token != null && token.contains(RegExp(r'\s'))) {
      throw const ResearchOsApiException(
        'Credential format is invalid. Credentials must not contain whitespace.',
      );
    }

    final uri = base.resolve('/v1/audit/inspection');
    final headers = <String, String>{
      'Accept': 'application/json',
      'Cache-Control': 'no-store',
    };
    if (token != null) {
      headers['Authorization'] = 'Bearer $token';
    }

    late final http.Response response;
    try {
      response = await _client.get(uri, headers: headers).timeout(timeout);
    } on Exception {
      throw const ResearchOsApiException(
        'Research OS could not be reached or the request timed out.',
      );
    }

    if (response.statusCode == 401 || response.statusCode == 403) {
      throw const ResearchOsApiException(
        'Research OS rejected the connection or its read-only permission.',
      );
    }
    if (response.statusCode != 200 && response.statusCode != 503) {
      throw ResearchOsApiException(
        'Research OS returned HTTP ${response.statusCode}.',
      );
    }

    late final Object? decoded;
    try {
      decoded = jsonDecode(response.body);
    } on FormatException {
      throw const ResearchOsApiException(
        'Research OS returned invalid JSON.',
      );
    }
    if (decoded is! Map<String, dynamic>) {
      throw const ResearchOsApiException(
        'Research OS response must be a JSON object.',
      );
    }

    late final AuditInspectionReport report;
    try {
      report = AuditInspectionReport.fromJson(decoded);
    } on FormatException {
      throw const ResearchOsApiException(
        'Research OS response did not match the audit inspection contract.',
      );
    }

    if (response.statusCode == 503 && report.status != 'UNKNOWN') {
      throw const ResearchOsApiException(
        'Research OS returned an inconsistent unavailable response.',
      );
    }
    return report;
  }

  Uri _validateBaseUrl(String value) {
    final parsed = Uri.tryParse(value.trim());
    if (parsed == null ||
        !parsed.hasAuthority ||
        parsed.host.isEmpty ||
        parsed.userInfo.isNotEmpty ||
        parsed.query.isNotEmpty ||
        parsed.fragment.isNotEmpty ||
        (parsed.path.isNotEmpty && parsed.path != '/') ||
        !(parsed.scheme == 'https' ||
            (parsed.scheme == 'http' &&
                const {'localhost', '127.0.0.1', '::1'}
                    .contains(parsed.host.toLowerCase())))) {
      throw const ResearchOsApiException(
        'API URL must be an HTTPS origin. Plain HTTP is allowed only for loopback development.',
      );
    }
    return parsed;
  }

  void close() {
    if (_ownsClient) _client.close();
  }
}
