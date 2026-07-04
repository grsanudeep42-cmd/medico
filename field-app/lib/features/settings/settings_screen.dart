import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/services/api_service.dart';
import '../../shared/theme.dart';

/// In-app settings screen for configuring the backend API URL.
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _urlCtrl = TextEditingController();
  bool _loading = true;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _urlCtrl.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    final api = context.read<ApiService>();
    final url = await api.getBaseUrl();
    if (mounted) setState(() { _urlCtrl.text = url; _loading = false; });
  }

  Future<void> _save() async {
    final url = _urlCtrl.text.trim();
    if (url.isEmpty) return;
    setState(() => _saving = true);
    final api = context.read<ApiService>();
    await api.updateBaseUrl(url);
    if (mounted) {
      setState(() => _saving = false);
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('API URL updated. Changes take effect immediately.'),
        backgroundColor: kColorSuccess,
      ));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700))),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: kColorAccent))
          : Padding(
              padding: const EdgeInsets.all(20),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Text('Backend Connection', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: kColorTextMuted, letterSpacing: 1)),
                const SizedBox(height: 12),
                TextField(
                  controller: _urlCtrl,
                  keyboardType: TextInputType.url,
                  style: const TextStyle(color: kColorTextPrimary),
                  decoration: const InputDecoration(
                    labelText: 'API Base URL',
                    hintText: 'http://10.0.2.2:8000',
                    prefixIcon: Icon(Icons.link_rounded, color: kColorAccent),
                  ),
                ),
                const SizedBox(height: 8),
                const Text(
                  'For Android emulator use http://10.0.2.2:8000.\nFor a real device use the server\'s LAN IP.',
                  style: TextStyle(fontSize: 12, color: kColorTextMuted, height: 1.5),
                ),
                const SizedBox(height: 20),
                ElevatedButton.icon(
                  onPressed: _saving ? null : _save,
                  icon: const Icon(Icons.save_rounded),
                  label: Text(_saving ? 'Saving…' : 'Save URL'),
                ),
              ]),
            ),
    );
  }
}
