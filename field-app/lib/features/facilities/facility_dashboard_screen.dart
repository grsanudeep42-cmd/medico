import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/models/facility.dart';
import '../../core/services/facility_sync_service.dart';
import '../../shared/theme.dart';
import '../../shared/widgets/sync_status_chip.dart';
import '../stock/stock_count_screen.dart';
import '../beds/bed_status_screen.dart';
import '../attendance/attendance_screen.dart';
import '../footfall/footfall_screen.dart';

/// Dashboard for a single facility showing 4 data-entry action cards.
class FacilityDashboardScreen extends StatefulWidget {
  const FacilityDashboardScreen({super.key, required this.facility});

  final Facility facility;

  @override
  State<FacilityDashboardScreen> createState() => _FacilityDashboardScreenState();
}

class _FacilityDashboardScreenState extends State<FacilityDashboardScreen> {
  @override
  void initState() {
    super.initState();
    // Kick off per-facility sync (staff, departments, stock levels)
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<FacilitySyncService>().syncFacility(widget.facility.id);
    });
  }

  Facility get f => widget.facility;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(f.name, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
            Text(
              '${f.facilityType} · ${f.facilityId}',
              style: const TextStyle(fontSize: 12, color: kColorTextMuted),
            ),
          ],
        ),
        actions: const [SyncStatusChip(), SizedBox(width: 12)],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Facility info banner
            _InfoBanner(facility: f),
            const SizedBox(height: 24),
            const Text(
              'Data Entry',
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: kColorTextMuted,
                letterSpacing: 1,
              ),
            ),
            const SizedBox(height: 12),
            _ActionGrid(facility: f),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }
}

// ── Info banner ──────────────────────────────────────────────────────────────

class _InfoBanner extends StatelessWidget {
  const _InfoBanner({required this.facility});
  final Facility facility;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: kColorCard,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: kColorBorder),
      ),
      child: Column(
        children: [
          Row(
            children: [
              const Icon(Icons.location_on_rounded, size: 16, color: kColorAccent),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  facility.address,
                  style: const TextStyle(fontSize: 13, color: kColorTextSecondary),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          const Divider(),
          const SizedBox(height: 10),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _Stat(label: 'Sanctioned Beds', value: facility.sanctionedBeds.toString()),
              _Stat(label: 'Functional Est.', value: facility.functionalBedsEstimate.toString()),
              _Stat(label: 'Tier', value: facility.tier),
            ],
          ),
        ],
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  const _Stat({required this.label, required this.value});
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          value,
          style: const TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.w800,
            color: kColorTextPrimary,
          ),
        ),
        Text(label, style: const TextStyle(fontSize: 11, color: kColorTextMuted)),
      ],
    );
  }
}

// ── Action grid ──────────────────────────────────────────────────────────────

class _ActionGrid extends StatelessWidget {
  const _ActionGrid({required this.facility});
  final Facility facility;

  @override
  Widget build(BuildContext context) {
    final items = [
      _ActionItem(
        icon: Icons.inventory_2_rounded,
        label: 'Stock Count',
        subtitle: 'Update inventory levels',
        color: kColorAccent,
        onTap: () => Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => StockCountScreen(facility: facility)),
        ),
      ),
      _ActionItem(
        icon: Icons.bed_rounded,
        label: 'Bed Status',
        subtitle: 'Log occupancy snapshot',
        color: const Color(0xFF6C63FF),
        onTap: () => Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => BedStatusScreen(facility: facility)),
        ),
      ),
      _ActionItem(
        icon: Icons.badge_rounded,
        label: 'Attendance',
        subtitle: 'Staff check-in',
        color: kColorWarning,
        onTap: () => Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => AttendanceScreen(facility: facility)),
        ),
      ),
      _ActionItem(
        icon: Icons.people_alt_rounded,
        label: 'Footfall',
        subtitle: 'Patient count log',
        color: kColorDanger,
        onTap: () => Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => FootfallScreen(facility: facility)),
        ),
      ),
    ];

    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisSpacing: 12,
      mainAxisSpacing: 12,
      childAspectRatio: 1.05,
      children: items.map((i) => _ActionCard(item: i)).toList(),
    );
  }
}

class _ActionItem {
  _ActionItem({
    required this.icon,
    required this.label,
    required this.subtitle,
    required this.color,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final String subtitle;
  final Color color;
  final VoidCallback onTap;
}

class _ActionCard extends StatelessWidget {
  const _ActionCard({required this.item});
  final _ActionItem item;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: item.onTap,
        borderRadius: BorderRadius.circular(16),
        splashColor: item.color.withAlpha(40),
        child: Container(
          decoration: BoxDecoration(
            color: kColorCard,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: kColorBorder),
          ),
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: item.color.withAlpha(25),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(item.icon, color: item.color, size: 24),
              ),
              const Spacer(),
              Text(
                item.label,
                style: const TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w700,
                  color: kColorTextPrimary,
                ),
              ),
              const SizedBox(height: 3),
              Text(
                item.subtitle,
                style: const TextStyle(fontSize: 11, color: kColorTextMuted),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
