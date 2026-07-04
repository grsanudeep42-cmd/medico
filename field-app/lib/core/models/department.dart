/// Dart model mirroring the backend `departments` table.
class Department {
  final String id;
  final String facilityId;
  final String name;
  final String createdAt;
  final String updatedAt;

  const Department({
    required this.id,
    required this.facilityId,
    required this.name,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Department.fromMap(Map<String, dynamic> m) => Department(
        id: m['id'] as String,
        facilityId: m['facility_id'] as String,
        name: m['name'] as String,
        createdAt: m['created_at'] as String? ?? DateTime.now().toIso8601String(),
        updatedAt: m['updated_at'] as String? ?? DateTime.now().toIso8601String(),
      );

  Map<String, dynamic> toMap() => {
        'id': id,
        'facility_id': facilityId,
        'name': name,
        'created_at': createdAt,
        'updated_at': updatedAt,
      };
}
