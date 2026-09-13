import 'package:flutter/material.dart';

class PolicyPage extends StatelessWidget {
  const PolicyPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Policy'),
      ),
      body: const ListTile(
        title: Text('Policy'),
        subtitle: Text(
          'Authoritative policy state is displayed here.',
        ),
      ),
    );
  }
}
