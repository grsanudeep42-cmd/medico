/// Dart model mirroring the backend `beds` table (point-in-time snapshots).
class BedSnapshot {
  final String id;
  final String facilityId;
  final int totalBeds;
  final int occupiedBeds;
  final String updatedAt;

  const BedSnapshot({
    required this.id,
    required this.facilityId,
    required this.totalBeds,
    required this.occupiedBeds,
    required this.updatedAt,
  });

  factory BedSnapshot.fromMap(Map<String, dynamic> m) => BedSnapshot(
        id: m['id'] as String,
        facilityId: m['facility_id'] as String,
        totalBeds: (m['total_beds'] as num).toInt(),
        occupiedBeds: (m['occupied_beds'] as num).toInt(),
        updatedAt: m['updated_at'] as String,
      );

  Map<String, dynamic> toMap() => {
        'id': id,
        'facility_id': facilityId,
        'total_beds': totalBeds,
        'occupied_beds': occupiedBeds,
        'updated_at': updatedAt,
      };

  double get occupancyRate => totalBeds > 0 ? occupiedBeds / totalBeds : 0.0;
}
