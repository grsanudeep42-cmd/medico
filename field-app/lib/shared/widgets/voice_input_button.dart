import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/services/connectivity_service.dart';
import '../theme.dart';

/// Animated mic FAB that cycles through idle → recording → processing states.
///
/// Calls [onRecordingComplete] with the raw audio file path when the user
/// stops recording. The parent widget (or [VoiceReviewSheet]) handles
/// the Whisper + LLM pipeline.
///
/// [onStart] / [onStop] allow the parent to show a recording indicator.
class VoiceInputButton extends StatefulWidget {
  const VoiceInputButton({
    super.key,
    required this.onStart,
    required this.onStop,
    this.tooltip,
    this.isProcessing = false,
  });

  /// Called when the user taps to START recording.
  final VoidCallback onStart;

  /// Called when the user taps again to STOP recording.
  final VoidCallback onStop;

  final String? tooltip;

  /// Set to true while the pipeline (Whisper + LLM) is running.
  final bool isProcessing;

  @override
  State<VoiceInputButton> createState() => _VoiceInputButtonState();
}

class _VoiceInputButtonState extends State<VoiceInputButton>
    with SingleTickerProviderStateMixin {
  bool _recording = false;
  late final AnimationController _pulseCtrl;
  late final Animation<double> _pulseAnim;

  @override
  void initState() {
    super.initState();
    _pulseCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    )..repeat(reverse: true);
    _pulseAnim = Tween<double>(begin: 1.0, end: 1.18).animate(
      CurvedAnimation(parent: _pulseCtrl, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _pulseCtrl.dispose();
    super.dispose();
  }

  void _handleTap() {
    final conn = context.read<ConnectivityService>();
    if (!conn.isOnline) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: const Text('Voice input requires a network connection.'),
        backgroundColor: kColorDanger,
      ));
      return;
    }

    if (widget.isProcessing) return;

    if (_recording) {
      setState(() => _recording = false);
      widget.onStop();
    } else {
      setState(() => _recording = true);
      widget.onStart();
    }
  }

  @override
  Widget build(BuildContext context) {
    Color bg;
    Widget icon;

    if (widget.isProcessing) {
      bg = kColorWarning;
      icon = const SizedBox(
        width: 22,
        height: 22,
        child: CircularProgressIndicator(strokeWidth: 2, color: kColorBackground),
      );
    } else if (_recording) {
      bg = kColorDanger;
      icon = const Icon(Icons.stop_rounded, color: kColorBackground, size: 26);
    } else {
      bg = kColorAccent;
      icon = const Icon(Icons.mic_rounded, color: kColorBackground, size: 26);
    }

    final fab = FloatingActionButton(
      heroTag: null,
      onPressed: _handleTap,
      backgroundColor: bg,
      tooltip: widget.tooltip ?? 'Voice Input',
      child: icon,
    );

    if (_recording) {
      return ScaleTransition(scale: _pulseAnim, child: fab);
    }
    return fab;
  }
}


/// Compact inline mic icon button for use inside app bars or form rows.
class VoiceMicButton extends StatelessWidget {
  const VoiceMicButton({
    super.key,
    required this.onStart,
    required this.onStop,
    required this.isRecording,
    this.isProcessing = false,
  });

  final VoidCallback onStart;
  final VoidCallback onStop;
  final bool isRecording;
  final bool isProcessing;

  @override
  Widget build(BuildContext context) {
    Color color;
    IconData icon;

    if (isProcessing) {
      color = kColorWarning;
      icon = Icons.hourglass_top_rounded;
    } else if (isRecording) {
      color = kColorDanger;
      icon = Icons.stop_circle_rounded;
    } else {
      color = kColorAccent;
      icon = Icons.mic_rounded;
    }

    return IconButton(
      onPressed: () {
        final conn = context.read<ConnectivityService>();
        if (!conn.isOnline) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: const Text('Voice input requires a network connection.'),
            backgroundColor: kColorDanger,
          ));
          return;
        }
        if (isProcessing) return;
        isRecording ? onStop() : onStart();
      },
      icon: Icon(icon, color: color),
      tooltip: 'Voice input',
    );
  }
}
