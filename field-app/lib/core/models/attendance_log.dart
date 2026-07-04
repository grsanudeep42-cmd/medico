/// Dart model mirroring the backend `attendance_logs` table.
class AttendanceLog {
  final String id;
  final String staffId;
  final String date; // ISO date string "YYYY-MM-DD"
  final bool present;
  final bool isSimulated;
  final String basis;

  const AttendanceLog({
    required this.id,
    required this.staffId,
    required this.date,
    required this.present,
    required this.isSimulated,
    required this.basis,
  });

  factory AttendanceLog.fromMap(Map<String, dynamic> m) => AttendanceLog(
        id: m['id'] as String,
        staffId: m['staff_id'] as String,
        date: m['date'] as String,
        present: (m['present'] == true || m['present'] == 1),
        isSimulated: (m['is_simulated'] == true || m['is_simulated'] == 1),
        basis: m['basis'] as String? ?? 'field app entry',
      );

  Map<String, dynamic> toMap() => {
        'id': id,
        'staff_id': staffId,
        'date': date,
        'present': present ? 1 : 0,
        'is_simulated': isSimulated ? 1 : 0,
        'basis': basis,
      };

  /// JSON payload for the backend API (uses bool, not int).
  Map<String, dynamic> toApiJson() => {
        'staff_id': staffId,
        'date': date,
        'present': present,
        'is_simulated': isSimulated,
        'basis': basis,
      };
}
