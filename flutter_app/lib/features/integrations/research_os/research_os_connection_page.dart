import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import 'audit_inspection_report.dart';
import 'research_os_audit_client.dart';

class ResearchOsConnectionPage extends StatefulWidget {
  const ResearchOsConnectionPage({super.key, this.httpClient});

  final http.Client? httpClient;

  @override
  State<ResearchOsConnectionPage> createState() =>
      _ResearchOsConnectionPageState();
}

class _ResearchOsConnectionPageState extends State<ResearchOsConnectionPage> {
  late final ResearchOsAuditClient _client;
  final TextEditingController _baseUrlController = TextEditingController();
  final TextEditingController _tokenController = TextEditingController();

  AuditInspectionReport? _report;
  String? _error;
  DateTime? _lastChecked;
  bool _checking = false;

  @override
  void initState() {
    super.initState();
    _client = ResearchOsAuditClient(client: widget.httpClient);
  }

  @override
  void dispose() {
    _baseUrlController.dispose();
    _tokenController.dispose();
    _client.close();
    super.dispose();
  }

  Future<void> _testConnection() async {
    setState(() {
      _checking = true;
      _error = null;
      _report = null;
    });

    try {
      final report = await _client.inspect(
        baseUrl: _baseUrlController.text,
        bearerToken: _tokenController.text.isEmpty
            ? null
            : _tokenController.text,
      );
      if (!mounted) return;
      setState(() {
        _report = report;
        _lastChecked = DateTime.now();
      });
    } on ResearchOsApiException catch (error) {
      if (!mounted) return;
      setState(() {
        _error = error.message;
        _lastChecked = DateTime.now();
      });
    } finally {
      if (mounted) {
        setState(() {
          _checking = false;
        });
      }
    }
  }

  void _disconnect() {
    setState(() {
      _baseUrlController.clear();
      _tokenController.clear();
      _report = null;
      _error = null;
      _lastChecked = null;
    });
  }

  String get _connectionStatus {
    if (_error != null) return 'NOT CONNECTED';
    return _report?.status ?? 'NOT CONNECTED';
  }

  Color _statusColor(BuildContext context) {
    switch (_connectionStatus) {
      case 'PASS':
        return Colors.green;
      case 'FAIL':
        return Theme.of(context).colorScheme.error;
      case 'UNKNOWN':
        return Colors.orange;
      default:
        return Theme.of(context).colorScheme.outline;
    }
  }

  String _formatLastChecked() {
    final value = _lastChecked;
    if (value == null) return 'Never';
    return value
        .toLocal()
        .toIso8601String()
        .replaceFirst('T', ' ')
        .split('.')
        .first;
  }

  @override
  Widget build(BuildContext context) {
    final report = _report;
    final statusColor = _statusColor(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Research OS Connector'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.hub_outlined),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          'Audit Inspection Connection',
                          style: Theme.of(context).textTheme.titleLarge,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Connect to Research OS as a separate API provider. '
                    'Only the read-only audit inspection endpoint is called.',
                  ),
                  const SizedBox(height: 18),
                  TextField(
                    controller: _baseUrlController,
                    keyboardType: TextInputType.url,
                    autocorrect: false,
                    decoration: const InputDecoration(
                      labelText: 'Research OS API Base URL',
                      hintText: 'https://research.example.com',
                      helperText:
                          'Use an HTTPS origin. HTTP is allowed only for localhost development.',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 14),
                  TextField(
                    controller: _tokenController,
                    obscureText: true,
                    autocorrect: false,
                    enableSuggestions: false,
                    decoration: const InputDecoration(
                      labelText: 'Scoped read-only API credential',
                      helperText:
                          'Required for remote connections. Kept in screen memory only; never saved or placed in the URL.',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Wrap(
                    spacing: 10,
                    runSpacing: 10,
                    children: [
                      FilledButton.icon(
                        onPressed: _checking ? null : _testConnection,
                        icon: _checking
                            ? const SizedBox(
                                width: 16,
                                height: 16,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                ),
                              )
                            : const Icon(Icons.link),
                        label: Text(
                          _checking ? 'Checking...' : 'Test & Inspect',
                        ),
                      ),
                      OutlinedButton.icon(
                        onPressed: _checking ? null : _disconnect,
                        icon: const Icon(Icons.link_off),
                        label: const Text('Disconnect'),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Connection Status',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Icon(Icons.circle, size: 12, color: statusColor),
                      const SizedBox(width: 8),
                      Text(
                        _connectionStatus,
                        style: TextStyle(
                          color: statusColor,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const Spacer(),
                      Text(
                        'Last checked: ${_formatLastChecked()}',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                  if (_error != null) ...[
                    const SizedBox(height: 12),
                    Text(
                      _error!,
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.error,
                      ),
                    ),
                  ],
                  if (report != null) ...[
                    const SizedBox(height: 16),
                    Text('Reason: ${report.reason}'),
                    const Divider(height: 24),
                    _MetricRow(
                      label: 'Ledger events',
                      value: report.ledgerEventCount.toString(),
                    ),
                    _MetricRow(
                      label: 'Checkpoints',
                      value: report.checkpointCount.toString(),
                    ),
                    _MetricRow(
                      label: 'Verified checkpoints',
                      value: report.verifiedCheckpointCount.toString(),
                    ),
                    _MetricRow(
                      label: 'External anchor',
                      value: report.externalAnchorStatus,
                    ),
                    _MetricRow(
                      label: 'Storage trust',
                      value: report.storageTrust,
                    ),
                    if (report.latestCheckpointHash != null)
                      _MetricRow(
                        label: 'Latest checkpoint digest',
                        value: report.latestCheckpointHash!,
                      ),
                  ],
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
          const Card(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Text(
                'Security boundary: read-only audit inspection only. '
                'No device operation, unlock, activation, repair, or bypass '
                'capability is exposed by this connector. A PASS indicates '
                'the provider-reported local consistency result only; it '
                'does not establish an external trust anchor.',
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _MetricRow extends StatelessWidget {
  const _MetricRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(child: Text(label)),
          const SizedBox(width: 12),
          Flexible(
            child: Text(
              value,
              textAlign: TextAlign.end,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ),
        ],
      ),
    );
  }
}
