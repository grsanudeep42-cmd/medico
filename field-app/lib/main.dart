import 'dart:io';

import 'package:flutter/material.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:provider/provider.dart';

import '../../core/db/database_service.dart';
import '../../core/services/api_service.dart';
import '../../core/services/connectivity_service.dart';
import '../../core/services/facility_sync_service.dart';
import '../../core/services/locale_service.dart';
import '../../core/services/sync_service.dart';
import '../../core/services/voice_service.dart';
import '../../features/facilities/facility_home_screen.dart';
import '../../shared/theme.dart';
import '../l10n/app_localizations.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // sqflite on Linux/Windows/macOS needs the FFI factory.
  if (Platform.isLinux || Platform.isWindows || Platform.isMacOS) {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
  }

  await DatabaseService.instance.init();
  await ApiService.instance.init();
  await VoiceService.instance.init();

  runApp(const MedicoFieldApp());
}

class MedicoFieldApp extends StatelessWidget {
  const MedicoFieldApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => LocaleService()),
        ChangeNotifierProvider(create: (_) => ConnectivityService()),
        Provider<ApiService>.value(value: ApiService.instance),
        Provider<VoiceService>.value(value: VoiceService.instance),
        ChangeNotifierProxyProvider<ConnectivityService, SyncService>(
          create: (ctx) => SyncService(
            connectivity: ctx.read<ConnectivityService>(),
            db: DatabaseService.instance,
            api: ApiService.instance,
          ),
          update: (ctx, conn, prev) => prev!,
        ),
        ChangeNotifierProvider(
          create: (_) => FacilitySyncService(
            db: DatabaseService.instance,
            api: ApiService.instance,
          ),
        ),
      ],
      child: Consumer<LocaleService>(
        builder: (context, localeService, _) => MaterialApp(
          title: 'Medico Field',
          debugShowCheckedModeBanner: false,
          theme: buildAppTheme(),
          locale: localeService.locale,
          supportedLocales: const [Locale('en'), Locale('hi'), Locale('te')],
          localizationsDelegates: AppLocalizations.localizationsDelegates,
          home: const FacilityHomeScreen(),
        ),
      ),
    );
  }
}
