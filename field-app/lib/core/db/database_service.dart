import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';

import '../models/facility.dart';
import '../models/department.dart';
import '../models/staff.dart';
import '../models/inventory_item.dart';
import '../models/stock_level.dart';
import '../models/bed_snapshot.dart';
import '../models/attendance_log.dart';
import '../models/footfall_log.dart';
import '../models/outbox_item.dart';
import 'schema.dart';

/// Singleton service that owns the sqflite [Database] instance.
///
/// Call [DatabaseService.init()] once at app startup before using any
/// other method. All operations are async and thread-safe via sqflite's
/// internal serialization.
class DatabaseService {
  DatabaseService._();
  static final DatabaseService instance = DatabaseService._();

  Database? _db;

  Database get db {
    assert(_db != null, 'DatabaseService.init() must be called first');
    return _db!;
  }

  // ── Initialization ─────────────────────────────────────────────────────────

  Future<void> init() async {
    if (_db != null) return;
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, kDbName);

    _db = await openDatabase(
      path,
      version: kDbVersion,
      onConfigure: (db) async => db.execute('PRAGMA foreign_keys = ON'),
      onCreate: _onCreate,
      onUpgrade: _onUpgrade,
    );
  }

  Future<void> _onCreate(Database db, int version) async {
    final batch = db.batch();
    for (final stmt in kCreateStatements) {
      batch.execute(stmt);
    }
    for (final idx in kIndexStatements) {
      batch.execute(idx);
    }
    await batch.commit(noResult: true);
  }

  Future<void> _onUpgrade(Database db, int oldVersion, int newVersion) async {
    // Future migrations go here, keyed by old → new version.
    // For now there is only v1, so nothing to do.
  }

  // ── Facilities ─────────────────────────────────────────────────────────────

  Future<List<Facility>> getFacilities() async {
    final rows = await db.query('facilities', orderBy: 'name ASC');
    return rows.map(Facility.fromMap).toList();
  }

  Future<Facility?> getFacility(String id) async {
    final rows = await db.query('facilities', where: 'id = ?', whereArgs: [id]);
    return rows.isEmpty ? null : Facility.fromMap(rows.first);
  }

  Future<void> upsertFacility(Facility f) async {
    await db.insert('facilities', f.toMap(), conflictAlgorithm: ConflictAlgorithm.replace);
  }

  Future<void> upsertFacilities(List<Facility> facilities) async {
    final batch = db.batch();
    for (final f in facilities) {
      batch.insert('facilities', f.toMap(), conflictAlgorithm: ConflictAlgorithm.replace);
    }
    await batch.commit(noResult: true);
  }

  // ── Departments ────────────────────────────────────────────────────────────

  Future<List<Department>> getDepartments(String facilityId) async {
    final rows = await db.query(
      'departments',
      where: 'facility_id = ?',
      whereArgs: [facilityId],
      orderBy: 'name ASC',
    );
    return rows.map(Department.fromMap).toList();
  }

  Future<void> upsertDepartments(List<Department> items) async {
    final batch = db.batch();
    for (final d in items) {
      batch.insert('departments', d.toMap(), conflictAlgorithm: ConflictAlgorithm.replace);
    }
    await batch.commit(noResult: true);
  }

  // ── Staff ──────────────────────────────────────────────────────────────────

  Future<List<Staff>> getStaff(String facilityId) async {
    final rows = await db.query(
      'staff',
      where: 'facility_id = ?',
      whereArgs: [facilityId],
      orderBy: 'name ASC',
    );
    return rows.map(Staff.fromMap).toList();
  }

  Future<void> upsertStaff(List<Staff> members) async {
    final batch = db.batch();
    for (final s in members) {
      batch.insert('staff', s.toMap(), conflictAlgorithm: ConflictAlgorithm.replace);
    }
    await batch.commit(noResult: true);
  }

  // ── Inventory Items ────────────────────────────────────────────────────────

  Future<List<InventoryItem>> getInventoryItems() async {
    final rows = await db.query('inventory_items', orderBy: 'category ASC, name ASC');
    return rows.map(InventoryItem.fromMap).toList();
  }

  Future<void> upsertInventoryItems(List<InventoryItem> items) async {
    final batch = db.batch();
    for (final item in items) {
      batch.insert('inventory_items', item.toMap(), conflictAlgorithm: ConflictAlgorithm.replace);
    }
    await batch.commit(noResult: true);
  }

  // ── Stock Levels ───────────────────────────────────────────────────────────

  Future<List<StockLevel>> getStockLevels(String facilityId) async {
    final rows = await db.query(
      'stock_levels',
      where: 'facility_id = ?',
      whereArgs: [facilityId],
    );
    return rows.map(StockLevel.fromMap).toList();
  }

  Future<StockLevel?> getStockLevelByItem(String facilityId, String itemId) async {
    final rows = await db.query(
      'stock_levels',
      where: 'facility_id = ? AND item_id = ?',
      whereArgs: [facilityId, itemId],
    );
    return rows.isEmpty ? null : StockLevel.fromMap(rows.first);
  }

  Future<void> upsertStockLevel(StockLevel sl) async {
    await db.insert('stock_levels', sl.toMap(), conflictAlgorithm: ConflictAlgorithm.replace);
  }

  Future<void> upsertStockLevels(List<StockLevel> levels) async {
    final batch = db.batch();
    for (final sl in levels) {
      batch.insert('stock_levels', sl.toMap(), conflictAlgorithm: ConflictAlgorithm.replace);
    }
    await batch.commit(noResult: true);
  }

  // ── Bed Snapshots ──────────────────────────────────────────────────────────

  Future<List<BedSnapshot>> getBedSnapshots(String facilityId, {int limit = 20}) async {
    final rows = await db.query(
      'beds',
      where: 'facility_id = ?',
      whereArgs: [facilityId],
      orderBy: 'updated_at DESC',
      limit: limit,
    );
    return rows.map(BedSnapshot.fromMap).toList();
  }

  Future<BedSnapshot?> getLatestBedSnapshot(String facilityId) async {
    final rows = await db.query(
      'beds',
      where: 'facility_id = ?',
      whereArgs: [facilityId],
      orderBy: 'updated_at DESC',
      limit: 1,
    );
    return rows.isEmpty ? null : BedSnapshot.fromMap(rows.first);
  }

  Future<void> insertBedSnapshot(BedSnapshot snap) async {
    await db.insert('beds', snap.toMap(), conflictAlgorithm: ConflictAlgorithm.replace);
  }

  // ── Attendance Logs ────────────────────────────────────────────────────────

  Future<List<AttendanceLog>> getAttendanceLogs(String staffId, String date) async {
    final rows = await db.query(
      'attendance_logs',
      where: 'staff_id = ? AND date = ?',
      whereArgs: [staffId, date],
    );
    return rows.map(AttendanceLog.fromMap).toList();
  }

  Future<Map<String, bool>> getAttendanceForDate(List<String> staffIds, String date) async {
    if (staffIds.isEmpty) return {};
    final placeholders = staffIds.map((_) => '?').join(', ');
    final rows = await db.rawQuery(
      'SELECT staff_id, present FROM attendance_logs WHERE date = ? AND staff_id IN ($placeholders)',
      [date, ...staffIds],
    );
    return {for (final r in rows) r['staff_id'] as String: (r['present'] == 1)};
  }

  Future<void> insertAttendanceLog(AttendanceLog log) async {
    await db.insert('attendance_logs', log.toMap(), conflictAlgorithm: ConflictAlgorithm.replace);
  }

  Future<void> insertAttendanceLogs(List<AttendanceLog> logs) async {
    final batch = db.batch();
    for (final log in logs) {
      batch.insert('attendance_logs', log.toMap(), conflictAlgorithm: ConflictAlgorithm.replace);
    }
    await batch.commit(noResult: true);
  }

  // ── Footfall Logs ──────────────────────────────────────────────────────────

  Future<List<FootfallLog>> getFootfallLogs(String facilityId, {int limit = 30}) async {
    final rows = await db.query(
      'footfall_logs',
      where: 'facility_id = ?',
      whereArgs: [facilityId],
      orderBy: 'date DESC',
      limit: limit,
    );
    return rows.map(FootfallLog.fromMap).toList();
  }

  Future<void> insertFootfallLog(FootfallLog log) async {
    await db.insert('footfall_logs', log.toMap(), conflictAlgorithm: ConflictAlgorithm.replace);
  }

  // ── Outbox Queue ───────────────────────────────────────────────────────────

  Future<void> enqueue(OutboxItem item) async {
    await db.insert('outbox_queue', item.toMap(), conflictAlgorithm: ConflictAlgorithm.replace);
  }

  /// Returns all unsynced items, oldest first (last-write-wins ordering).
  Future<List<OutboxItem>> getPendingItems() async {
    final rows = await db.query(
      'outbox_queue',
      where: 'synced_at IS NULL',
      orderBy: 'created_at ASC',
    );
    return rows.map(OutboxItem.fromMap).toList();
  }

  Future<int> getPendingCount() async {
    final result = await db.rawQuery(
      'SELECT COUNT(*) as cnt FROM outbox_queue WHERE synced_at IS NULL',
    );
    return (result.first['cnt'] as int?) ?? 0;
  }

  Future<void> markSynced(String id, String syncedAt) async {
    await db.update(
      'outbox_queue',
      {'synced_at': syncedAt},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<void> incrementRetry(String id) async {
    await db.rawUpdate(
      'UPDATE outbox_queue SET retry_count = retry_count + 1 WHERE id = ?',
      [id],
    );
  }

  /// Prune synced outbox rows older than [days] days.
  Future<void> pruneOutbox({int days = 7}) async {
    final cutoff = DateTime.now().toUtc().subtract(Duration(days: days)).toIso8601String();
    await db.delete(
      'outbox_queue',
      where: 'synced_at IS NOT NULL AND synced_at < ?',
      whereArgs: [cutoff],
    );
  }

  // ── Sync Metadata ──────────────────────────────────────────────────────────

  Future<String?> getLastSyncedAt(String tableName) async {
    final rows = await db.query(
      'sync_metadata',
      where: 'table_name = ?',
      whereArgs: [tableName],
    );
    return rows.isEmpty ? null : rows.first['last_synced_at'] as String;
  }

  Future<void> setLastSyncedAt(String tableName, String iso8601) async {
    await db.insert(
      'sync_metadata',
      {'table_name': tableName, 'last_synced_at': iso8601},
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  // ── Utility ────────────────────────────────────────────────────────────────

  Future<void> close() async {
    await _db?.close();
    _db = null;
  }
}
