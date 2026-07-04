import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/db/database_service.dart';
import '../../core/models/facility.dart';
import '../../core/services/facility_sync_service.dart';
import '../../shared/theme.dart';
import '../../shared/widgets/empty_state_widget.dart';
import '../../shared/widgets/sync_status_chip.dart';
import '../settings/settings_screen.dart';
import 'facility_dashboard_screen.dart';

/// Entry screen: shows all locally-known facilities.
///
/// On first launch with no synced data this screen shows a clear empty state —
/// no placeholder or sample records are ever inserted.
class FacilityHomeScreen extends StatefulWidget {
  const FacilityHomeScreen({super.key});

  @override
  State<FacilityHomeScreen> createState() => _FacilityHomeScreenState();
}

class _FacilityHomeScreenState extends State<FacilityHomeScreen> {
  List<Facility> _facilities = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadFacilities();
  }

  Future<void> _loadFacilities() async {
    setState(() => _loading = true);
    final db = DatabaseService.instance;
    final facilities = await db.getFacilities();
    if (mounted) {
      setState(() {
        _facilities = facilities;
        _loading = false;
      });
    }
  }

  Future<void> _onRefresh() async {
    final syncService = context.read<FacilitySyncService>();
    await syncService.syncAll();
    await _loadFacilities();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              width: 28,
              height: 28,
              decoration: BoxDecoration(
                color: kColorAccent,
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(Icons.local_hospital_rounded, size: 16, color: kColorBackground),
            ),
            const SizedBox(width: 10),
            const Text('Medico Field'),
          ],
        ),
        actions: [
          const SyncStatusChip(),
          const SizedBox(width: 8),
          Consumer<FacilitySyncService>(
            builder: (context2, svc, child2) => svc.isLoading
                ? const Padding(
                    padding: EdgeInsets.symmetric(horizontal: 16),
                    child: SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2, color: kColorAccent),
                    ),
                  )
                : IconButton(
                    icon: const Icon(Icons.refresh_rounded),
                    tooltip: 'Sync from server',
                    onPressed: _onRefresh,
                  ),
          ),
          IconButton(
            icon: const Icon(Icons.settings_rounded),
            tooltip: 'Settings',
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const SettingsScreen()),
            ),
          ),
        ],
      ),
      body: RefreshIndicator(
        color: kColorAccent,
        backgroundColor: kColorCard,
        onRefresh: _onRefresh,
        child: _loading
            ? const Center(child: CircularProgressIndicator(color: kColorAccent))
            : _facilities.isEmpty
                ? ListView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    children: [
                      SizedBox(height: MediaQuery.of(context).size.height * 0.2),
                      EmptyStateWidget(
                        icon: Icons.location_city_rounded,
                        title: 'No Facilities Loaded',
                        message:
                            'Pull down to sync from the server, or connect to a network.\n'
                            'No sample data is shown until real facilities are loaded.',
                        actionLabel: 'Sync Now',
                        onAction: _onRefresh,
                      ),
                    ],
                  )
                : ListView.builder(
                    physics: const AlwaysScrollableScrollPhysics(),
                    padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
                    itemCount: _facilities.length,
                    itemBuilder: (context, i) => _FacilityCard(
                      facility: _facilities[i],
                      onTap: () => Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => FacilityDashboardScreen(facility: _facilities[i]),
                        ),
                      ).then((_) => _loadFacilities()),
                    ),
                  ),
      ),
    );
  }
}

class _FacilityCard extends StatelessWidget {
  const _FacilityCard({required this.facility, required this.onTap});

  final Facility facility;
  final VoidCallback onTap;

  Color _tierColor() {
    switch (facility.tier) {
      case 'apex':
        return kColorDanger;
      case 'community':
        return kColorWarning;
      default:
        return kColorAccent;
    }
  }

  @override
  Widget build(BuildContext context) {
    final tier = _tierColor();
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(16),
          child: Container(
            decoration: BoxDecoration(
              color: kColorCard,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: kColorBorder),
            ),
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    color: tier.withAlpha(25),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(Icons.local_hospital_rounded, color: tier, size: 22),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        facility.name,
                        style: const TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w700,
                          color: kColorTextPrimary,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          _Badge(label: facility.facilityType, color: tier),
                          const SizedBox(width: 6),
                          _Badge(label: facility.facilityId, color: kColorTextMuted),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Text(
                        facility.address,
                        style: const TextStyle(fontSize: 12, color: kColorTextMuted),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
                const Icon(Icons.chevron_right_rounded, color: kColorTextMuted),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _Badge extends StatelessWidget {
  const _Badge({required this.label, required this.color});
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: color.withAlpha(20),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: color.withAlpha(60)),
      ),
      child: Text(
        label,
        style: TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: color),
      ),
    );
  }
}
