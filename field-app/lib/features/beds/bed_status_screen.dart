import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:uuid/uuid.dart';

import '../../core/db/database_service.dart';
import '../../core/models/bed_snapshot.dart';
import '../../core/models/facility.dart';
import '../../core/models/outbox_item.dart';
import '../../core/services/sync_service.dart';
import '../../shared/theme.dart';
import '../../shared/widgets/sync_status_chip.dart';

const _uuid = Uuid();

class BedStatusScreen extends StatefulWidget {
  const BedStatusScreen({super.key, required this.facility});
  final Facility facility;

  @override
  State<BedStatusScreen> createState() => _BedStatusScreenState();
}

class _BedStatusScreenState extends State<BedStatusScreen> {
  final _db = DatabaseService.instance;
  BedSnapshot? _latest;
  int _total = 0;
  int _occupied = 0;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final snap = await _db.getLatestBedSnapshot(widget.facility.id);
    if (mounted) {
      setState(() {
        _latest = snap;
        _total = snap?.totalBeds ?? widget.facility.sanctionedBeds;
        _occupied = snap?.occupiedBeds ?? 0;
      });
    }
  }

  Future<void> _submit() async {
    if (_occupied > _total) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('Occupied beds cannot exceed total beds'),
        backgroundColor: kColorDanger,
      ));
      return;
    }
    setState(() => _saving = true);
    final sync = context.read<SyncService>();
    final now = DateTime.now().toUtc().toIso8601String();
    final id = _uuid.v4();
    final snap = BedSnapshot(id: id, facilityId: widget.facility.id, totalBeds: _total, occupiedBeds: _occupied, updatedAt: now);
    await _db.insertBedSnapshot(snap);
    await _db.enqueue(OutboxItem(
      id: _uuid.v4(), entityType: 'bed_snapshot', entityId: id, operation: 'create',
      payload: {'total_beds': _total, 'occupied_beds': _occupied, 'updated_at': now},
      facilityId: widget.facility.id, createdAt: now,
    ));
    await sync.refreshPendingCount();
    sync.drain();
    if (mounted) {
      setState(() => _saving = false);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: const Text('Bed snapshot saved. Will sync when online.'),
        backgroundColor: kColorSuccess.withAlpha(200),
      ));
      _load();
    }
  }

  @override
  Widget build(BuildContext context) {
    final occupancy = _total > 0 ? _occupied / _total : 0.0;
    final occupancyColor = occupancy > 0.9 ? kColorDanger : occupancy > 0.7 ? kColorWarning : kColorSuccess;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Bed Status', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
        actions: const [SyncStatusChip(), SizedBox(width: 12)],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(children: [
          // Occupancy ring
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(color: kColorCard, borderRadius: BorderRadius.circular(16), border: Border.all(color: kColorBorder)),
            child: Column(children: [
              Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                SizedBox(width: 120, height: 120, child: Stack(alignment: Alignment.center, children: [
                  CircularProgressIndicator(
                    value: occupancy, strokeWidth: 10,
                    backgroundColor: kColorBorder,
                    color: occupancyColor,
                  ),
                  Column(mainAxisSize: MainAxisSize.min, children: [
                    Text('${(occupancy * 100).toStringAsFixed(0)}%',
                        style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800, color: occupancyColor)),
                    const Text('Occupancy', style: TextStyle(fontSize: 10, color: kColorTextMuted)),
                  ]),
                ])),
              ]),
              const SizedBox(height: 16),
              if (_latest != null) Text(
                'Last recorded: ${_latest!.updatedAt.substring(0, 16).replaceAll('T', ' ')} UTC',
                style: const TextStyle(fontSize: 12, color: kColorTextMuted),
              ),
            ]),
          ),
          const SizedBox(height: 20),
          _StepperCard(
            label: 'Total Beds',
            value: _total,
            onDecrement: _total > 0 ? () => setState(() => _total--) : null,
            onIncrement: () => setState(() => _total++),
          ),
          const SizedBox(height: 12),
          _StepperCard(
            label: 'Occupied Beds',
            value: _occupied,
            onDecrement: _occupied > 0 ? () => setState(() => _occupied--) : null,
            onIncrement: _occupied < _total ? () => setState(() => _occupied++) : null,
          ),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: _saving ? null : _submit,
            icon: _saving
                ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: kColorBackground))
                : const Icon(Icons.save_rounded),
            label: Text(_saving ? 'Saving…' : 'Save Snapshot'),
          ),
        ]),
      ),
    );
  }
}

class _StepperCard extends StatelessWidget {
  const _StepperCard({required this.label, required this.value, this.onDecrement, this.onIncrement});
  final String label;
  final int value;
  final VoidCallback? onDecrement;
  final VoidCallback? onIncrement;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      decoration: BoxDecoration(color: kColorCard, borderRadius: BorderRadius.circular(12), border: Border.all(color: kColorBorder)),
      child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
        Text(label, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: kColorTextPrimary)),
        Row(children: [
          _CircleBtn(icon: Icons.remove, onPressed: onDecrement),
          Padding(padding: const EdgeInsets.symmetric(horizontal: 20),
            child: Text('$value', style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800, color: kColorTextPrimary))),
          _CircleBtn(icon: Icons.add, onPressed: onIncrement),
        ]),
      ]),
    );
  }
}

class _CircleBtn extends StatelessWidget {
  const _CircleBtn({required this.icon, this.onPressed});
  final IconData icon;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {
    return IconButton(
      onPressed: onPressed,
      icon: Icon(icon, size: 20),
      style: IconButton.styleFrom(
        backgroundColor: onPressed != null ? kColorAccent.withAlpha(40) : kColorBorder,
        foregroundColor: onPressed != null ? kColorAccent : kColorTextMuted,
        shape: const CircleBorder(),
        padding: const EdgeInsets.all(8),
      ),
    );
  }
}
