/// Dart model mirroring the backend `facilities` table.
class Facility {
  final String id; // UUID string
  final String facilityId; // human-readable code, e.g. "MH-PHC-0042"
  final String name;
  final String facilityType; // PHC | CHC | tertiary_referral
  final String tier; // primary | community | apex
  final String? referralParentId;
  final String address;
  final double lat;
  final double lng;
  final int sanctionedBeds;
  final int functionalBedsEstimate;
  final String createdAt;
  final String updatedAt;

  const Facility({
    required this.id,
    required this.facilityId,
    required this.name,
    required this.facilityType,
    required this.tier,
    this.referralParentId,
    required this.address,
    required this.lat,
    required this.lng,
    required this.sanctionedBeds,
    required this.functionalBedsEstimate,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Facility.fromMap(Map<String, dynamic> m) => Facility(
        id: m['id'] as String,
        facilityId: m['facility_id'] as String,
        name: m['name'] as String,
        facilityType: m['facility_type'] as String,
        tier: m['tier'] as String,
        referralParentId: m['referral_parent_id'] as String?,
        address: m['address'] as String,
        lat: (m['lat'] as num).toDouble(),
        lng: (m['lng'] as num).toDouble(),
        sanctionedBeds: (m['sanctioned_beds'] as num).toInt(),
        functionalBedsEstimate: (m['functional_beds_estimate'] as num).toInt(),
        createdAt: m['created_at'] as String? ?? DateTime.now().toIso8601String(),
        updatedAt: m['updated_at'] as String? ?? DateTime.now().toIso8601String(),
      );

  Map<String, dynamic> toMap() => {
        'id': id,
        'facility_id': facilityId,
        'name': name,
        'facility_type': facilityType,
        'tier': tier,
        'referral_parent_id': referralParentId,
        'address': address,
        'lat': lat,
        'lng': lng,
        'sanctioned_beds': sanctionedBeds,
        'functional_beds_estimate': functionalBedsEstimate,
        'created_at': createdAt,
        'updated_at': updatedAt,
      };
}
