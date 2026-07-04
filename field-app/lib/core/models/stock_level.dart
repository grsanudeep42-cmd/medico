/// Dart model mirroring the backend `stock_levels` table.
class StockLevel {
  final String id;
  final String facilityId;
  final String itemId;
  final double quantity;
  final double reorderThreshold;
  final String lastUpdated;

  const StockLevel({
    required this.id,
    required this.facilityId,
    required this.itemId,
    required this.quantity,
    required this.reorderThreshold,
    required this.lastUpdated,
  });

  factory StockLevel.fromMap(Map<String, dynamic> m) => StockLevel(
        id: m['id'] as String,
        facilityId: m['facility_id'] as String,
        itemId: m['item_id'] as String,
        quantity: (m['quantity'] as num).toDouble(),
        reorderThreshold: (m['reorder_threshold'] as num).toDouble(),
        lastUpdated: m['last_updated'] as String,
      );

  Map<String, dynamic> toMap() => {
        'id': id,
        'facility_id': facilityId,
        'item_id': itemId,
        'quantity': quantity,
        'reorder_threshold': reorderThreshold,
        'last_updated': lastUpdated,
      };

  StockLevel copyWith({double? quantity, double? reorderThreshold, String? lastUpdated}) =>
      StockLevel(
        id: id,
        facilityId: facilityId,
        itemId: itemId,
        quantity: quantity ?? this.quantity,
        reorderThreshold: reorderThreshold ?? this.reorderThreshold,
        lastUpdated: lastUpdated ?? this.lastUpdated,
      );
}
