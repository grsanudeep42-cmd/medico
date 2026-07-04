import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/services/api_service.dart';
import '../../core/services/locale_service.dart';
import '../../core/services/voice_service.dart';
import '../../l10n/app_localizations.dart';
import '../../shared/theme.dart';

/// Settings screen: API URL + Language + AI Keys.
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _urlCtrl = TextEditingController();
  final _whisperCtrl = TextEditingController();
  final _llmCtrl = TextEditingController();
  bool _loading = true;
  bool _savingUrl = false;
  bool _savingKeys = false;
  bool _showWhisper = false;
  bool _showLlm = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _urlCtrl.dispose();
    _whisperCtrl.dispose();
    _llmCtrl.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    final api = context.read<ApiService>();
    final voice = context.read<VoiceService>();
    final url = await api.getBaseUrl();
    final wKey = await voice.getWhisperKey();
    final lKey = await voice.getLlmKey();
    if (mounted) {
      setState(() {
        _urlCtrl.text = url;
        _whisperCtrl.text = wKey;
        _llmCtrl.text = lKey;
        _loading = false;
      });
    }
  }

  Future<void> _saveUrl() async {
    final url = _urlCtrl.text.trim();
    if (url.isEmpty) return;
    setState(() => _savingUrl = true);
    await context.read<ApiService>().updateBaseUrl(url);
    if (mounted) {
      setState(() => _savingUrl = false);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(AppLocalizations.of(context).apiUrlUpdated),
        backgroundColor: kColorSuccess,
      ));
    }
  }

  Future<void> _saveKeys() async {
    setState(() => _savingKeys = true);
    await context.read<VoiceService>().saveKeys(
      whisperKey: _whisperCtrl.text.trim(),
      llmKey: _llmCtrl.text.trim(),
    );
    if (mounted) {
      setState(() => _savingKeys = false);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(AppLocalizations.of(context).keysSaved),
        backgroundColor: kColorSuccess,
      ));
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final localeService = context.watch<LocaleService>();

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.settings, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: kColorAccent))
          : ListView(
              padding: const EdgeInsets.all(20),
              children: [
                // ── Language ──────────────────────────────────────────────
                _SectionHeader(label: l10n.languageLabel),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
                  decoration: BoxDecoration(
                    color: kColorCard,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: kColorBorder),
                  ),
                  child: Row(children: [
                    const Icon(Icons.language_rounded, color: kColorAccent, size: 20),
                    const SizedBox(width: 10),
                    Expanded(
                      child: DropdownButtonHideUnderline(
                        child: DropdownButton<Locale>(
                          value: localeService.locale,
                          dropdownColor: kColorCard,
                          style: const TextStyle(color: kColorTextPrimary, fontSize: 15),
                          items: localeService.options
                              .map((o) => DropdownMenuItem(
                                    value: o.locale,
                                    child: Text('${o.nativeLabel} (${o.label})'),
                                  ))
                              .toList(),
                          onChanged: (l) {
                            if (l != null) localeService.setLocale(l);
                          },
                        ),
                      ),
                    ),
                  ]),
                ),
                const SizedBox(height: 28),

                // ── API URL ───────────────────────────────────────────────
                _SectionHeader(label: l10n.backendConnection),
                TextField(
                  controller: _urlCtrl,
                  keyboardType: TextInputType.url,
                  style: const TextStyle(color: kColorTextPrimary),
                  decoration: InputDecoration(
                    labelText: l10n.apiBaseUrl,
                    hintText: l10n.apiUrlHint,
                    prefixIcon: const Icon(Icons.link_rounded, color: kColorAccent),
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  l10n.apiUrlHelp,
                  style: const TextStyle(fontSize: 12, color: kColorTextMuted, height: 1.5),
                ),
                const SizedBox(height: 12),
                ElevatedButton.icon(
                  onPressed: _savingUrl ? null : _saveUrl,
                  icon: _savingUrl
                      ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: kColorBackground))
                      : const Icon(Icons.save_rounded),
                  label: Text(_savingUrl ? l10n.saving : l10n.saveUrl),
                ),
                const SizedBox(height: 28),

                // ── AI Keys ───────────────────────────────────────────────
                _SectionHeader(label: l10n.aiKeysLabel),
                TextField(
                  controller: _whisperCtrl,
                  obscureText: !_showWhisper,
                  style: const TextStyle(color: kColorTextPrimary),
                  decoration: InputDecoration(
                    labelText: l10n.whisperKeyLabel,
                    prefixIcon: const Icon(Icons.mic_rounded, color: kColorAccent),
                    suffixIcon: IconButton(
                      icon: Icon(_showWhisper ? Icons.visibility_off_rounded : Icons.visibility_rounded, color: kColorTextMuted),
                      onPressed: () => setState(() => _showWhisper = !_showWhisper),
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _llmCtrl,
                  obscureText: !_showLlm,
                  style: const TextStyle(color: kColorTextPrimary),
                  decoration: InputDecoration(
                    labelText: l10n.llmKeyLabel,
                    prefixIcon: const Icon(Icons.psychology_rounded, color: kColorAccent),
                    suffixIcon: IconButton(
                      icon: Icon(_showLlm ? Icons.visibility_off_rounded : Icons.visibility_rounded, color: kColorTextMuted),
                      onPressed: () => setState(() => _showLlm = !_showLlm),
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                ElevatedButton.icon(
                  onPressed: _savingKeys ? null : _saveKeys,
                  icon: _savingKeys
                      ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: kColorBackground))
                      : const Icon(Icons.vpn_key_rounded),
                  label: Text(_savingKeys ? l10n.saving : l10n.saveKeys),
                ),
                const SizedBox(height: 40),
              ],
            ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({required this.label});
  final String label;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 10),
    child: Text(
      label,
      style: const TextStyle(
        fontSize: 11,
        fontWeight: FontWeight.w700,
        color: kColorTextMuted,
        letterSpacing: 1.2,
      ),
    ),
  );
}
