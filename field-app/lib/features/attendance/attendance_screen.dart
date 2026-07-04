import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import 'package:uuid/uuid.dart';

import '../../core/db/database_service.dart';
import '../../core/models/attendance_log.dart';
import '../../core/models/extraction_result.dart';
import '../../core/models/facility.dart';
import '../../core/models/outbox_item.dart';
import '../../core/models/staff.dart';
import '../../core/services/sync_service.dart';
import '../../core/services/voice_service.dart';
import '../../l10n/app_localizations.dart';
import '../../shared/theme.dart';
import '../../shared/widgets/empty_state_widget.dart';
import '../../shared/widgets/sync_status_chip.dart';
import '../../shared/widgets/voice_input_button.dart';
import '../../shared/widgets/voice_review_sheet.dart';

const _uuid = Uuid();

class AttendanceScreen extends StatefulWidget {
  const AttendanceScreen({super.key, required this.facility});
  final Facility facility;

  @override
  State<AttendanceScreen> createState() => _AttendanceScreenState();
}

class _AttendanceScreenState extends State<AttendanceScreen> {
  final _db = DatabaseService.instance;
  List<Staff> _staff = [];
  Map<String, bool> _attendance = {}; // staffId → present
  Map<String, bool> _alreadySubmitted = {};
  DateTime _selectedDate = DateTime.now();
  bool _loading = true;
  bool _saving = false;
  bool _voiceProcessing = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    final staffList = await _db.getStaff(widget.facility.id);
    final staffIds = staffList.map((s) => s.id).toList();
    final dateStr = DateFormat('yyyy-MM-dd').format(_selectedDate);
    final existing = await _db.getAttendanceForDate(staffIds, dateStr);
    if (mounted) {
      setState(() {
        _staff = staffList;
        _alreadySubmitted = existing;
        _attendance = {for (final s in staffList) s.id: existing[s.id] ?? true};
        _loading = false;
      });
    }
  }

  Future<void> _submit() async {
    final l10n = AppLocalizations.of(context);
    setState(() => _saving = true);
    final sync = context.read<SyncService>();
    final dateStr = DateFormat('yyyy-MM-dd').format(_selectedDate);
    final now = DateTime.now().toUtc().toIso8601String();
    final logs = _staff.map((s) => AttendanceLog(
      id: _uuid.v4(), staffId: s.id, date: dateStr,
      present: _attendance[s.id] ?? true,
      isSimulated: false, basis: 'field app check-in',
    )).toList();
    await _db.insertAttendanceLogs(logs);
    for (final log in logs) {
      await _db.enqueue(OutboxItem(
        id: _uuid.v4(), entityType: 'attendance_log', entityId: log.id, operation: 'create',
        payload: log.toApiJson(), facilityId: widget.facility.id, createdAt: now,
      ));
    }
    await sync.refreshPendingCount();
    sync.drain();
    if (mounted) {
      setState(() => _saving = false);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(l10n.attendanceSaved(logs.length)),
        backgroundColor: kColorSuccess.withAlpha(200),
      ));
      _load();
    }
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context, initialDate: _selectedDate,
      firstDate: DateTime.now().subtract(const Duration(days: 30)),
      lastDate: DateTime.now(),
      builder: (context, child) => Theme(
        data: Theme.of(context).copyWith(colorScheme: const ColorScheme.dark(primary: kColorAccent, surface: kColorCard)),
        child: child!,
      ),
    );
    if (picked != null && picked != _selectedDate) {
      setState(() => _selectedDate = picked);
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
    final result = await voice.stopAndProcess(screen: VoiceScreen.attendance, languageCode: locale);
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
    if (r is! AttendanceExtraction) return;
    final status = r.status.toLowerCase() == 'present';
    setState(() {
      for (final name in r.names) {
        final query = name.toLowerCase();
        // Fuzzy match: find the staff member whose name contains the spoken name query
        final matched = _staff.cast<Staff?>().firstWhere(
          (s) => s!.name.toLowerCase().contains(query) || query.contains(s.name.toLowerCase()),
          orElse: () => null,
        );
        if (matched != null) {
          _attendance[matched.id] = status;
        }
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final presentCount = _attendance.values.where((v) => v).length;
    final dateStr = DateFormat('EEE, d MMM yyyy').format(_selectedDate);

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.attendance, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
        actions: const [SyncStatusChip(), SizedBox(width: 12)],
      ),
      floatingActionButton: VoiceInputButton(
        tooltip: l10n.voiceInput,
        isProcessing: _voiceProcessing,
        onStart: _onVoiceStart,
        onStop: _onVoiceStop,
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: kColorAccent))
          : _staff.isEmpty
              ? EmptyStateWidget(
                  icon: Icons.badge_rounded,
                  title: l10n.noStaffTitle,
                  message: l10n.noStaffMessage,
                )
              : Column(children: [
                  GestureDetector(
                    onTap: _pickDate,
                    child: Container(
                      margin: const EdgeInsets.all(16),
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                      decoration: BoxDecoration(
                        color: kColorCard,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: kColorAccent.withAlpha(100)),
                      ),
                      child: Row(children: [
                        const Icon(Icons.calendar_today_rounded, size: 18, color: kColorAccent),
                        const SizedBox(width: 10),
                        Text(dateStr, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: kColorTextPrimary)),
                        const Spacer(),
                        Text(
                          l10n.presentSlashTotal(presentCount, _staff.length),
                          style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: kColorAccent),
                        ),
                        const SizedBox(width: 8),
                        const Icon(Icons.edit_calendar_rounded, size: 16, color: kColorTextMuted),
                      ]),
                    ),
                  ),
                  Expanded(
                    child: ListView.separated(
                      padding: const EdgeInsets.fromLTRB(16, 0, 16, 100),
                      separatorBuilder: (context2, index2) => const SizedBox(height: 8),
                      itemCount: _staff.length,
                      itemBuilder: (_, i) {
                        final s = _staff[i];
                        final isPresent = _attendance[s.id] ?? true;
                        final wasSubmitted = _alreadySubmitted.containsKey(s.id);
                        return Container(
                          decoration: BoxDecoration(
                            color: kColorCard,
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: isPresent ? kColorAccent.withAlpha(60) : kColorDanger.withAlpha(60)),
                          ),
                          child: ListTile(
                            contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
                            leading: CircleAvatar(
                              backgroundColor: isPresent ? kColorAccent.withAlpha(30) : kColorDanger.withAlpha(30),
                              child: Text(
                                s.name.isNotEmpty ? s.name[0].toUpperCase() : '?',
                                style: TextStyle(fontWeight: FontWeight.w700, color: isPresent ? kColorAccent : kColorDanger),
                              ),
                            ),
                            title: Text(s.name, style: const TextStyle(fontWeight: FontWeight.w600, color: kColorTextPrimary)),
                            subtitle: Text(
                              '${s.role}${wasSubmitted ? ' · ${l10n.alreadySubmitted}' : ''}',
                              style: TextStyle(color: wasSubmitted ? kColorAccent : kColorTextMuted, fontSize: 12),
                            ),
                            trailing: Switch(
                              value: isPresent,
                              onChanged: (v) => setState(() => _attendance[s.id] = v),
                            ),
                          ),
                        );
                      },
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
                    decoration: const BoxDecoration(color: kColorSurface, border: Border(top: BorderSide(color: kColorBorder))),
                    child: ElevatedButton.icon(
                      onPressed: _saving ? null : _submit,
                      icon: _saving
                          ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: kColorBackground))
                          : const Icon(Icons.check_circle_rounded),
                      label: Text(_saving ? l10n.saving : l10n.submitAttendance),
                    ),
                  ),
                ]),
    );
  }
}
