/// Dart model mirroring the backend `inventory_items` table.
class InventoryItem {
  final String id;
  final String name;
  final String category;
  final String unit;
  final String createdAt;
  final String updatedAt;

  const InventoryItem({
    required this.id,
    required this.name,
    required this.category,
    required this.unit,
    required this.createdAt,
    required this.updatedAt,
  });

  factory InventoryItem.fromMap(Map<String, dynamic> m) => InventoryItem(
        id: m['id'] as String,
        name: m['name'] as String,
        category: m['category'] as String,
        unit: m['unit'] as String,
        createdAt: m['created_at'] as String? ?? DateTime.now().toIso8601String(),
        updatedAt: m['updated_at'] as String? ?? DateTime.now().toIso8601String(),
      );

  Map<String, dynamic> toMap() => {
        'id': id,
        'name': name,
        'category': category,
        'unit': unit,
        'created_at': createdAt,
        'updated_at': updatedAt,
      };
}
