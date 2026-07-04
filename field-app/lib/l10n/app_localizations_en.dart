// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'Medico Field';

  @override
  String get settings => 'Settings';

  @override
  String get synced => 'Synced';

  @override
  String get offline => 'Offline';

  @override
  String get syncing => 'Syncing…';

  @override
  String pendingCount(int n) {
    return '$n pending';
  }

  @override
  String get syncNow => 'Sync Now';

  @override
  String get noFacilitiesTitle => 'No Facilities Loaded';

  @override
  String get noFacilitiesMessage =>
      'Pull down to sync from the server, or connect to a network.\nNo sample data is shown until real facilities are loaded.';

  @override
  String get stockCount => 'Stock Count';

  @override
  String get updateInventoryLevels => 'Update inventory levels';

  @override
  String get bedStatus => 'Bed Status';

  @override
  String get logOccupancy => 'Log occupancy snapshot';

  @override
  String get attendance => 'Attendance';

  @override
  String get staffCheckin => 'Staff check-in';

  @override
  String get footfall => 'Footfall';

  @override
  String get patientCountLog => 'Patient count log';

  @override
  String get noInventoryTitle => 'No Inventory Items';

  @override
  String get noInventoryMessage =>
      'Sync the facility first to load inventory items from the server.';

  @override
  String get saveStockCount => 'Save Stock Count';

  @override
  String get saving => 'Saving…';

  @override
  String get belowReorder => '⚠ Below reorder threshold';

  @override
  String itemsSaved(int n) {
    return '$n items saved. Will sync when online.';
  }

  @override
  String get totalBeds => 'Total Beds';

  @override
  String get occupiedBeds => 'Occupied Beds';

  @override
  String get saveSnapshot => 'Save Snapshot';

  @override
  String get occupiedExceedsTotal => 'Occupied beds cannot exceed total beds';

  @override
  String lastRecorded(String ts) {
    return 'Last recorded: $ts UTC';
  }

  @override
  String get occupancy => 'Occupancy';

  @override
  String get bedSnapshotSaved => 'Bed snapshot saved. Will sync when online.';

  @override
  String get noStaffTitle => 'No Staff Loaded';

  @override
  String get noStaffMessage =>
      'Sync the facility first to load staff members from the server.';

  @override
  String get submitAttendance => 'Submit Attendance';

  @override
  String attendanceSaved(int n) {
    return 'Attendance for $n staff saved. Will sync when online.';
  }

  @override
  String get alreadySubmitted => 'Already submitted';

  @override
  String presentSlashTotal(int present, int total) {
    return '$present / $total Present';
  }

  @override
  String get newEntry => 'New Entry';

  @override
  String get patientCountLabel => 'Patient Count';

  @override
  String get departmentOptional => 'Department (optional)';

  @override
  String get allDepartments => 'All departments';

  @override
  String get logFootfall => 'Log Footfall';

  @override
  String get footfallSaved => 'Footfall logged. Will sync when online.';

  @override
  String get recentEntries => 'RECENT ENTRIES';

  @override
  String patients(int n) {
    return '$n patients';
  }

  @override
  String get patientsMustBePositive => 'Patient count must be ≥ 0';

  @override
  String get backendConnection => 'BACKEND CONNECTION';

  @override
  String get apiBaseUrl => 'API Base URL';

  @override
  String get apiUrlHint => 'http://10.0.2.2:8000';

  @override
  String get apiUrlHelp =>
      'For Android emulator use http://10.0.2.2:8000.\nFor a real device use the server\'s LAN IP.';

  @override
  String get saveUrl => 'Save URL';

  @override
  String get apiUrlUpdated =>
      'API URL updated. Changes take effect immediately.';

  @override
  String get languageLabel => 'LANGUAGE';

  @override
  String get selectLanguage => 'Select Language';

  @override
  String get aiKeysLabel => 'AI / VOICE KEYS';

  @override
  String get whisperKeyLabel => 'Whisper API Key';

  @override
  String get llmKeyLabel => 'LLM API Key (gpt-4o-mini)';

  @override
  String get saveKeys => 'Save Keys';

  @override
  String get keysSaved => 'API keys saved.';

  @override
  String get voiceInput => 'Voice Input';

  @override
  String get recording => 'Recording…';

  @override
  String get processing => 'Processing…';

  @override
  String get reviewExtraction => 'Review Voice Input';

  @override
  String get confirmAndFill => 'Confirm & Fill';

  @override
  String get retryRecording => 'Retry';

  @override
  String get extractionFailed =>
      'Could not understand the recording. Please try again.';

  @override
  String get voiceRequiresNetwork =>
      'Voice input requires a network connection.';

  @override
  String get voiceKeysMissing => 'Set Whisper and LLM keys in Settings first.';

  @override
  String get saved => 'saved';
}
