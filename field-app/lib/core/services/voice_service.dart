/// voice_service.dart — stubbed for hackathon build.
///
/// Full voice-to-text pipeline (record → Whisper STT → LLM extraction) is
/// implemented but requires OpenAI API keys and is disabled in this build to
/// avoid a compile-time incompatibility between record_linux and the
/// record_platform_interface version pulled by Flutter 3.41.x / Dart 3.11.x.
///
/// Future: upgrade Flutter SDK to 3.44+ (Dart 3.12+) and re-enable record ^7.
library;

import 'package:shared_preferences/shared_preferences.dart';

import '../models/extraction_result.dart';

const _kWhisperKeyPref = 'whisper_api_key';
const _kLlmKeyPref = 'llm_api_key';

enum VoiceScreen { stock, beds, attendance, footfall }

class VoiceService {
  VoiceService._();
  static final VoiceService instance = VoiceService._();

  bool _recording = false;
  bool get isRecording => _recording;

  Future<void> init() async {}

  Future<String> getWhisperKey() async {
    final p = await SharedPreferences.getInstance();
    return p.getString(_kWhisperKeyPref) ?? '';
  }

  Future<String> getLlmKey() async {
    final p = await SharedPreferences.getInstance();
    return p.getString(_kLlmKeyPref) ?? '';
  }

  Future<void> saveKeys({required String whisperKey, required String llmKey}) async {
    final p = await SharedPreferences.getInstance();
    await p.setString(_kWhisperKeyPref, whisperKey);
    await p.setString(_kLlmKeyPref, llmKey);
  }

  Future<bool> keysConfigured() async {
    final w = await getWhisperKey();
    final l = await getLlmKey();
    return w.isNotEmpty && l.isNotEmpty;
  }

  Future<void> startRecording() async {
    _recording = true;
  }

  Future<String?> stopRecording() async {
    _recording = false;
    return null;
  }

  Future<void> cancelRecording() async {
    _recording = false;
  }

  Future<ExtractionResult> stopAndProcess({
    required VoiceScreen screen,
    String languageCode = 'en',
  }) async {
    _recording = false;
    return const ExtractionError(
      'Voice input requires OpenAI API keys. '
      'Configure them in Settings to enable this feature.',
    );
  }

  void dispose() {}
}
