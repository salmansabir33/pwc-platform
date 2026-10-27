import 'package:flutter/material.dart';
import '../core/contracts.g.dart';

/// Synthetic component contract, not a NativeApi entitlement or live transport.
abstract interface class VerificationGateway {
  Future<VerificationCasePage> cases();
  Future<VerificationCase> change(String id, String command, int revision);
}

class VerificationScreen extends StatefulWidget {
  final VerificationGateway? gateway;
  final String scope;
  final bool urdu;
  final bool review;
  const VerificationScreen({super.key, this.gateway, this.scope = 'unavailable', this.urdu = false, this.review = false});
  @override
  State<VerificationScreen> createState() => _VerificationScreenState();
}

class _VerificationScreenState extends State<VerificationScreen> {
  List<VerificationCase> _cases = [];
  bool _busy = false;
  bool _error = false;
  int _generation = 0;
  String t(String en, String ur) => widget.urdu ? ur : en;
  @override
  void didUpdateWidget(covariant VerificationScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.scope != widget.scope || oldWidget.gateway != widget.gateway || oldWidget.urdu != widget.urdu || oldWidget.review != widget.review) {
      _generation++; _cases = []; _busy = false; _error = false;
    }
  }
  @override
  void dispose() { _generation++; super.dispose(); }
  Future<void> run(Future<List<VerificationCase>> Function() work) async {
    if (_busy || widget.gateway == null || widget.review) return;
    final generation = _generation;
    setState(() { _busy = true; _error = false; });
    try {
      final value = await work();
      if (mounted && generation == _generation) setState(() { _cases = value; });
    } catch (_) {
      if (mounted && generation == _generation) setState(() { _error = true; });
    } finally {
      if (mounted && generation == _generation) setState(() { _busy = false; });
    }
  }
  @override
  Widget build(BuildContext context) {
    final disabled = widget.gateway == null || _busy || widget.review;
    return ListView(padding: const EdgeInsets.all(16), children: [
      Text(widget.review ? 'PWC-01 · Verification review' : 'ORG-03 · Verification preparation', style: Theme.of(context).textTheme.headlineSmall),
      Text(t('Eligibility and representative mandate are separate. Submission is preparation only, not verification or NGO authority.', 'اہلیت اور نمائندگی الگ ہیں۔ جمع کرنا صرف تیاری ہے، تصدیق یا اختیار نہیں۔')),
      Text(t('Unavailable: no approved evidence rubric, file intake, scanning, storage, retention or reviewer IAM. No upload or review shortcut.', 'فائل اور جائزہ غیر دستیاب ہیں۔')),
      if (widget.gateway == null) Text(t('Live verification transport is not connected.', 'براہ راست رابطہ دستیاب نہیں۔')),
      if (_error) Text(t('Unavailable or conflicting. Reload current status; no automatic replay.', 'غیر دستیاب یا متصادم؛ حالت دوبارہ دیکھیں۔')),
      if (_busy) const LinearProgressIndicator(),
      if (!widget.review) FilledButton(onPressed: disabled ? null : () => run(() async => (await widget.gateway!.cases()).results), child: const Text('Load own cases')),
      for (final c in _cases) Card(child: Column(children: [
        Text('${c.purpose} · ${c.track} · ${c.state}'),
        Text('Revision ${c.revision}'),
        FilledButton(onPressed: disabled || c.state != 'draft' ? null : () => run(() async => [await widget.gateway!.change(c.id, 'submit', c.revision)]), child: const Text('Submit preparation only')),
        TextButton(onPressed: disabled || c.state == 'withdrawn' ? null : () => run(() async => [await widget.gateway!.change(c.id, 'withdraw', c.revision)]), child: const Text('Withdraw case')),
      ])),
      const Text('Needs-information, replacement evidence, decisions, appeals and re-verification are unavailable pending approved contracts. Native credentials remain native-backed; no verification transport or credential persistence is added.'),
    ]);
  }
}
