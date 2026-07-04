import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

const String _kLocaleKey = 'app_locale';

/// Supported locales shown in the language picker.
const List<LocaleOption> kSupportedLocaleOptions = [
  LocaleOption(locale: Locale('en'), label: 'English', nativeLabel: 'English'),
  LocaleOption(locale: Locale('hi'), label: 'Hindi', nativeLabel: 'हिंदी'),
  LocaleOption(locale: Locale('te'), label: 'Telugu', nativeLabel: 'తెలుగు'),
];

class LocaleOption {
  const LocaleOption({
    required this.locale,
    required this.label,
    required this.nativeLabel,
  });
  final Locale locale;
  final String label;
  final String nativeLabel;
}

/// Manages the active [Locale] and persists it across restarts.
///
/// Wire into [MaterialApp.locale] via [Consumer<LocaleService>].
class LocaleService extends ChangeNotifier {
  LocaleService() {
    _loadSavedLocale();
  }

  Locale _locale = const Locale('en');
  Locale get locale => _locale;

  List<LocaleOption> get options => kSupportedLocaleOptions;

  String get currentLabel =>
      kSupportedLocaleOptions
          .firstWhere(
            (o) => o.locale.languageCode == _locale.languageCode,
            orElse: () => kSupportedLocaleOptions.first,
          )
          .nativeLabel;

  Future<void> _loadSavedLocale() async {
    final prefs = await SharedPreferences.getInstance();
    final code = prefs.getString(_kLocaleKey);
    if (code != null) {
      _locale = Locale(code);
      notifyListeners();
    }
  }

  Future<void> setLocale(Locale locale) async {
    if (locale == _locale) return;
    _locale = locale;
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kLocaleKey, locale.languageCode);
  }
}
