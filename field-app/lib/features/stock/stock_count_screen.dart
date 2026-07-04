import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:uuid/uuid.dart';

import '../../core/db/database_service.dart';
import '../../core/models/facility.dart';
import '../../core/models/inventory_item.dart';
import '../../core/models/outbox_item.dart';
import '../../core/models/stock_level.dart';
import '../../core/services/sync_service.dart';
import '../../shared/theme.dart';
import '../../shared/widgets/empty_state_widget.dart';
import '../../shared/widgets/sync_status_chip.dart';

const _uuid = Uuid();

class StockCountScreen extends StatefulWidget {
  const StockCountScreen({super.key, required this.facility});
  final Facility facility;

  @override
  State<StockCountScreen> createState() => _StockCountScreenState();
}

class _StockCountScreenState extends State<StockCountScreen> {
  final _db = DatabaseService.instance;
  List<InventoryItem> _items = [];
  Map<String, StockLevel?> _levels = {};
  Map<String, TextEditingController> _ctrls = {};
  bool _loading = true;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    for (final c in _ctrls.values) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    final items = await _db.getInventoryItems();
    final Map<String, StockLevel?> levels = {};
    final Map<String, TextEditingController> ctrls = {};
    for (final item in items) {
      final sl = await _db.getStockLevelByItem(widget.facility.id, item.id);
      levels[item.id] = sl;
      ctrls[item.id] = TextEditingController(text: sl != null ? sl.quantity.toString() : '0');
    }
    if (mounted) setState(() { _items = items; _levels = levels; _ctrls = ctrls; _loading = false; });
  }

  Future<void> _save() async {
    setState(() => _saving = true);
    final sync = context.read<SyncService>();
    int saved = 0;
    for (final item in _items) {
      final qty = double.tryParse(_ctrls[item.id]?.text.trim() ?? '0') ?? 0;
      final now = DateTime.now().toUtc().toIso8601String();
      final existing = _levels[item.id];
      final levelId = existing?.id ?? _uuid.v4();
      await _db.upsertStockLevel(StockLevel(
        id: levelId, facilityId: widget.facility.id, itemId: item.id,
        quantity: qty, reorderThreshold: existing?.reorderThreshold ?? 0, lastUpdated: now,
      ));
      await _db.enqueue(OutboxItem(
        id: _uuid.v4(), entityType: 'stock_level', entityId: levelId,
        operation: existing == null ? 'create' : 'upsert',
        payload: {'item_id': item.id, 'quantity': qty, 'reorder_threshold': existing?.reorderThreshold ?? 0, 'last_updated': now},
        facilityId: widget.facility.id, createdAt: now,
      ));
      saved++;
    }
    await sync.refreshPendingCount();
    sync.drain();
    if (mounted) {
      setState(() => _saving = false);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text('$saved items saved. Will sync when online.'),
        backgroundColor: kColorSuccess.withAlpha(200),
      ));
      _load();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Stock Count', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
        actions: const [SyncStatusChip(), SizedBox(width: 12)],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: kColorAccent))
          : _items.isEmpty
              ? const EmptyStateWidget(
                  icon: Icons.inventory_2_rounded,
                  title: 'No Inventory Items',
                  message: 'Sync the facility first to load inventory items from the server.',
                )
              : Column(children: [
                  Expanded(
                    child: ListView.separated(
                      padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
                      separatorBuilder: (ctx2, idx2) => const SizedBox(height: 10),
                      itemCount: _items.length,
                      itemBuilder: (_, i) {
                        final item = _items[i];
                        final sl = _levels[item.id];
                        final isLow = sl != null && sl.quantity <= sl.reorderThreshold;
                        return Container(
                          decoration: BoxDecoration(
                            color: kColorCard, borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: isLow ? kColorDanger.withAlpha(100) : kColorBorder),
                          ),
                          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                          child: Row(children: [
                            Container(
                              width: 36, height: 36,
                              decoration: BoxDecoration(color: kColorAccent.withAlpha(20), borderRadius: BorderRadius.circular(10)),
                              child: const Icon(Icons.medication_rounded, color: kColorAccent, size: 18),
                            ),
                            const SizedBox(width: 12),
                            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                              Text(item.name, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: kColorTextPrimary)),
                              Text('${item.category} · ${item.unit}', style: const TextStyle(fontSize: 11, color: kColorTextMuted)),
                              if (isLow) const Text('⚠ Below reorder threshold', style: TextStyle(fontSize: 11, color: kColorDanger)),
                            ])),
                            const SizedBox(width: 12),
                            SizedBox(
                              width: 90,
                              child: TextField(
                                controller: _ctrls[item.id],
                                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                                textAlign: TextAlign.center,
                                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: kColorTextPrimary),
                                decoration: const InputDecoration(contentPadding: EdgeInsets.symmetric(horizontal: 8, vertical: 10)),
                              ),
                            ),
                          ]),
                        );
                      },
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
                    decoration: const BoxDecoration(color: kColorSurface, border: Border(top: BorderSide(color: kColorBorder))),
                    child: ElevatedButton.icon(
                      onPressed: _saving ? null : _save,
                      icon: _saving
                          ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: kColorBackground))
                          : const Icon(Icons.save_rounded),
                      label: Text(_saving ? 'Saving…' : 'Save Stock Count'),
                    ),
                  ),
                ]),
    );
  }
}
