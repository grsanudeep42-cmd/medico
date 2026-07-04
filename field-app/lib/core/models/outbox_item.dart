import 'dart:convert';

/// An entry in the local write-ahead outbox queue.
///
/// Every field write (stock, bed, attendance, footfall) creates one of these
/// before hitting the network. The [SyncService] drains pending items when
/// connectivity is restored.
class OutboxItem {
  final String id; // client-generated UUID
  final String entityType; // 'stock_level' | 'bed_snapshot' | 'attendance_log' | 'footfall_log'
  final String entityId; // UUID of the local entity row
  final String operation; // 'create' | 'upsert' | 'update'
  final Map<String, dynamic> payload; // full body to send to the API
  final String facilityId; // for URL construction
  final String createdAt; // ISO8601 UTC — used for last-write-wins ordering
  final String? syncedAt; // NULL until successfully acknowledged by server
  final int retryCount;

  const OutboxItem({
    required this.id,
    required this.entityType,
    required this.entityId,
    required this.operation,
    required this.payload,
    required this.facilityId,
    required this.createdAt,
    this.syncedAt,
    this.retryCount = 0,
  });

  factory OutboxItem.fromMap(Map<String, dynamic> m) => OutboxItem(
        id: m['id'] as String,
        entityType: m['entity_type'] as String,
        entityId: m['entity_id'] as String,
        operation: m['operation'] as String,
        payload: jsonDecode(m['payload_json'] as String) as Map<String, dynamic>,
        facilityId: m['facility_id'] as String,
        createdAt: m['created_at'] as String,
        syncedAt: m['synced_at'] as String?,
        retryCount: (m['retry_count'] as num?)?.toInt() ?? 0,
      );

  Map<String, dynamic> toMap() => {
        'id': id,
        'entity_type': entityType,
        'entity_id': entityId,
        'operation': operation,
        'payload_json': jsonEncode(payload),
        'facility_id': facilityId,
        'created_at': createdAt,
        'synced_at': syncedAt,
        'retry_count': retryCount,
      };

  OutboxItem markSynced() => OutboxItem(
        id: id,
        entityType: entityType,
        entityId: entityId,
        operation: operation,
        payload: payload,
        facilityId: facilityId,
        createdAt: createdAt,
        syncedAt: DateTime.now().toUtc().toIso8601String(),
        retryCount: retryCount,
      );

  OutboxItem incrementRetry() => OutboxItem(
        id: id,
        entityType: entityType,
        entityId: entityId,
        operation: operation,
        payload: payload,
        facilityId: facilityId,
        createdAt: createdAt,
        syncedAt: syncedAt,
        retryCount: retryCount + 1,
      );

  bool get isSynced => syncedAt != null;
}
