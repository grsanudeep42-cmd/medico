import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'core/db/database_service.dart';
import 'core/services/api_service.dart';
import 'core/services/connectivity_service.dart';
import 'core/services/facility_sync_service.dart';
import 'core/services/sync_service.dart';
import 'features/facilities/facility_home_screen.dart';
import 'shared/theme.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Bootstrap singletons before the widget tree is built
  await DatabaseService.instance.init();
  await ApiService.instance.init();

  runApp(const MedicoFieldApp());
}

class MedicoFieldApp extends StatelessWidget {
  const MedicoFieldApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        // ConnectivityService must be first — others depend on it
        ChangeNotifierProvider(create: (_) => ConnectivityService()),

        // ApiService as plain provider (singleton, already initialised)
        Provider<ApiService>.value(value: ApiService.instance),

        // SyncService wires ConnectivityService + DatabaseService + ApiService
        ChangeNotifierProxyProvider<ConnectivityService, SyncService>(
          create: (ctx) => SyncService(
            connectivity: ctx.read<ConnectivityService>(),
            db: DatabaseService.instance,
            api: ApiService.instance,
          ),
          update: (ctx, conn, prev) => prev!,
        ),

        // FacilitySyncService for pulling reference data
        ChangeNotifierProvider(
          create: (_) => FacilitySyncService(
            db: DatabaseService.instance,
            api: ApiService.instance,
          ),
        ),
      ],
      child: MaterialApp(
        title: 'Medico Field',
        debugShowCheckedModeBanner: false,
        theme: buildAppTheme(),
        home: const FacilityHomeScreen(),
      ),
    );
  }
}
