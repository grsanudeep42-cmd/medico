import 'package:path/path.dart';
import 'package:sqflite/sqflite.dart';

/// Singleton database helper for offline-first local storage.
class LocalDatabase {
  LocalDatabase._();
  static final LocalDatabase instance = LocalDatabase._();

  static Database? _db;

  Future<Database> get database async {
    _db ??= await _init();
    return _db!;
  }

  Future<Database> _init() async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, 'medico.db');

    return openDatabase(
      path,
      version: 1,
      onCreate: _onCreate,
      onUpgrade: _onUpgrade,
    );
  }

  Future<void> _onCreate(Database db, int version) async {
    await db.execute('''
      CREATE TABLE IF NOT EXISTS facilities (
        id          TEXT PRIMARY KEY,
        name        TEXT NOT NULL,
        type        TEXT NOT NULL,
        state       TEXT NOT NULL,
        address     TEXT,
        pincode     TEXT,
        phone       TEXT,
        active      INTEGER NOT NULL DEFAULT 1,
        synced      INTEGER NOT NULL DEFAULT 0,
        created_at  TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
      )
    ''');

    await db.execute('''
      CREATE TABLE IF NOT EXISTS sync_queue (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type TEXT NOT NULL,
        entity_id   TEXT NOT NULL,
        operation   TEXT NOT NULL,   -- 'create' | 'update' | 'delete'
        payload     TEXT NOT NULL,   -- JSON string
        created_at  TEXT NOT NULL DEFAULT (datetime('now'))
      )
    ''');
  }

  Future<void> _onUpgrade(Database db, int oldVersion, int newVersion) async {
    // Future migrations go here.
  }

  // ── Facility helpers ──────────────────────────────────────────────────────

  Future<int> upsertFacility(Map<String, dynamic> facility) async {
    final db = await database;
    return db.insert(
      'facilities',
      facility,
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<List<Map<String, dynamic>>> getAllFacilities({bool activeOnly = true}) async {
    final db = await database;
    return db.query(
      'facilities',
      where: activeOnly ? 'active = 1' : null,
      orderBy: 'name ASC',
    );
  }

  Future<Map<String, dynamic>?> getFacilityById(String id) async {
    final db = await database;
    final rows = await db.query('facilities', where: 'id = ?', whereArgs: [id]);
    return rows.isEmpty ? null : rows.first;
  }

  Future<int> deleteFacility(String id) async {
    final db = await database;
    return db.delete('facilities', where: 'id = ?', whereArgs: [id]);
  }

  // ── Sync queue helpers ───────────────────────────────────────────────────

  Future<int> enqueueSync({
    required String entityType,
    required String entityId,
    required String operation,
    required String payload,
  }) async {
    final db = await database;
    return db.insert('sync_queue', {
      'entity_type': entityType,
      'entity_id': entityId,
      'operation': operation,
      'payload': payload,
    });
  }

  Future<List<Map<String, dynamic>>> getPendingSyncItems() async {
    final db = await database;
    return db.query('sync_queue', orderBy: 'id ASC');
  }

  Future<int> deleteSyncItem(int id) async {
    final db = await database;
    return db.delete('sync_queue', where: 'id = ?', whereArgs: [id]);
  }

  Future<void> close() async {
    final db = _db;
    if (db != null) {
      await db.close();
      _db = null;
    }
  }
}
