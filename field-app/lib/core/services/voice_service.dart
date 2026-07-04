import 'dart:convert';
import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models/extraction_result.dart';

const _kWhisperKeyPref = 'whisper_api_key';
const _kLlmKeyPref = 'llm_api_key';

/// Screen context passed to [VoiceService.extract] so the correct
/// LLM system prompt and JSON schema are used.
enum VoiceScreen { stock, beds, attendance, footfall }

/// Orchestrates: record audio → Whisper STT → LLM extraction.
///
/// Usage:
/// ```dart
/// final vs = VoiceService.instance;
/// await vs.init();
/// await vs.startRecording();
/// // ... user speaks ...
/// final result = await vs.stopAndProcess(screen: VoiceScreen.stock);
/// // result is StockExtraction | ExtractionError
/// ```
class VoiceService {
  VoiceService._();
  static final VoiceService instance = VoiceService._();

  final AudioRecorder _recorder = AudioRecorder();
  late final Dio _openaiDio;
  bool _initialized = false;
  bool _recording = false;

  bool get isRecording => _recording;

  // ── Init ───────────────────────────────────────────────────────────────────

  Future<void> init() async {
    if (_initialized) return;
    _openaiDio = Dio(BaseOptions(
      baseUrl: 'https://api.openai.com/v1',
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 60),
    ));
    _initialized = true;
  }

  // ── Key management ─────────────────────────────────────────────────────────

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

  // ── Recording ──────────────────────────────────────────────────────────────

  /// Returns the temp file path where audio will be saved.
  Future<String> _tempPath() async {
    final dir = await getTemporaryDirectory();
    return '${dir.path}/medico_voice.m4a';
  }

  Future<void> startRecording() async {
    if (_recording) return;
    final hasPermission = await _recorder.hasPermission();
    if (!hasPermission) {
      throw Exception('Microphone permission denied');
    }
    final path = await _tempPath();
    await _recorder.start(
      const RecordConfig(encoder: AudioEncoder.aacLc, bitRate: 64000, sampleRate: 16000),
      path: path,
    );
    _recording = true;
  }

  /// Stops recording and returns the file path.
  Future<String?> stopRecording() async {
    if (!_recording) return null;
    final path = await _recorder.stop();
    _recording = false;
    return path;
  }

  /// Cancels recording without processing.
  Future<void> cancelRecording() async {
    if (_recording) {
      await _recorder.cancel();
      _recording = false;
    }
  }

  // ── Full pipeline ──────────────────────────────────────────────────────────

  /// Stop recording → Whisper → LLM → typed [ExtractionResult].
  Future<ExtractionResult> stopAndProcess({
    required VoiceScreen screen,
    String languageCode = 'en',
  }) async {
    final filePath = await stopRecording();
    if (filePath == null) {
      return const ExtractionError('Recording failed to produce a file.');
    }
    try {
      final transcript = await _transcribe(filePath, languageCode);
      if (transcript.isEmpty) {
        return const ExtractionError('No speech detected. Please try again.');
      }
      return await _extract(transcript, screen);
    } catch (e) {
      debugPrint('[VoiceService] Pipeline error: $e');
      return ExtractionError(e.toString());
    } finally {
      // Clean up temp file
      try { File(filePath).deleteSync(); } catch (_) {}
    }
  }

  // ── Whisper STT ────────────────────────────────────────────────────────────

  Future<String> _transcribe(String filePath, String languageCode) async {
    final key = await getWhisperKey();
    final formData = FormData.fromMap({
      'model': 'whisper-1',
      'language': languageCode,
      'response_format': 'text',
      'file': await MultipartFile.fromFile(filePath, filename: 'audio.m4a'),
    });
    final resp = await _openaiDio.post(
      '/audio/transcriptions',
      data: formData,
      options: Options(headers: {'Authorization': 'Bearer $key'}),
    );
    return (resp.data as String).trim();
  }

  // ── LLM extraction ─────────────────────────────────────────────────────────

  static const Map<VoiceScreen, String> _systemPrompts = {
    VoiceScreen.stock: '''
You are a medical supply clerk assistant. Extract stock information from the transcript.
Return ONLY valid JSON with this exact schema:
{"item_name": string, "quantity": number, "unit": string, "action": "set"|"add"|"remove"}
- action "set" means replace current count, "add" means increase, "remove" means decrease.
- unit can be empty string if not mentioned.
- If you cannot extract a valid item and quantity, return {"error": "cannot parse"}.
''',
    VoiceScreen.beds: '''
You are a hospital bed management assistant. Extract bed occupancy information.
Return ONLY valid JSON with this exact schema:
{"total_beds": integer|null, "occupied_beds": integer|null}
- Use null for any field not mentioned.
- If nothing can be extracted, return {"error": "cannot parse"}.
''',
    VoiceScreen.attendance: '''
You are a healthcare attendance system assistant. Extract attendance information.
Return ONLY valid JSON with this exact schema:
{"names": [string], "status": "present"|"absent"}
- names is a list of staff member names or partial names as spoken.
- If nothing can be extracted, return {"error": "cannot parse"}.
''',
    VoiceScreen.footfall: '''
You are a medical facility footfall logger. Extract patient count information.
Return ONLY valid JSON with this exact schema:
{"count": integer, "department": string|null}
- department is null if not mentioned or if it refers to the whole facility.
- If no count can be extracted, return {"error": "cannot parse"}.
''',
  };

  Future<ExtractionResult> _extract(String transcript, VoiceScreen screen) async {
    final key = await getLlmKey();
    final systemPrompt = _systemPrompts[screen]!;

    final resp = await _openaiDio.post(
      '/chat/completions',
      data: {
        'model': 'gpt-4o-mini',
        'response_format': {'type': 'json_object'},
        'messages': [
          {'role': 'system', 'content': systemPrompt},
          {'role': 'user', 'content': transcript},
        ],
        'max_tokens': 200,
        'temperature': 0,
      },
      options: Options(headers: {'Authorization': 'Bearer $key'}),
    );

    final content = resp.data['choices'][0]['message']['content'] as String;
    final json = jsonDecode(content) as Map<String, dynamic>;

    if (json.containsKey('error')) {
      return ExtractionError('LLM could not parse: ${json['error']}');
    }

    return switch (screen) {
      VoiceScreen.stock => StockExtraction.fromJson(json),
      VoiceScreen.beds => BedExtraction.fromJson(json),
      VoiceScreen.attendance => AttendanceExtraction.fromJson(json),
      VoiceScreen.footfall => FootfallExtraction.fromJson(json),
    };
  }

  void dispose() {
    _recorder.dispose();
  }
}
