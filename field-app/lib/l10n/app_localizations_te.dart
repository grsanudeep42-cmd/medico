// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Telugu (`te`).
class AppLocalizationsTe extends AppLocalizations {
  AppLocalizationsTe([String locale = 'te']) : super(locale);

  @override
  String get appTitle => 'మెడికో ఫీల్డ్';

  @override
  String get settings => 'సెట్టింగులు';

  @override
  String get synced => 'సమకాలీకరించబడింది';

  @override
  String get offline => 'ఆఫ్‌లైన్';

  @override
  String get syncing => 'సమకాలీకరిస్తోంది…';

  @override
  String pendingCount(int n) {
    return '$n పెండింగ్';
  }

  @override
  String get syncNow => 'ఇప్పుడు సమకాలీకరించు';

  @override
  String get noFacilitiesTitle => 'సౌకర్యాలు లోడ్ కాలేదు';

  @override
  String get noFacilitiesMessage =>
      'సర్వర్ నుండి సమకాలీకరించడానికి క్రిందికి లాగండి, లేదా నెట్‌వర్క్‌కు కనెక్ట్ అవ్వండి.\nనిజమైన సౌకర్యాలు లోడ్ అయ్యే వరకు నమూనా డేటా చూపబడదు.';

  @override
  String get stockCount => 'స్టాక్ లెక్క';

  @override
  String get updateInventoryLevels => 'జాబితా స్థాయిలను అప్‌డేట్ చేయండి';

  @override
  String get bedStatus => 'బెడ్ స్థితి';

  @override
  String get logOccupancy => 'ఆక్యుపెన్సీ స్నాప్‌షాట్ లాగ్ చేయండి';

  @override
  String get attendance => 'హాజరు';

  @override
  String get staffCheckin => 'సిబ్బంది చెక్-ఇన్';

  @override
  String get footfall => 'పేషెంట్ సంఖ్య';

  @override
  String get patientCountLog => 'పేషెంట్ సంఖ్య లాగ్';

  @override
  String get noInventoryTitle => 'జాబితా అంశాలు లేవు';

  @override
  String get noInventoryMessage =>
      'జాబితా అంశాలు లోడ్ చేయడానికి ముందు సౌకర్యాన్ని సమకాలీకరించండి.';

  @override
  String get saveStockCount => 'స్టాక్ లెక్క సేవ్ చేయండి';

  @override
  String get saving => 'సేవ్ అవుతోంది…';

  @override
  String get belowReorder => '⚠ రీఆర్డర్ పరిమితి కంటే తక్కువ';

  @override
  String itemsSaved(int n) {
    return '$n అంశాలు సేవ్ అయ్యాయి. ఆన్‌లైన్‌లో ఉన్నప్పుడు సమకాలీకరించబడతాయి.';
  }

  @override
  String get totalBeds => 'మొత్తం బెడ్లు';

  @override
  String get occupiedBeds => 'ఆక్యుపైడ్ బెడ్లు';

  @override
  String get saveSnapshot => 'స్నాప్‌షాట్ సేవ్ చేయండి';

  @override
  String get occupiedExceedsTotal =>
      'ఆక్యుపైడ్ బెడ్లు మొత్తం బెడ్లను మించకూడదు';

  @override
  String lastRecorded(String ts) {
    return 'చివరిగా రికార్డ్: $ts UTC';
  }

  @override
  String get occupancy => 'ఆక్యుపెన్సీ';

  @override
  String get bedSnapshotSaved =>
      'బెడ్ స్నాప్‌షాట్ సేవ్ అయింది. ఆన్‌లైన్‌లో ఉన్నప్పుడు సమకాలీకరించబడుతుంది.';

  @override
  String get noStaffTitle => 'సిబ్బంది లోడ్ కాలేదు';

  @override
  String get noStaffMessage =>
      'సిబ్బంది సభ్యులను లోడ్ చేయడానికి ముందు సౌకర్యాన్ని సమకాలీకరించండి.';

  @override
  String get submitAttendance => 'హాజరు సమర్పించండి';

  @override
  String attendanceSaved(int n) {
    return '$n సిబ్బంది హాజరు సేవ్ అయింది. ఆన్‌లైన్‌లో ఉన్నప్పుడు సమకాలీకరించబడుతుంది.';
  }

  @override
  String get alreadySubmitted => 'ఇప్పటికే సమర్పించబడింది';

  @override
  String presentSlashTotal(int present, int total) {
    return '$present / $total హాజరు';
  }

  @override
  String get newEntry => 'కొత్త నమోదు';

  @override
  String get patientCountLabel => 'పేషెంట్ సంఖ్య';

  @override
  String get departmentOptional => 'విభాగం (ఐచ్ఛికం)';

  @override
  String get allDepartments => 'అన్ని విభాగాలు';

  @override
  String get logFootfall => 'పేషెంట్ సంఖ్య లాగ్ చేయండి';

  @override
  String get footfallSaved =>
      'పేషెంట్ సంఖ్య లాగ్ అయింది. ఆన్‌లైన్‌లో ఉన్నప్పుడు సమకాలీకరించబడుతుంది.';

  @override
  String get recentEntries => 'ఇటీవలి నమోదులు';

  @override
  String patients(int n) {
    return '$n పేషెంట్లు';
  }

  @override
  String get patientsMustBePositive => 'పేషెంట్ సంఖ్య ≥ 0 అయి ఉండాలి';

  @override
  String get backendConnection => 'బ్యాకెండ్ కనెక్షన్';

  @override
  String get apiBaseUrl => 'API బేస్ URL';

  @override
  String get apiUrlHint => 'http://10.0.2.2:8000';

  @override
  String get apiUrlHelp =>
      'Android ఎమ్యులేటర్ కోసం http://10.0.2.2:8000 వాడండి.\nనిజమైన పరికరానికి సర్వర్ LAN IP వాడండి.';

  @override
  String get saveUrl => 'URL సేవ్ చేయండి';

  @override
  String get apiUrlUpdated => 'API URL అప్‌డేట్ అయింది.';

  @override
  String get languageLabel => 'భాష';

  @override
  String get selectLanguage => 'భాష ఎంచుకోండి';

  @override
  String get aiKeysLabel => 'AI / వాయిస్ కీలు';

  @override
  String get whisperKeyLabel => 'Whisper API కీ';

  @override
  String get llmKeyLabel => 'LLM API కీ (gpt-4o-mini)';

  @override
  String get saveKeys => 'కీలు సేవ్ చేయండి';

  @override
  String get keysSaved => 'API కీలు సేవ్ అయ్యాయి.';

  @override
  String get voiceInput => 'వాయిస్ ఇన్‌పుట్';

  @override
  String get recording => 'రికార్డ్ అవుతోంది…';

  @override
  String get processing => 'ప్రాసెస్ అవుతోంది…';

  @override
  String get reviewExtraction => 'వాయిస్ ఇన్‌పుట్ సమీక్ష';

  @override
  String get confirmAndFill => 'నిర్ధారించి నింపండి';

  @override
  String get retryRecording => 'మళ్ళీ ప్రయత్నించండి';

  @override
  String get extractionFailed =>
      'రికార్డింగ్ అర్థం కాలేదు. దయచేసి మళ్ళీ ప్రయత్నించండి.';

  @override
  String get voiceRequiresNetwork =>
      'వాయిస్ ఇన్‌పుట్‌కు నెట్‌వర్క్ కనెక్షన్ అవసరం.';

  @override
  String get voiceKeysMissing =>
      'ముందు సెట్టింగులలో Whisper మరియు LLM కీలు సెట్ చేయండి.';

  @override
  String get saved => 'సేవ్ అయింది';
}
