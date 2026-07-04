import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models/facility.dart';
import '../models/department.dart';
import '../models/staff.dart';
import '../models/inventory_item.dart';
import '../models/stock_level.dart';

/// Default base URL — points to localhost via Android emulator loopback.
/// Override via Settings screen → stored in SharedPreferences.
const String kDefaultBaseUrl = 'http://10.0.2.2:8000';
const String kPrefsBaseUrlKey = 'api_base_url';

/// Thin Dio wrapper around the Medico FastAPI backend.
///
/// Each method maps 1:1 to a backend REST endpoint.  Error handling is left to
/// the caller (SyncService / FacilitySyncService) so they can decide whether
/// to retry or discard.
class ApiService {
  ApiService._();
  static final ApiService instance = ApiService._();

  late Dio _dio;
  bool _initialized = false;

  Future<void> init() async {
    if (_initialized) return;
    final prefs = await SharedPreferences.getInstance();
    final base = prefs.getString(kPrefsBaseUrlKey) ?? kDefaultBaseUrl;
    _configure(base);
    _initialized = true;
  }

  void _configure(String baseUrl) {
    _dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 15),
      headers: {'Content-Type': 'application/json'},
    ));
  }

  /// Allow the settings screen to change the base URL at runtime.
  Future<void> updateBaseUrl(String url) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(kPrefsBaseUrlKey, url);
    _configure(url);
  }

  Future<String> getBaseUrl() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(kPrefsBaseUrlKey) ?? kDefaultBaseUrl;
  }

  // ── Facilities ─────────────────────────────────────────────────────────────

  Future<List<Facility>> fetchFacilities() async {
    final resp = await _dio.get('/facilities');
    return (resp.data as List).map((j) => Facility.fromMap(j as Map<String, dynamic>)).toList();
  }

  // ── Departments ────────────────────────────────────────────────────────────

  Future<List<Department>> fetchDepartments(String facilityId) async {
    final resp = await _dio.get('/facilities/$facilityId/departments');
    return (resp.data as List).map((j) => Department.fromMap(j as Map<String, dynamic>)).toList();
  }

  // ── Staff ──────────────────────────────────────────────────────────────────

  Future<List<Staff>> fetchStaff(String facilityId) async {
    final resp = await _dio.get('/facilities/$facilityId/staff');
    return (resp.data as List).map((j) => Staff.fromMap(j as Map<String, dynamic>)).toList();
  }

  // ── Inventory Items ────────────────────────────────────────────────────────

  Future<List<InventoryItem>> fetchInventoryItems() async {
    final resp = await _dio.get('/inventory-items');
    return (resp.data as List)
        .map((j) => InventoryItem.fromMap(j as Map<String, dynamic>))
        .toList();
  }

  // ── Stock Levels ───────────────────────────────────────────────────────────

  Future<List<StockLevel>> fetchStockLevels(String facilityId) async {
    final resp = await _dio.get('/facilities/$facilityId/stock-levels');
    return (resp.data as List).map((j) => StockLevel.fromMap(j as Map<String, dynamic>)).toList();
  }

  Future<void> createStockLevel(String facilityId, Map<String, dynamic> body) async {
    await _dio.post('/facilities/$facilityId/stock-levels', data: body);
  }

  Future<void> updateStockLevel(
      String facilityId, String levelId, Map<String, dynamic> body) async {
    await _dio.put('/facilities/$facilityId/stock-levels/$levelId', data: body);
  }

  // ── Bed Snapshots ──────────────────────────────────────────────────────────

  Future<void> createBedSnapshot(String facilityId, Map<String, dynamic> body) async {
    await _dio.post('/facilities/$facilityId/beds', data: body);
  }

  // ── Attendance ─────────────────────────────────────────────────────────────

  Future<void> createAttendanceLog(String facilityId, Map<String, dynamic> body) async {
    await _dio.post('/facilities/$facilityId/attendance', data: body);
  }

  // ── Footfall ───────────────────────────────────────────────────────────────

  Future<void> createFootfallLog(String facilityId, Map<String, dynamic> body) async {
    await _dio.post('/facilities/$facilityId/footfall', data: body);
  }
}
