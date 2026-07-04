import 'package:flutter/material.dart';

import '../../core/models/extraction_result.dart';
import '../theme.dart';

/// Modal bottom sheet shown after voice extraction.
///
/// Displays extracted fields with editable inline inputs.
/// Has **"Confirm & Fill"** and **"Retry"** buttons.
///
/// NEVER writes data itself — calls [onConfirm] with the (possibly edited)
/// [ExtractionResult]. The parent screen's form still requires an explicit
/// Save / Submit tap.
class VoiceReviewSheet extends StatelessWidget {
  const VoiceReviewSheet({
    super.key,
    required this.result,
    required this.onConfirm,
    required this.onRetry,
  });

  final ExtractionResult result;
  final ValueChanged<ExtractionResult> onConfirm;
  final VoidCallback onRetry;

  static Future<void> show({
    required BuildContext context,
    required ExtractionResult result,
    required ValueChanged<ExtractionResult> onConfirm,
    required VoidCallback onRetry,
  }) {
    return showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: kColorCard,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (_) => VoiceReviewSheet(
        result: result,
        onConfirm: onConfirm,
        onRetry: onRetry,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        left: 20,
        right: 20,
        top: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 24,
      ),
      child: switch (result) {
        ExtractionError() => _ErrorBody(
            message: (result as ExtractionError).message,
            onRetry: onRetry,
          ),
        StockExtraction() => _StockReviewBody(
            initial: result as StockExtraction,
            onConfirm: onConfirm,
            onRetry: onRetry,
          ),
        BedExtraction() => _BedReviewBody(
            initial: result as BedExtraction,
            onConfirm: onConfirm,
            onRetry: onRetry,
          ),
        AttendanceExtraction() => _AttendanceReviewBody(
            initial: result as AttendanceExtraction,
            onConfirm: onConfirm,
            onRetry: onRetry,
          ),
        FootfallExtraction() => _FootfallReviewBody(
            initial: result as FootfallExtraction,
            onConfirm: onConfirm,
            onRetry: onRetry,
          ),
      },
    );
  }
}

// ── Shared helpers ────────────────────────────────────────────────────────────

Widget _sheetHeader(String title) => Column(
  children: [
    Container(
      width: 40, height: 4,
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: const Color(0xFF4A6080),
        borderRadius: BorderRadius.circular(2),
      ),
    ),
    Row(children: [
      Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: const Color(0xFF00C9A7).withAlpha(25),
          borderRadius: BorderRadius.circular(10),
        ),
        child: const Icon(Icons.auto_awesome_rounded, color: Color(0xFF00C9A7), size: 18),
      ),
      const SizedBox(width: 10),
      Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: Color(0xFFF0F4FF))),
    ]),
    const SizedBox(height: 4),
    const Text('Review and edit before confirming. Nothing is saved until you tap Confirm.',
        style: TextStyle(fontSize: 12, color: Color(0xFF8BA3CC))),
    const Divider(height: 24, color: Color(0xFF1E2D50)),
  ],
);

Widget _actionRow(BuildContext context, {required VoidCallback onConfirm, required VoidCallback onRetry}) =>
    Row(children: [
      Expanded(
        child: OutlinedButton.icon(
          onPressed: () { Navigator.pop(context); onRetry(); },
          icon: const Icon(Icons.refresh_rounded, size: 16),
          label: const Text('Retry'),
          style: OutlinedButton.styleFrom(
            foregroundColor: const Color(0xFF8BA3CC),
            side: const BorderSide(color: Color(0xFF1E2D50)),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            padding: const EdgeInsets.symmetric(vertical: 14),
          ),
        ),
      ),
      const SizedBox(width: 12),
      Expanded(
        flex: 2,
        child: ElevatedButton.icon(
          onPressed: () { Navigator.pop(context); onConfirm(); },
          icon: const Icon(Icons.check_rounded, size: 18),
          label: const Text('Confirm & Fill'),
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF00C9A7),
            foregroundColor: const Color(0xFF0A1628),
            padding: const EdgeInsets.symmetric(vertical: 14),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
        ),
      ),
    ]);

InputDecoration _fieldDeco(String label) => InputDecoration(
  labelText: label,
  labelStyle: const TextStyle(color: Color(0xFF8BA3CC)),
  filled: true,
  fillColor: const Color(0xFF0F1F3D),
  border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: Color(0xFF1E2D50))),
  enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: Color(0xFF1E2D50))),
  focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: Color(0xFF00C9A7))),
  contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
);

// ── Error body ────────────────────────────────────────────────────────────────

class _ErrorBody extends StatelessWidget {
  const _ErrorBody({required this.message, required this.onRetry});
  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
      _sheetHeader('Voice Input'),
      const Icon(Icons.error_outline_rounded, color: Color(0xFFFF6B6B), size: 40),
      const SizedBox(height: 12),
      Text(message, style: const TextStyle(color: Color(0xFF8BA3CC), fontSize: 14)),
      const SizedBox(height: 20),
      SizedBox(width: double.infinity, child: ElevatedButton.icon(
        onPressed: () { Navigator.pop(context); onRetry(); },
        icon: const Icon(Icons.refresh_rounded),
        label: const Text('Retry Recording'),
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFF00C9A7),
          foregroundColor: const Color(0xFF0A1628),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          padding: const EdgeInsets.symmetric(vertical: 14),
        ),
      )),
    ]);
  }
}

// ── Stock review ──────────────────────────────────────────────────────────────

class _StockReviewBody extends StatefulWidget {
  const _StockReviewBody({required this.initial, required this.onConfirm, required this.onRetry});
  final StockExtraction initial;
  final ValueChanged<ExtractionResult> onConfirm;
  final VoidCallback onRetry;

  @override
  State<_StockReviewBody> createState() => _StockReviewBodyState();
}

class _StockReviewBodyState extends State<_StockReviewBody> {
  late final TextEditingController _itemCtrl;
  late final TextEditingController _qtyCtrl;
  late final TextEditingController _unitCtrl;
  late String _action;

  @override
  void initState() {
    super.initState();
    _itemCtrl = TextEditingController(text: widget.initial.itemName);
    _qtyCtrl = TextEditingController(text: widget.initial.quantity.toString());
    _unitCtrl = TextEditingController(text: widget.initial.unit);
    _action = widget.initial.action;
  }

  @override
  void dispose() {
    _itemCtrl.dispose(); _qtyCtrl.dispose(); _unitCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
      _sheetHeader('Review Voice Input'),
      const Text('ITEM', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: Color(0xFF4A6080), letterSpacing: 1)),
      const SizedBox(height: 6),
      TextField(controller: _itemCtrl, style: const TextStyle(color: Color(0xFFF0F4FF)), decoration: _fieldDeco('Item name')),
      const SizedBox(height: 12),
      Row(children: [
        Expanded(child: TextField(controller: _qtyCtrl, keyboardType: const TextInputType.numberWithOptions(decimal: true),
            style: const TextStyle(color: Color(0xFFF0F4FF)), decoration: _fieldDeco('Quantity'))),
        const SizedBox(width: 10),
        Expanded(child: TextField(controller: _unitCtrl,
            style: const TextStyle(color: Color(0xFFF0F4FF)), decoration: _fieldDeco('Unit'))),
      ]),
      const SizedBox(height: 12),
      const Text('ACTION', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: Color(0xFF4A6080), letterSpacing: 1)),
      const SizedBox(height: 6),
      SegmentedButton<String>(
        segments: const [
          ButtonSegment(value: 'set', label: Text('Set')),
          ButtonSegment(value: 'add', label: Text('Add')),
          ButtonSegment(value: 'remove', label: Text('Remove')),
        ],
        selected: {_action},
        onSelectionChanged: (s) => setState(() => _action = s.first),
        style: ButtonStyle(
          backgroundColor: WidgetStateProperty.resolveWith(
            (s) => s.contains(WidgetState.selected) ? const Color(0xFF00C9A7).withAlpha(40) : const Color(0xFF0F1F3D),
          ),
          foregroundColor: WidgetStateProperty.resolveWith(
            (s) => s.contains(WidgetState.selected) ? const Color(0xFF00C9A7) : const Color(0xFF8BA3CC),
          ),
        ),
      ),
      const SizedBox(height: 20),
      _actionRow(context,
        onConfirm: () => widget.onConfirm(StockExtraction(
          itemName: _itemCtrl.text.trim(),
          quantity: double.tryParse(_qtyCtrl.text) ?? widget.initial.quantity,
          unit: _unitCtrl.text.trim(),
          action: _action,
        )),
        onRetry: widget.onRetry,
      ),
    ]);
  }
}

// ── Bed review ────────────────────────────────────────────────────────────────

class _BedReviewBody extends StatefulWidget {
  const _BedReviewBody({required this.initial, required this.onConfirm, required this.onRetry});
  final BedExtraction initial;
  final ValueChanged<ExtractionResult> onConfirm;
  final VoidCallback onRetry;

  @override
  State<_BedReviewBody> createState() => _BedReviewBodyState();
}

class _BedReviewBodyState extends State<_BedReviewBody> {
  late final TextEditingController _totalCtrl;
  late final TextEditingController _occupiedCtrl;

  @override
  void initState() {
    super.initState();
    _totalCtrl = TextEditingController(text: widget.initial.totalBeds?.toString() ?? '');
    _occupiedCtrl = TextEditingController(text: widget.initial.occupiedBeds?.toString() ?? '');
  }

  @override
  void dispose() { _totalCtrl.dispose(); _occupiedCtrl.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    return Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
      _sheetHeader('Review Voice Input'),
      Row(children: [
        Expanded(child: TextField(controller: _totalCtrl, keyboardType: TextInputType.number,
            style: const TextStyle(color: Color(0xFFF0F4FF)), decoration: _fieldDeco('Total Beds'))),
        const SizedBox(width: 10),
        Expanded(child: TextField(controller: _occupiedCtrl, keyboardType: TextInputType.number,
            style: const TextStyle(color: Color(0xFFF0F4FF)), decoration: _fieldDeco('Occupied Beds'))),
      ]),
      const SizedBox(height: 20),
      _actionRow(context,
        onConfirm: () => widget.onConfirm(BedExtraction(
          totalBeds: int.tryParse(_totalCtrl.text),
          occupiedBeds: int.tryParse(_occupiedCtrl.text),
        )),
        onRetry: widget.onRetry,
      ),
    ]);
  }
}

// ── Attendance review ─────────────────────────────────────────────────────────

class _AttendanceReviewBody extends StatefulWidget {
  const _AttendanceReviewBody({required this.initial, required this.onConfirm, required this.onRetry});
  final AttendanceExtraction initial;
  final ValueChanged<ExtractionResult> onConfirm;
  final VoidCallback onRetry;

  @override
  State<_AttendanceReviewBody> createState() => _AttendanceReviewBodyState();
}

class _AttendanceReviewBodyState extends State<_AttendanceReviewBody> {
  late final TextEditingController _namesCtrl;
  late String _status;

  @override
  void initState() {
    super.initState();
    _namesCtrl = TextEditingController(text: widget.initial.names.join(', '));
    _status = widget.initial.status;
  }

  @override
  void dispose() { _namesCtrl.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    return Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
      _sheetHeader('Review Voice Input'),
      const Text('STAFF NAMES (comma-separated)', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: Color(0xFF4A6080), letterSpacing: 1)),
      const SizedBox(height: 6),
      TextField(controller: _namesCtrl, style: const TextStyle(color: Color(0xFFF0F4FF)),
          decoration: _fieldDeco('Names as spoken')),
      const SizedBox(height: 12),
      SegmentedButton<String>(
        segments: const [
          ButtonSegment(value: 'present', label: Text('Present')),
          ButtonSegment(value: 'absent', label: Text('Absent')),
        ],
        selected: {_status},
        onSelectionChanged: (s) => setState(() => _status = s.first),
        style: ButtonStyle(
          backgroundColor: WidgetStateProperty.resolveWith(
            (s) => s.contains(WidgetState.selected) ? const Color(0xFF00C9A7).withAlpha(40) : const Color(0xFF0F1F3D),
          ),
          foregroundColor: WidgetStateProperty.resolveWith(
            (s) => s.contains(WidgetState.selected) ? const Color(0xFF00C9A7) : const Color(0xFF8BA3CC),
          ),
        ),
      ),
      const SizedBox(height: 20),
      _actionRow(context,
        onConfirm: () => widget.onConfirm(AttendanceExtraction(
          names: _namesCtrl.text.split(',').map((n) => n.trim()).where((n) => n.isNotEmpty).toList(),
          status: _status,
        )),
        onRetry: widget.onRetry,
      ),
    ]);
  }
}

// ── Footfall review ───────────────────────────────────────────────────────────

class _FootfallReviewBody extends StatefulWidget {
  const _FootfallReviewBody({required this.initial, required this.onConfirm, required this.onRetry});
  final FootfallExtraction initial;
  final ValueChanged<ExtractionResult> onConfirm;
  final VoidCallback onRetry;

  @override
  State<_FootfallReviewBody> createState() => _FootfallReviewBodyState();
}

class _FootfallReviewBodyState extends State<_FootfallReviewBody> {
  late final TextEditingController _countCtrl;
  late final TextEditingController _deptCtrl;

  @override
  void initState() {
    super.initState();
    _countCtrl = TextEditingController(text: widget.initial.count.toString());
    _deptCtrl = TextEditingController(text: widget.initial.department ?? '');
  }

  @override
  void dispose() { _countCtrl.dispose(); _deptCtrl.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    return Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
      _sheetHeader('Review Voice Input'),
      Row(children: [
        Expanded(child: TextField(controller: _countCtrl, keyboardType: TextInputType.number,
            style: const TextStyle(color: Color(0xFFF0F4FF)), decoration: _fieldDeco('Patient Count'))),
        const SizedBox(width: 10),
        Expanded(child: TextField(controller: _deptCtrl,
            style: const TextStyle(color: Color(0xFFF0F4FF)), decoration: _fieldDeco('Department (optional)'))),
      ]),
      const SizedBox(height: 20),
      _actionRow(context,
        onConfirm: () => widget.onConfirm(FootfallExtraction(
          count: int.tryParse(_countCtrl.text) ?? widget.initial.count,
          department: _deptCtrl.text.trim().isEmpty ? null : _deptCtrl.text.trim(),
        )),
        onRetry: widget.onRetry,
      ),
    ]);
  }
}
