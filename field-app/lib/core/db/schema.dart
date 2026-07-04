/// SQLite DDL constants and schema version management.
///
/// Schema version history:
///   v1 — initial schema (all tables)
library;

const int kDbVersion = 1;
const String kDbName = 'medico_field.db';

/// All CREATE TABLE statements, in dependency order.
const List<String> kCreateStatements = [
  // ── Reference tables (populated by server sync) ─────────────────────────
  '''
  CREATE TABLE IF NOT EXISTS facilities (
    id TEXT PRIMARY KEY,
    facility_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    facility_type TEXT NOT NULL,
    tier TEXT NOT NULL,
    referral_parent_id TEXT,
    address TEXT NOT NULL,
    lat REAL NOT NULL,
    lng REAL NOT NULL,
    sanctioned_beds INTEGER NOT NULL DEFAULT 0,
    functional_beds_estimate INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
  )
  ''',
  '''
  CREATE TABLE IF NOT EXISTS departments (
    id TEXT PRIMARY KEY,
    facility_id TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (facility_id) REFERENCES facilities(id) ON DELETE CASCADE
  )
  ''',
  '''
  CREATE TABLE IF NOT EXISTS staff (
    id TEXT PRIMARY KEY,
    facility_id TEXT NOT NULL,
    role TEXT NOT NULL,
    sanctioned INTEGER NOT NULL DEFAULT 1,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (facility_id) REFERENCES facilities(id) ON DELETE CASCADE
  )
  ''',
  '''
  CREATE TABLE IF NOT EXISTS inventory_items (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
  )
  ''',

  // ── Operational tables (field data entry) ───────────────────────────────
  '''
  CREATE TABLE IF NOT EXISTS stock_levels (
    id TEXT PRIMARY KEY,
    facility_id TEXT NOT NULL,
    item_id TEXT NOT NULL,
    quantity REAL NOT NULL DEFAULT 0,
    reorder_threshold REAL NOT NULL DEFAULT 0,
    last_updated TEXT NOT NULL,
    FOREIGN KEY (facility_id) REFERENCES facilities(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES inventory_items(id) ON DELETE CASCADE
  )
  ''',
  '''
  CREATE TABLE IF NOT EXISTS beds (
    id TEXT PRIMARY KEY,
    facility_id TEXT NOT NULL,
    total_beds INTEGER NOT NULL DEFAULT 0,
    occupied_beds INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (facility_id) REFERENCES facilities(id) ON DELETE CASCADE
  )
  ''',
  '''
  CREATE TABLE IF NOT EXISTS attendance_logs (
    id TEXT PRIMARY KEY,
    staff_id TEXT NOT NULL,
    date TEXT NOT NULL,
    present INTEGER NOT NULL DEFAULT 0,
    is_simulated INTEGER NOT NULL DEFAULT 0,
    basis TEXT NOT NULL,
    FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE CASCADE
  )
  ''',
  '''
  CREATE TABLE IF NOT EXISTS footfall_logs (
    id TEXT PRIMARY KEY,
    facility_id TEXT NOT NULL,
    date TEXT NOT NULL,
    patient_count INTEGER NOT NULL,
    department TEXT,
    is_simulated INTEGER NOT NULL DEFAULT 0,
    basis TEXT NOT NULL,
    FOREIGN KEY (facility_id) REFERENCES facilities(id) ON DELETE CASCADE
  )
  ''',

  // ── Sync infrastructure ──────────────────────────────────────────────────
  '''
  CREATE TABLE IF NOT EXISTS outbox_queue (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    operation TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    facility_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    synced_at TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0
  )
  ''',
  '''
  CREATE TABLE IF NOT EXISTS sync_metadata (
    table_name TEXT PRIMARY KEY,
    last_synced_at TEXT NOT NULL
  )
  ''',
];

/// Index creation for performance.
const List<String> kIndexStatements = [
  'CREATE INDEX IF NOT EXISTS idx_departments_facility ON departments(facility_id)',
  'CREATE INDEX IF NOT EXISTS idx_staff_facility ON staff(facility_id)',
  'CREATE INDEX IF NOT EXISTS idx_stock_facility ON stock_levels(facility_id)',
  'CREATE INDEX IF NOT EXISTS idx_stock_item ON stock_levels(item_id)',
  'CREATE INDEX IF NOT EXISTS idx_beds_facility ON beds(facility_id)',
  'CREATE INDEX IF NOT EXISTS idx_attendance_staff ON attendance_logs(staff_id)',
  'CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance_logs(date)',
  'CREATE INDEX IF NOT EXISTS idx_footfall_facility ON footfall_logs(facility_id)',
  'CREATE INDEX IF NOT EXISTS idx_footfall_date ON footfall_logs(date)',
  'CREATE INDEX IF NOT EXISTS idx_outbox_synced ON outbox_queue(synced_at)',
  'CREATE INDEX IF NOT EXISTS idx_outbox_created ON outbox_queue(created_at)',
];
