import 'dart:convert';

import 'package:http/http.dart' as http;

import '../contracts/decision_contract.dart';
import '../models/decision_request.dart';

class DecisionApiException implements Exception {
  const DecisionApiException(this.message);

  final String message;

  @override
  String toString() => 'DecisionApiException: $message';
}

class DecisionService {
  DecisionService({
    http.Client? client,
    this.baseUrl = const String.fromEnvironment('DECISION_API_BASE_URL'),
    this.timeout = const Duration(seconds: 8),
  }) : _client = client ?? http.Client();

  final http.Client _client;
  final String baseUrl;
  final Duration timeout;

  DecisionResponse parseAuthoritativeResponse(Map<String, dynamic> json) {
    return DecisionResponse.fromJson(json);
  }

  Future<DecisionResponse> requestDecision(DecisionRequest request) async {
    if (baseUrl.trim().isEmpty) {
      throw const DecisionApiException(
        'Decision API is not configured. Set DECISION_API_BASE_URL.',
      );
    }
    final base = Uri.tryParse(baseUrl);
    if (base == null ||
        !base.hasAuthority ||
        (base.scheme != 'https' &&
            !(base.scheme == 'http' &&
                (base.host == 'localhost' ||
                    base.host == '127.0.0.1' ||
                    base.host == '::1')))) {
      throw const DecisionApiException(
        'Decision API URL must use HTTPS, except for loopback development.',
      );
    }

    final uri = base.resolve('/v1/decisions');
    late final http.Response response;
    try {
      response = await _client
          .post(
            uri,
            headers: const {'Content-Type': 'application/json'},
            body: jsonEncode(request.toJson()),
          )
          .timeout(timeout);
    } on Exception {
      throw const DecisionApiException(
        'Decision API request failed or timed out. No permission is granted.',
      );
    }

    if (response.statusCode != 200) {
      throw DecisionApiException(
        'Decision API returned HTTP ${response.statusCode}. No permission is granted.',
      );
    }

    late final Object? decoded;
    try {
      decoded = jsonDecode(response.body);
    } on FormatException {
      throw const DecisionApiException(
        'Decision API returned invalid JSON. No permission is granted.',
      );
    }
    if (decoded is! Map<String, dynamic>) {
      throw const DecisionApiException(
        'Decision API response must be a JSON object. No permission is granted.',
      );
    }
    if (decoded['correlation_id'] != request.correlationId) {
      throw const DecisionApiException(
        'Decision API correlation ID mismatch. No permission is granted.',
      );
    }
    try {
      return parseAuthoritativeResponse(decoded);
    } on Object {
      throw const DecisionApiException(
        'Decision API response did not match the decision contract. No permission is granted.',
      );
    }
  }

  void close() => _client.close();
}
