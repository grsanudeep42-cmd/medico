/// Typed extraction results from the Whisper → LLM voice pipeline.
///
/// Each screen has its own subclass matching its data-entry domain.
/// [ExtractionError] is returned when parsing fails.
library;

// ── Base ──────────────────────────────────────────────────────────────────────

sealed class ExtractionResult {
  const ExtractionResult();
}

// ── Per-screen results ────────────────────────────────────────────────────────

/// Stock screen: a single item quantity update.
///
/// [action] is one of "set" | "add" | "remove".
class StockExtraction extends ExtractionResult {
  const StockExtraction({
    required this.itemName,
    required this.quantity,
    required this.unit,
    required this.action,
  });

  final String itemName;
  final double quantity;
  final String unit; // may be empty if not spoken
  final String action; // "set" | "add" | "remove"

  factory StockExtraction.fromJson(Map<String, dynamic> j) => StockExtraction(
        itemName: (j['item_name'] as String? ?? '').trim(),
        quantity: (j['quantity'] as num? ?? 0).toDouble(),
        unit: (j['unit'] as String? ?? '').trim(),
        action: (j['action'] as String? ?? 'set').trim(),
      );

  @override
  String toString() =>
      'StockExtraction(item: $itemName, qty: $quantity $unit, action: $action)';
}

/// Beds screen: occupancy snapshot fields.
class BedExtraction extends ExtractionResult {
  const BedExtraction({this.totalBeds, this.occupiedBeds});

  final int? totalBeds;
  final int? occupiedBeds;

  factory BedExtraction.fromJson(Map<String, dynamic> j) => BedExtraction(
        totalBeds: (j['total_beds'] as num?)?.toInt(),
        occupiedBeds: (j['occupied_beds'] as num?)?.toInt(),
      );

  @override
  String toString() =>
      'BedExtraction(total: $totalBeds, occupied: $occupiedBeds)';
}

/// Attendance screen: list of staff names and their status.
class AttendanceExtraction extends ExtractionResult {
  const AttendanceExtraction({required this.names, required this.status});

  final List<String> names; // as spoken — caller fuzzy-matches against staff list
  final String status; // "present" | "absent"

  factory AttendanceExtraction.fromJson(Map<String, dynamic> j) =>
      AttendanceExtraction(
        names: List<String>.from(
          (j['names'] as List<dynamic>? ?? []).map((e) => e.toString().trim()),
        ),
        status: (j['status'] as String? ?? 'absent').trim(),
      );

  @override
  String toString() =>
      'AttendanceExtraction(names: $names, status: $status)';
}

/// Footfall screen: patient count and optional department.
class FootfallExtraction extends ExtractionResult {
  const FootfallExtraction({required this.count, this.department});

  final int count;
  final String? department;

  factory FootfallExtraction.fromJson(Map<String, dynamic> j) =>
      FootfallExtraction(
        count: (j['count'] as num? ?? 0).toInt(),
        department: (j['department'] as String?)?.trim().isEmpty == true
            ? null
            : (j['department'] as String?)?.trim(),
      );

  @override
  String toString() =>
      'FootfallExtraction(count: $count, dept: $department)';
}

/// Returned when transcription or LLM parsing fails.
class ExtractionError extends ExtractionResult {
  const ExtractionError(this.message);
  final String message;

  @override
  String toString() => 'ExtractionError: $message';
}
