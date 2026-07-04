import 'package:flutter/foundation.dart';

import '../db/database_service.dart';
import '../services/api_service.dart';

/// Pulls reference and operational data from the server and upserts it
/// into the local SQLite database.
///
/// Called on first launch and on manual pull-to-refresh.
class FacilitySyncService extends ChangeNotifier {
  FacilitySyncService({required DatabaseService db, required ApiService api})
      : _db = db,
        _api = api;

  final DatabaseService _db;
  final ApiService _api;

  bool _loading = false;
  bool get isLoading => _loading;

  String? _error;
  String? get error => _error;

  String? _lastSyncedAt;
  String? get lastSyncedAt => _lastSyncedAt;

  // ── Public API ─────────────────────────────────────────────────────────────

  /// Sync all reference tables for all facilities the server knows about.
  Future<void> syncAll() async {
    if (_loading) return;
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      await _syncFacilities();
      await _syncInventoryItems();
      _lastSyncedAt = DateTime.now().toIso8601String();
      await _db.setLastSyncedAt('facilities', _lastSyncedAt!);
    } catch (e) {
      _error = 'Sync failed: $e';
      debugPrint('[FacilitySyncService] $e');
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  /// Sync per-facility reference data (staff, departments, stock levels).
  Future<void> syncFacility(String facilityId) async {
    if (_loading) return;
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final staff = await _api.fetchStaff(facilityId);
      await _db.upsertStaff(staff);

      final departments = await _api.fetchDepartments(facilityId);
      await _db.upsertDepartments(departments);

      final stockLevels = await _api.fetchStockLevels(facilityId);
      await _db.upsertStockLevels(stockLevels);

      await _db.setLastSyncedAt('staff_$facilityId', DateTime.now().toIso8601String());
    } catch (e) {
      _error = 'Facility sync failed: $e';
      debugPrint('[FacilitySyncService] syncFacility $facilityId: $e');
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  // ── Private helpers ────────────────────────────────────────────────────────

  Future<void> _syncFacilities() async {
    final facilities = await _api.fetchFacilities();
    await _db.upsertFacilities(facilities);
  }

  Future<void> _syncInventoryItems() async {
    final items = await _api.fetchInventoryItems();
    await _db.upsertInventoryItems(items);
  }
}
