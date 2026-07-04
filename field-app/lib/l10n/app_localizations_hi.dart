// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Hindi (`hi`).
class AppLocalizationsHi extends AppLocalizations {
  AppLocalizationsHi([String locale = 'hi']) : super(locale);

  @override
  String get appTitle => 'मेडिको फील्ड';

  @override
  String get settings => 'सेटिंग्स';

  @override
  String get synced => 'सिंक हो गया';

  @override
  String get offline => 'ऑफलाइन';

  @override
  String get syncing => 'सिंक हो रहा है…';

  @override
  String pendingCount(int n) {
    return '$n बाकी';
  }

  @override
  String get syncNow => 'अभी सिंक करें';

  @override
  String get noFacilitiesTitle => 'कोई सुविधा लोड नहीं हुई';

  @override
  String get noFacilitiesMessage =>
      'सर्वर से सिंक करने के लिए नीचे खींचें, या नेटवर्क से कनेक्ट करें।\nवास्तविक सुविधाएं लोड होने तक कोई नमूना डेटा नहीं दिखाया जाएगा।';

  @override
  String get stockCount => 'स्टॉक गिनती';

  @override
  String get updateInventoryLevels => 'इन्वेंटरी स्तर अपडेट करें';

  @override
  String get bedStatus => 'बेड स्थिति';

  @override
  String get logOccupancy => 'अधिभोग स्नैपशॉट लॉग करें';

  @override
  String get attendance => 'उपस्थिति';

  @override
  String get staffCheckin => 'स्टाफ चेक-इन';

  @override
  String get footfall => 'रोगी संख्या';

  @override
  String get patientCountLog => 'रोगी संख्या लॉग';

  @override
  String get noInventoryTitle => 'कोई इन्वेंटरी आइटम नहीं';

  @override
  String get noInventoryMessage =>
      'इन्वेंटरी आइटम लोड करने के लिए पहले सुविधा सिंक करें।';

  @override
  String get saveStockCount => 'स्टॉक गिनती सहेजें';

  @override
  String get saving => 'सहेजा जा रहा है…';

  @override
  String get belowReorder => '⚠ पुनः ऑर्डर सीमा से नीचे';

  @override
  String itemsSaved(int n) {
    return '$n आइटम सहेजे गए। ऑनलाइन होने पर सिंक होंगे।';
  }

  @override
  String get totalBeds => 'कुल बेड';

  @override
  String get occupiedBeds => 'भरे हुए बेड';

  @override
  String get saveSnapshot => 'स्नैपशॉट सहेजें';

  @override
  String get occupiedExceedsTotal => 'भरे हुए बेड कुल बेड से अधिक नहीं हो सकते';

  @override
  String lastRecorded(String ts) {
    return 'अंतिम रिकॉर्ड: $ts UTC';
  }

  @override
  String get occupancy => 'अधिभोग';

  @override
  String get bedSnapshotSaved =>
      'बेड स्नैपशॉट सहेजा गया। ऑनलाइन होने पर सिंक होगा।';

  @override
  String get noStaffTitle => 'कोई स्टाफ लोड नहीं हुआ';

  @override
  String get noStaffMessage =>
      'स्टाफ सदस्यों को लोड करने के लिए पहले सुविधा सिंक करें।';

  @override
  String get submitAttendance => 'उपस्थिति जमा करें';

  @override
  String attendanceSaved(int n) {
    return '$n स्टाफ की उपस्थिति सहेजी गई। ऑनलाइन होने पर सिंक होगी।';
  }

  @override
  String get alreadySubmitted => 'पहले से जमा हो गई';

  @override
  String presentSlashTotal(int present, int total) {
    return '$present / $total उपस्थित';
  }

  @override
  String get newEntry => 'नई प्रविष्टि';

  @override
  String get patientCountLabel => 'रोगी संख्या';

  @override
  String get departmentOptional => 'विभाग (वैकल्पिक)';

  @override
  String get allDepartments => 'सभी विभाग';

  @override
  String get logFootfall => 'रोगी संख्या लॉग करें';

  @override
  String get footfallSaved =>
      'रोगी संख्या लॉग की गई। ऑनलाइन होने पर सिंक होगी।';

  @override
  String get recentEntries => 'हाल की प्रविष्टियां';

  @override
  String patients(int n) {
    return '$n रोगी';
  }

  @override
  String get patientsMustBePositive => 'रोगी संख्या ≥ 0 होनी चाहिए';

  @override
  String get backendConnection => 'बैकएंड कनेक्शन';

  @override
  String get apiBaseUrl => 'API बेस URL';

  @override
  String get apiUrlHint => 'http://10.0.2.2:8000';

  @override
  String get apiUrlHelp =>
      'Android एमुलेटर के लिए http://10.0.2.2:8000 उपयोग करें।\nवास्तविक डिवाइस के लिए सर्वर का LAN IP उपयोग करें।';

  @override
  String get saveUrl => 'URL सहेजें';

  @override
  String get apiUrlUpdated => 'API URL अपडेट किया गया।';

  @override
  String get languageLabel => 'भाषा';

  @override
  String get selectLanguage => 'भाषा चुनें';

  @override
  String get aiKeysLabel => 'AI / वॉइस कुंजियां';

  @override
  String get whisperKeyLabel => 'Whisper API कुंजी';

  @override
  String get llmKeyLabel => 'LLM API कुंजी (gpt-4o-mini)';

  @override
  String get saveKeys => 'कुंजियां सहेजें';

  @override
  String get keysSaved => 'API कुंजियां सहेजी गईं।';

  @override
  String get voiceInput => 'वॉइस इनपुट';

  @override
  String get recording => 'रिकॉर्ड हो रहा है…';

  @override
  String get processing => 'प्रक्रिया हो रही है…';

  @override
  String get reviewExtraction => 'वॉइस इनपुट की समीक्षा करें';

  @override
  String get confirmAndFill => 'पुष्टि करें और भरें';

  @override
  String get retryRecording => 'फिर कोशिश करें';

  @override
  String get extractionFailed =>
      'रिकॉर्डिंग समझ नहीं आई। कृपया फिर कोशिश करें।';

  @override
  String get voiceRequiresNetwork =>
      'वॉइस इनपुट के लिए नेटवर्क कनेक्शन आवश्यक है।';

  @override
  String get voiceKeysMissing =>
      'पहले सेटिंग्स में Whisper और LLM कुंजियां सेट करें।';

  @override
  String get saved => 'सहेजा';
}
