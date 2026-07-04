import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import 'package:uuid/uuid.dart';

import '../../core/db/database_service.dart';
import '../../core/models/department.dart';
import '../../core/models/extraction_result.dart';
import '../../core/models/facility.dart';
import '../../core/models/footfall_log.dart';
import '../../core/models/outbox_item.dart';
import '../../core/services/sync_service.dart';
import '../../core/services/voice_service.dart';
import '../../l10n/app_localizations.dart';
import '../../shared/theme.dart';
import '../../shared/widgets/sync_status_chip.dart';
import '../../shared/widgets/voice_input_button.dart';
import '../../shared/widgets/voice_review_sheet.dart';

const _uuid = Uuid();

class FootfallScreen extends StatefulWidget {
  const FootfallScreen({super.key, required this.facility});
  final Facility facility;

  @override
  State<FootfallScreen> createState() => _FootfallScreenState();
}

class _FootfallScreenState extends State<FootfallScreen> {
  final _db = DatabaseService.instance;
  final _countCtrl = TextEditingController(text: '0');

  List<Department> _departments = [];
  List<FootfallLog> _recentLogs = [];
  String? _selectedDepartment;
  DateTime _selectedDate = DateTime.now();
  bool _saving = false;
  bool _voiceProcessing = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _countCtrl.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    final depts = await _db.getDepartments(widget.facility.id);
    final logs = await _db.getFootfallLogs(widget.facility.id, limit: 10);
    if (mounted) setState(() { _departments = depts; _recentLogs = logs; });
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context, initialDate: _selectedDate,
      firstDate: DateTime.now().subtract(const Duration(days: 30)),
      lastDate: DateTime.now(),
      builder: (ctx, child) => Theme(
        data: Theme.of(ctx).copyWith(colorScheme: const ColorScheme.dark(primary: kColorAccent, surface: kColorCard)),
        child: child!,
      ),
    );
    if (picked != null) setState(() => _selectedDate = picked);
  }

  Future<void> _submit() async {
    final l10n = AppLocalizations.of(context);
    final count = int.tryParse(_countCtrl.text.trim()) ?? 0;
    if (count < 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.patientsMustBePositive), backgroundColor: kColorDanger));
      return;
    }
    setState(() => _saving = true);
    final sync = context.read<SyncService>();
    final dateStr = DateFormat('yyyy-MM-dd').format(_selectedDate);
    final now = DateTime.now().toUtc().toIso8601String();
    final id = _uuid.v4();
    final log = FootfallLog(
      id: id, facilityId: widget.facility.id, date: dateStr,
      patientCount: count, department: _selectedDepartment,
      isSimulated: false, basis: 'field app entry',
    );
    await _db.insertFootfallLog(log);
    await _db.enqueue(OutboxItem(
      id: _uuid.v4(), entityType: 'footfall_log', entityId: id, operation: 'create',
      payload: log.toApiJson(), facilityId: widget.facility.id, createdAt: now,
    ));
    await sync.refreshPendingCount();
    sync.drain();
    if (mounted) {
      setState(() { _saving = false; _countCtrl.text = '0'; _selectedDepartment = null; });
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(l10n.footfallSaved),
        backgroundColor: kColorSuccess.withAlpha(200),
      ));
      _load();
    }
  }

  Future<void> _onVoiceStart() async {
    final voice = context.read<VoiceService>();
    if (!await voice.keysConfigured()) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(AppLocalizations.of(context).voiceKeysMissing),
          backgroundColor: kColorDanger,
        ));
      }
      return;
    }
    await voice.startRecording();
  }

  Future<void> _onVoiceStop() async {
    setState(() => _voiceProcessing = true);
    final voice = context.read<VoiceService>();
    final locale = Localizations.localeOf(context).languageCode;
    final result = await voice.stopAndProcess(screen: VoiceScreen.footfall, languageCode: locale);
    setState(() => _voiceProcessing = false);
    if (!mounted) return;
    await VoiceReviewSheet.show(
      context: context,
      result: result,
      onConfirm: _applyExtraction,
      onRetry: () => _onVoiceStart().then((_) => null),
    );
  }

  void _applyExtraction(ExtractionResult r) {
    if (r is! FootfallExtraction) return;
    setState(() {
      _countCtrl.text = r.count.toString();
      if (r.department != null) {
        final query = r.department!.toLowerCase();
        final matched = _departments.cast<Department?>().firstWhere(
          (d) => d!.name.toLowerCase().contains(query) || query.contains(d.name.toLowerCase()),
          orElse: () => null,
        );
        _selectedDepartment = matched?.name;
      } else {
        _selectedDepartment = null;
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.footfall, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
        actions: const [SyncStatusChip(), SizedBox(width: 12)],
      ),
      floatingActionButton: VoiceInputButton(
        tooltip: l10n.voiceInput,
        isProcessing: _voiceProcessing,
        onStart: _onVoiceStart,
        onStop: _onVoiceStop,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(color: kColorCard, borderRadius: BorderRadius.circular(16), border: Border.all(color: kColorBorder)),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(l10n.newEntry, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: kColorTextPrimary)),
              const SizedBox(height: 16),
              GestureDetector(
                onTap: _pickDate,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                  decoration: BoxDecoration(color: kColorSurface, borderRadius: BorderRadius.circular(12), border: Border.all(color: kColorBorder)),
                  child: Row(children: [
                    const Icon(Icons.calendar_today_rounded, size: 16, color: kColorAccent),
                    const SizedBox(width: 10),
                    Text(DateFormat('EEE, d MMM yyyy').format(_selectedDate),
                        style: const TextStyle(fontSize: 14, color: kColorTextPrimary)),
                    const Spacer(),
                    const Icon(Icons.edit_rounded, size: 14, color: kColorTextMuted),
                  ]),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _countCtrl,
                keyboardType: TextInputType.number,
                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: kColorTextPrimary),
                decoration: InputDecoration(
                  labelText: l10n.patientCountLabel,
                  prefixIcon: const Icon(Icons.people_alt_rounded, color: kColorAccent),
                ),
              ),
              const SizedBox(height: 12),
              if (_departments.isNotEmpty)
                DropdownButtonFormField<String?>(
                  initialValue: _selectedDepartment,
                  dropdownColor: kColorCard,
                  style: const TextStyle(color: kColorTextPrimary, fontSize: 14),
                  decoration: InputDecoration(
                    labelText: l10n.departmentOptional,
                    prefixIcon: const Icon(Icons.domain_rounded, color: kColorAccent),
                  ),
                  items: [
                    DropdownMenuItem(value: null, child: Text(l10n.allDepartments, style: const TextStyle(color: kColorTextMuted))),
                    ..._departments.map((d) => DropdownMenuItem(value: d.name, child: Text(d.name))),
                  ],
                  onChanged: (v) => setState(() => _selectedDepartment = v),
                ),
              const SizedBox(height: 20),
              ElevatedButton.icon(
                onPressed: _saving ? null : _submit,
                icon: _saving
                    ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: kColorBackground))
                    : const Icon(Icons.add_chart_rounded),
                label: Text(_saving ? l10n.saving : l10n.logFootfall),
              ),
            ]),
          ),
          const SizedBox(height: 24),
          if (_recentLogs.isNotEmpty) ...[
            Text(l10n.recentEntries, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: kColorTextMuted, letterSpacing: 1)),
            const SizedBox(height: 10),
            ..._recentLogs.map((log) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                decoration: BoxDecoration(color: kColorCard, borderRadius: BorderRadius.circular(10), border: Border.all(color: kColorBorder)),
                child: Row(children: [
                  const Icon(Icons.people_rounded, size: 18, color: kColorAccent),
                  const SizedBox(width: 10),
                  Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(l10n.patients(log.patientCount), style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: kColorTextPrimary)),
                    Text('${log.date}${log.department != null ? ' · ${log.department}' : ''}',
                        style: const TextStyle(fontSize: 12, color: kColorTextMuted)),
                  ])),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(color: kColorAccent.withAlpha(20), borderRadius: BorderRadius.circular(6)),
                    child: Text(l10n.saved, style: const TextStyle(fontSize: 10, color: kColorAccent, fontWeight: FontWeight.w600)),
                  ),
                ]),
              ),
            )),
          ],
        ]),
      ),
    );
  }
}
