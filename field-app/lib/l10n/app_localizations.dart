import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_hi.dart';
import 'app_localizations_te.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('hi'),
    Locale('te'),
  ];

  /// Application title
  ///
  /// In en, this message translates to:
  /// **'Medico Field'**
  String get appTitle;

  /// Settings nav label
  ///
  /// In en, this message translates to:
  /// **'Settings'**
  String get settings;

  /// Sync chip: all data uploaded
  ///
  /// In en, this message translates to:
  /// **'Synced'**
  String get synced;

  /// Sync chip: no network
  ///
  /// In en, this message translates to:
  /// **'Offline'**
  String get offline;

  /// Sync chip: upload in progress
  ///
  /// In en, this message translates to:
  /// **'Syncing…'**
  String get syncing;

  /// Sync chip: n writes awaiting upload
  ///
  /// In en, this message translates to:
  /// **'{n} pending'**
  String pendingCount(int n);

  /// Pull-to-refresh button label
  ///
  /// In en, this message translates to:
  /// **'Sync Now'**
  String get syncNow;

  /// Empty state heading on home screen
  ///
  /// In en, this message translates to:
  /// **'No Facilities Loaded'**
  String get noFacilitiesTitle;

  /// Empty state body on home screen
  ///
  /// In en, this message translates to:
  /// **'Pull down to sync from the server, or connect to a network.\nNo sample data is shown until real facilities are loaded.'**
  String get noFacilitiesMessage;

  /// Dashboard card label
  ///
  /// In en, this message translates to:
  /// **'Stock Count'**
  String get stockCount;

  /// Dashboard card subtitle
  ///
  /// In en, this message translates to:
  /// **'Update inventory levels'**
  String get updateInventoryLevels;

  /// Dashboard card label
  ///
  /// In en, this message translates to:
  /// **'Bed Status'**
  String get bedStatus;

  /// Dashboard card subtitle
  ///
  /// In en, this message translates to:
  /// **'Log occupancy snapshot'**
  String get logOccupancy;

  /// Dashboard card label
  ///
  /// In en, this message translates to:
  /// **'Attendance'**
  String get attendance;

  /// Dashboard card subtitle
  ///
  /// In en, this message translates to:
  /// **'Staff check-in'**
  String get staffCheckin;

  /// Dashboard card label
  ///
  /// In en, this message translates to:
  /// **'Footfall'**
  String get footfall;

  /// Dashboard card subtitle
  ///
  /// In en, this message translates to:
  /// **'Patient count log'**
  String get patientCountLog;

  /// Empty state title on stock screen
  ///
  /// In en, this message translates to:
  /// **'No Inventory Items'**
  String get noInventoryTitle;

  /// Empty state body on stock screen
  ///
  /// In en, this message translates to:
  /// **'Sync the facility first to load inventory items from the server.'**
  String get noInventoryMessage;

  /// Stock screen save button
  ///
  /// In en, this message translates to:
  /// **'Save Stock Count'**
  String get saveStockCount;

  /// Button loading state
  ///
  /// In en, this message translates to:
  /// **'Saving…'**
  String get saving;

  /// Low stock warning label
  ///
  /// In en, this message translates to:
  /// **'⚠ Below reorder threshold'**
  String get belowReorder;

  /// Snackbar after saving stock
  ///
  /// In en, this message translates to:
  /// **'{n} items saved. Will sync when online.'**
  String itemsSaved(int n);

  /// Bed status stepper label
  ///
  /// In en, this message translates to:
  /// **'Total Beds'**
  String get totalBeds;

  /// Bed status stepper label
  ///
  /// In en, this message translates to:
  /// **'Occupied Beds'**
  String get occupiedBeds;

  /// Bed status save button
  ///
  /// In en, this message translates to:
  /// **'Save Snapshot'**
  String get saveSnapshot;

  /// Validation error for bed status
  ///
  /// In en, this message translates to:
  /// **'Occupied beds cannot exceed total beds'**
  String get occupiedExceedsTotal;

  /// Bed status last-recorded label
  ///
  /// In en, this message translates to:
  /// **'Last recorded: {ts} UTC'**
  String lastRecorded(String ts);

  /// Occupancy ring label
  ///
  /// In en, this message translates to:
  /// **'Occupancy'**
  String get occupancy;

  /// Snackbar after saving bed snapshot
  ///
  /// In en, this message translates to:
  /// **'Bed snapshot saved. Will sync when online.'**
  String get bedSnapshotSaved;

  /// Empty state title on attendance screen
  ///
  /// In en, this message translates to:
  /// **'No Staff Loaded'**
  String get noStaffTitle;

  /// Empty state body on attendance screen
  ///
  /// In en, this message translates to:
  /// **'Sync the facility first to load staff members from the server.'**
  String get noStaffMessage;

  /// Attendance submit button
  ///
  /// In en, this message translates to:
  /// **'Submit Attendance'**
  String get submitAttendance;

  /// Snackbar after attendance submit
  ///
  /// In en, this message translates to:
  /// **'Attendance for {n} staff saved. Will sync when online.'**
  String attendanceSaved(int n);

  /// Staff tile subtitle when attendance already logged
  ///
  /// In en, this message translates to:
  /// **'Already submitted'**
  String get alreadySubmitted;

  /// Attendance date bar summary
  ///
  /// In en, this message translates to:
  /// **'{present} / {total} Present'**
  String presentSlashTotal(int present, int total);

  /// Footfall card heading
  ///
  /// In en, this message translates to:
  /// **'New Entry'**
  String get newEntry;

  /// Footfall count field label
  ///
  /// In en, this message translates to:
  /// **'Patient Count'**
  String get patientCountLabel;

  /// Footfall department dropdown label
  ///
  /// In en, this message translates to:
  /// **'Department (optional)'**
  String get departmentOptional;

  /// Footfall dropdown 'no department' option
  ///
  /// In en, this message translates to:
  /// **'All departments'**
  String get allDepartments;

  /// Footfall submit button
  ///
  /// In en, this message translates to:
  /// **'Log Footfall'**
  String get logFootfall;

  /// Snackbar after logging footfall
  ///
  /// In en, this message translates to:
  /// **'Footfall logged. Will sync when online.'**
  String get footfallSaved;

  /// Footfall recent entries section header
  ///
  /// In en, this message translates to:
  /// **'RECENT ENTRIES'**
  String get recentEntries;

  /// Footfall log patient count
  ///
  /// In en, this message translates to:
  /// **'{n} patients'**
  String patients(int n);

  /// Footfall validation error
  ///
  /// In en, this message translates to:
  /// **'Patient count must be ≥ 0'**
  String get patientsMustBePositive;

  /// Settings section header
  ///
  /// In en, this message translates to:
  /// **'BACKEND CONNECTION'**
  String get backendConnection;

  /// Settings URL field label
  ///
  /// In en, this message translates to:
  /// **'API Base URL'**
  String get apiBaseUrl;

  /// Settings URL field hint
  ///
  /// In en, this message translates to:
  /// **'http://10.0.2.2:8000'**
  String get apiUrlHint;

  /// Settings URL helper text
  ///
  /// In en, this message translates to:
  /// **'For Android emulator use http://10.0.2.2:8000.\nFor a real device use the server\'s LAN IP.'**
  String get apiUrlHelp;

  /// Settings save URL button
  ///
  /// In en, this message translates to:
  /// **'Save URL'**
  String get saveUrl;

  /// Snackbar after saving URL
  ///
  /// In en, this message translates to:
  /// **'API URL updated. Changes take effect immediately.'**
  String get apiUrlUpdated;

  /// Settings language section header
  ///
  /// In en, this message translates to:
  /// **'LANGUAGE'**
  String get languageLabel;

  /// Settings language dropdown label
  ///
  /// In en, this message translates to:
  /// **'Select Language'**
  String get selectLanguage;

  /// Settings AI keys section header
  ///
  /// In en, this message translates to:
  /// **'AI / VOICE KEYS'**
  String get aiKeysLabel;

  /// Settings Whisper key field label
  ///
  /// In en, this message translates to:
  /// **'Whisper API Key'**
  String get whisperKeyLabel;

  /// Settings LLM key field label
  ///
  /// In en, this message translates to:
  /// **'LLM API Key (gpt-4o-mini)'**
  String get llmKeyLabel;

  /// Settings save AI keys button
  ///
  /// In en, this message translates to:
  /// **'Save Keys'**
  String get saveKeys;

  /// Snackbar after saving keys
  ///
  /// In en, this message translates to:
  /// **'API keys saved.'**
  String get keysSaved;

  /// Voice button tooltip
  ///
  /// In en, this message translates to:
  /// **'Voice Input'**
  String get voiceInput;

  /// Voice button recording state
  ///
  /// In en, this message translates to:
  /// **'Recording…'**
  String get recording;

  /// Voice button processing state
  ///
  /// In en, this message translates to:
  /// **'Processing…'**
  String get processing;

  /// Bottom sheet title
  ///
  /// In en, this message translates to:
  /// **'Review Voice Input'**
  String get reviewExtraction;

  /// Voice review confirm button
  ///
  /// In en, this message translates to:
  /// **'Confirm & Fill'**
  String get confirmAndFill;

  /// Voice review retry button
  ///
  /// In en, this message translates to:
  /// **'Retry'**
  String get retryRecording;

  /// Voice extraction error message
  ///
  /// In en, this message translates to:
  /// **'Could not understand the recording. Please try again.'**
  String get extractionFailed;

  /// Toast when offline and mic tapped
  ///
  /// In en, this message translates to:
  /// **'Voice input requires a network connection.'**
  String get voiceRequiresNetwork;

  /// Toast when keys not configured
  ///
  /// In en, this message translates to:
  /// **'Set Whisper and LLM keys in Settings first.'**
  String get voiceKeysMissing;

  /// Badge on footfall recent log entry
  ///
  /// In en, this message translates to:
  /// **'saved'**
  String get saved;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en', 'hi', 'te'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'hi':
      return AppLocalizationsHi();
    case 'te':
      return AppLocalizationsTe();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
