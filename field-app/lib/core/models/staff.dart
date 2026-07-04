/// Dart model mirroring the backend `staff` table.
class Staff {
  final String id;
  final String facilityId;
  final String role;
  final bool sanctioned;
  final String name;
  final String createdAt;
  final String updatedAt;

  const Staff({
    required this.id,
    required this.facilityId,
    required this.role,
    required this.sanctioned,
    required this.name,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Staff.fromMap(Map<String, dynamic> m) => Staff(
        id: m['id'] as String,
        facilityId: m['facility_id'] as String,
        role: m['role'] as String,
        // SQLite stores booleans as 0/1
        sanctioned: (m['sanctioned'] == true || m['sanctioned'] == 1),
        name: m['name'] as String,
        createdAt: m['created_at'] as String? ?? DateTime.now().toIso8601String(),
        updatedAt: m['updated_at'] as String? ?? DateTime.now().toIso8601String(),
      );

  Map<String, dynamic> toMap() => {
        'id': id,
        'facility_id': facilityId,
        'role': role,
        'sanctioned': sanctioned ? 1 : 0,
        'name': name,
        'created_at': createdAt,
        'updated_at': updatedAt,
      };
}
