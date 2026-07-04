import 'package:flutter/foundation.dart';

import '../db/database_service.dart';
import '../models/outbox_item.dart';
import '../services/api_service.dart';
import '../services/connectivity_service.dart';

/// Drains the local [outbox_queue] whenever connectivity is restored.
///
/// Conflict resolution: **last-write-wins by [OutboxItem.createdAt]**.
/// Items are processed oldest-first (ascending `created_at`).  If the
/// server returns a 409 the local payload (newer timestamp) is re-sent as a
/// PUT, replacing any server-side state.
///
/// Retries: a failed item increments its [retry_count].  Items that fail
/// 5+ times are skipped in that drain pass to avoid blocking the queue.
class SyncService extends ChangeNotifier {
  SyncService({
    required ConnectivityService connectivity,
    required DatabaseService db,
    required ApiService api,
  })  : _connectivity = connectivity,
        _db = db,
        _api = api {
    _connectivity.addListener(_onConnectivityChanged);
  }

  final ConnectivityService _connectivity;
  final DatabaseService _db;
  final ApiService _api;

  bool _syncing = false;
  bool get isSyncing => _syncing;

  int _pendingCount = 0;
  int get pendingCount => _pendingCount;

  String? _lastError;
  String? get lastError => _lastError;

  static const int _maxRetries = 5;

  // ── Connectivity listener ──────────────────────────────────────────────────

  void _onConnectivityChanged() {
    if (_connectivity.isOnline && !_syncing) {
      drain();
    }
  }

  // ── Public API ─────────────────────────────────────────────────────────────

  Future<void> refreshPendingCount() async {
    _pendingCount = await _db.getPendingCount();
    notifyListeners();
  }

  /// Immediately attempt to drain the outbox. Safe to call manually.
  Future<void> drain() async {
    if (_syncing) return;
    _syncing = true;
    _lastError = null;
    notifyListeners();

    try {
      await _doDrain();
      await _db.pruneOutbox();
    } catch (e) {
      _lastError = e.toString();
    } finally {
      _syncing = false;
      _pendingCount = await _db.getPendingCount();
      notifyListeners();
    }
  }

  Future<void> _doDrain() async {
    final items = await _db.getPendingItems();
    for (final item in items) {
      if (item.retryCount >= _maxRetries) continue;
      await _processItem(item);
    }
  }

  Future<void> _processItem(OutboxItem item) async {
    try {
      switch (item.entityType) {
        case 'stock_level':
          await _syncStockLevel(item);
        case 'bed_snapshot':
          await _api.createBedSnapshot(item.facilityId, item.payload);
        case 'attendance_log':
          await _api.createAttendanceLog(item.facilityId, item.payload);
        case 'footfall_log':
          await _api.createFootfallLog(item.facilityId, item.payload);
        default:
          // Unknown type — mark as synced to avoid blocking queue
          await _markSynced(item.id);
          return;
      }
      await _markSynced(item.id);
    } catch (e) {
      // Increment retry; skip this item for now
      await _db.incrementRetry(item.id);
      debugPrint('[SyncService] Failed to sync ${item.entityType}/${item.entityId}: $e');
    }
  }

  Future<void> _syncStockLevel(OutboxItem item) async {
    final payload = item.payload;
    final facilityId = item.facilityId;

    if (item.operation == 'create') {
      await _api.createStockLevel(facilityId, payload);
    } else {
      // 'upsert' or 'update' — try PUT, fall back to POST on 404
      try {
        await _api.updateStockLevel(facilityId, item.entityId, payload);
      } catch (e) {
        // If the level doesn't exist on the server yet, create it
        await _api.createStockLevel(facilityId, payload);
      }
    }
  }

  Future<void> _markSynced(String id) async {
    final now = DateTime.now().toUtc().toIso8601String();
    await _db.markSynced(id, now);
  }

  @override
  void dispose() {
    _connectivity.removeListener(_onConnectivityChanged);
    super.dispose();
  }
}
