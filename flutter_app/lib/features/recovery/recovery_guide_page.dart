import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class RecoveryGuidePage extends StatefulWidget {
  const RecoveryGuidePage({super.key});

  @override
  State<RecoveryGuidePage> createState() => _RecoveryGuidePageState();
}

class _RecoveryGuidePageState extends State<RecoveryGuidePage> {
  static const _cases = <String, _RecoveryCase>{
    'not_sure': _RecoveryCase(
      title: 'Help me identify the problem',
      summary:
          'Start with the exact message shown on the iPhone or iPad. This app does not currently read device state over USB.',
      steps: [
        'Write down the exact on-screen message (for example, “iPhone Unavailable”, “Activation Lock”, or “Remote Management”).',
        'Note the iPhone/iPad model and, if known, the iOS/iPadOS version.',
        'On Windows, install or open the official Apple Devices app; use iTunes only if Apple’s instructions for your setup require it.',
        'Do not share your passcode, Apple Account password, verification codes, or recovery key with anyone.',
      ],
      url: 'https://support.apple.com/iphone',
      linkLabel: 'Apple iPhone Support',
    ),
    'passcode': _RecoveryCase(
      title: 'Forgot the screen passcode',
      summary:
          'Apple’s supported recovery process may require erasing and restoring the device. This tool cannot reveal or remove a passcode while preserving data.',
      steps: [
        'If you recently changed the passcode, check Apple’s guidance about using the previous passcode when that option is available.',
        'On Windows, install/open Apple Devices from Microsoft Store, then follow Apple’s recovery-mode instructions for your model.',
        'Choose Restore only after understanding that it erases data on the device. Restore a backup afterward if one is available.',
        'After restore, Activation Lock may still require the Apple Account previously linked to the device.',
      ],
      url: 'https://support.apple.com/en-us/118430',
      linkLabel: 'Apple: If you forgot your iPhone passcode',
    ),
    'activation': _RecoveryCase(
      title: 'Activation Lock / Apple Account',
      summary:
          'Activation Lock is an anti-theft protection. It cannot be removed by this app or by restoring the device.',
      steps: [
        'Sign in with the Apple Account that was previously used to set up the device.',
        'If it is your account but you cannot sign in, use Apple’s account recovery process.',
        'For a second-hand device, ask the previous owner to remove the device from their account using Apple’s official process.',
        'If you have valid proof of purchase, contact Apple Support to ask whether they can assist.',
      ],
      url: 'https://support.apple.com/en-us/108934',
      linkLabel: 'Apple: Activation Lock',
    ),
    'mdm': _RecoveryCase(
      title: 'Remote Management / MDM',
      summary:
          'Organization management is controlled by the organization. This app will not remove or evade an MDM profile.',
      steps: [
        'Contact the organization’s IT administrator or the seller who enrolled the device.',
        'Ask the administrator to verify ownership and release the device from its management system if appropriate.',
        'After the administrator confirms release, follow Apple’s normal setup instructions.',
        'If you bought the device second-hand and the organization cannot be identified, contact the seller for a refund or resolution.',
      ],
      url: 'https://support.apple.com/business-education',
      linkLabel: 'Apple for Business and Education',
    ),
    'unavailable': _RecoveryCase(
      title: 'iPhone Unavailable / disabled',
      summary:
          'This message usually means the device is not accepting passcode attempts. Use Apple’s supported reset or recovery instructions.',
      steps: [
        'Stop guessing passcodes; additional attempts may increase the wait or require a reset.',
        'Follow Apple’s on-device reset option if it is displayed and you know the Apple Account credentials required.',
        'Otherwise, use recovery mode with Apple Devices on Windows and follow Apple’s restore instructions.',
        'A restore erases local data. You may restore a backup afterward; Activation Lock can still appear.',
      ],
      url: 'https://support.apple.com/en-us/118430',
      linkLabel: 'Apple: Passcode recovery',
    ),
  };

  String _selectedCase = 'not_sure';

  Future<void> _copyLink(String url) async {
    await Clipboard.setData(ClipboardData(text: url));
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Official support link copied')),
    );
  }

  Future<void> _copyChecklist(_RecoveryCase recoveryCase) async {
    final checklist = StringBuffer()
      ..writeln(recoveryCase.title)
      ..writeln(recoveryCase.summary)
      ..writeln()
      ..writelnAll(recoveryCase.steps.map((step) => '- $step'))
      ..writeln()
      ..writeln('Official support: ${recoveryCase.url}');
    await Clipboard.setData(ClipboardData(text: checklist.toString()));
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Recovery checklist copied')),
    );
  }

  @override
  Widget build(BuildContext context) {
    final recoveryCase = _cases[_selectedCase]!;

    return Scaffold(
      appBar: AppBar(title: const Text('Official Recovery Assistant')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.verified_user_outlined, size: 28),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Safe, owner-authorized recovery',
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        const SizedBox(height: 8),
                        const Text(
                          'This assistant provides official recovery guidance only. '
                          'It does not connect to or inspect a device, unlock it, '
                          'remove Activation Lock, reveal passcodes, or bypass MDM.',
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 20),
          Text(
            'What do you see on the device?',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 8),
          DropdownButtonFormField<String>(
            value: _selectedCase,
            isExpanded: true,
            decoration: const InputDecoration(
              border: OutlineInputBorder(),
              labelText: 'Choose a problem',
            ),
            items: _cases.entries
                .map(
                  (entry) => DropdownMenuItem<String>(
                    value: entry.key,
                    child: Text(entry.value.title),
                  ),
                )
                .toList(),
            onChanged: (value) {
              if (value != null) setState(() => _selectedCase = value);
            },
          ),
          const SizedBox(height: 20),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    recoveryCase.title,
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 8),
                  Text(recoveryCase.summary),
                  const SizedBox(height: 20),
                  Text(
                    'Recommended steps',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 8),
                  for (var index = 0;
                      index < recoveryCase.steps.length;
                      index++)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          CircleAvatar(
                            radius: 13,
                            child: Text('${index + 1}'),
                          ),
                          const SizedBox(width: 10),
                          Expanded(child: Text(recoveryCase.steps[index])),
                        ],
                      ),
                    ),
                  const Divider(height: 28),
                  Text(
                    'Official resource',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 8),
                  SelectableText(recoveryCase.url),
                  const SizedBox(height: 12),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      FilledButton.icon(
                        onPressed: () => _copyLink(recoveryCase.url),
                        icon: const Icon(Icons.link),
                        label: const Text('Copy official link'),
                      ),
                      OutlinedButton.icon(
                        onPressed: () => _copyChecklist(recoveryCase),
                        icon: const Icon(Icons.content_copy),
                        label: const Text('Copy checklist'),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    recoveryCase.linkLabel,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
          const Text(
            'Privacy: do not paste passwords, passcodes, verification codes, '
            'recovery keys, or personal device identifiers into public issues or logs.',
          ),
        ],
      ),
    );
  }
}

class _RecoveryCase {
  const _RecoveryCase({
    required this.title,
    required this.summary,
    required this.steps,
    required this.url,
    required this.linkLabel,
  });

  final String title;
  final String summary;
  final List<String> steps;
  final String url;
  final String linkLabel;
}
