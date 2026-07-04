/// Dart model mirroring the backend `footfall_logs` table.
class FootfallLog {
  final String id;
  final String facilityId;
  final String date; // ISO date string "YYYY-MM-DD"
  final int patientCount;
  final String? department;
  final bool isSimulated;
  final String basis;

  const FootfallLog({
    required this.id,
    required this.facilityId,
    required this.date,
    required this.patientCount,
    this.department,
    required this.isSimulated,
    required this.basis,
  });

  factory FootfallLog.fromMap(Map<String, dynamic> m) => FootfallLog(
        id: m['id'] as String,
        facilityId: m['facility_id'] as String,
        date: m['date'] as String,
        patientCount: (m['patient_count'] as num).toInt(),
        department: m['department'] as String?,
        isSimulated: (m['is_simulated'] == true || m['is_simulated'] == 1),
        basis: m['basis'] as String? ?? 'field app entry',
      );

  Map<String, dynamic> toMap() => {
        'id': id,
        'facility_id': facilityId,
        'date': date,
        'patient_count': patientCount,
        'department': department,
        'is_simulated': isSimulated ? 1 : 0,
        'basis': basis,
      };

  /// JSON payload for the backend API.
  Map<String, dynamic> toApiJson() => {
        'date': date,
        'patient_count': patientCount,
        if (department != null) 'department': department,
        'is_simulated': isSimulated,
        'basis': basis,
      };
}
