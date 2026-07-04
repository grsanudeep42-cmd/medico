import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/services/connectivity_service.dart';
import '../../core/services/sync_service.dart';
import '../theme.dart';

/// Compact chip shown in AppBars and screens displaying sync + connectivity state.
class SyncStatusChip extends StatelessWidget {
  const SyncStatusChip({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer2<ConnectivityService, SyncService>(
      builder: (context, conn, sync, _) {
        final online = conn.isOnline;
        final syncing = sync.isSyncing;
        final pending = sync.pendingCount;

        Color color;
        IconData icon;
        String label;

        if (syncing) {
          color = kColorWarning;
          icon = Icons.sync;
          label = 'Syncing…';
        } else if (!online) {
          color = kColorDanger;
          icon = Icons.wifi_off_rounded;
          label = pending > 0 ? '$pending pending' : 'Offline';
        } else if (pending > 0) {
          color = kColorWarning;
          icon = Icons.upload_rounded;
          label = '$pending pending';
        } else {
          color = kColorSuccess;
          icon = Icons.cloud_done_rounded;
          label = 'Synced';
        }

        return AnimatedContainer(
          duration: const Duration(milliseconds: 300),
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
          decoration: BoxDecoration(
            color: color.withAlpha(26),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: color.withAlpha(77)),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              syncing
                  ? SizedBox(
                      width: 12,
                      height: 12,
                      child: CircularProgressIndicator(
                        strokeWidth: 1.5,
                        color: color,
                      ),
                    )
                  : Icon(icon, size: 12, color: color),
              const SizedBox(width: 5),
              Text(
                label,
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  color: color,
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
