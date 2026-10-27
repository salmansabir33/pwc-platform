import 'package:flutter/material.dart';
import 'dart:math';
import '../core/contracts.g.dart';

/// Synthetic component contract, not a NativeApi entitlement or live transport.
abstract interface class VerificationGateway {
  Future<VerificationCasePage> cases();
  Future<VerificationCase> create(VerificationCaseInput input, String key);
  Future<VerificationRequirements> requirements(String id);
  Future<VerificationHistoryPage> history(String id);
  Future<EvidencePreparationPage> preparation(String id);
  Future<EvidencePreparation> prepare(
    String id,
    EvidencePreparationInput input,
    String key,
  );
  Future<EvidencePreparation> replace(
    String id,
    String item,
    EvidencePreparationEdit input,
    bool withdraw,
  );
  Future<VerificationCase> change(String id, String command, int revision);
}

class VerificationScreen extends StatefulWidget {
  final VerificationGateway? gateway;
  final String scope;
  final VerificationCaseInput? source;
  final bool urdu;
  final bool review;
  const VerificationScreen({
    super.key,
    this.gateway,
    this.source,
    this.scope = 'unavailable',
    this.urdu = false,
    this.review = false,
  });
  @override
  State<VerificationScreen> createState() => _VerificationScreenState();
}

class _VerificationScreenState extends State<VerificationScreen> {
  List<VerificationCase> _cases = [];
  bool _busy = false;
  bool _error = false;
  int _generation = 0;
  String? _detailId;
  VerificationRequirements? _requirements;
  List<EvidencePreparation> _preparation = [];
  List<VerificationHistory> _history = [];
  String key() {
    // No credentials or storage: cryptographically random UUID retry identity.
    final bytes = List<int>.generate(16, (_) => _random.nextInt(256));
    bytes[6] = (bytes[6] & 15) | 64;
    bytes[8] = (bytes[8] & 63) | 128;
    final hex = bytes.map((b) => b.toRadixString(16).padLeft(2, '0')).join();
    return '${hex.substring(0, 8)}-${hex.substring(8, 12)}-${hex.substring(12, 16)}-${hex.substring(16, 20)}-${hex.substring(20)}';
  }

  final _random = Random.secure();
  String t(String en, String ur) => widget.urdu ? ur : en;
  @override
  void didUpdateWidget(covariant VerificationScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.scope != widget.scope ||
        oldWidget.gateway != widget.gateway ||
        oldWidget.urdu != widget.urdu ||
        oldWidget.review != widget.review ||
        oldWidget.source != widget.source) {
      _generation++;
      _cases = [];
      _busy = false;
      _error = false;
      _detailId = null;
      _requirements = null;
      _preparation = [];
      _history = [];
    }
  }

  @override
  void dispose() {
    _generation++;
    super.dispose();
  }

  Future<void> run(Future<List<VerificationCase>> Function() work) async {
    if (_busy || widget.gateway == null || widget.review) return;
    final generation = _generation;
    setState(() {
      _busy = true;
      _error = false;
    });
    try {
      final value = await work();
      if (mounted && generation == _generation) {
        setState(() {
          _cases = value;
        });
      }
    } catch (_) {
      if (mounted && generation == _generation) {
        setState(() {
          _error = true;
        });
      }
    } finally {
      if (mounted && generation == _generation) {
        setState(() {
          _busy = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final disabled = widget.gateway == null || _busy || widget.review;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text(
          widget.review
              ? 'PWC-01 · Verification review'
              : 'ORG-03 · Verification preparation',
          style: Theme.of(context).textTheme.headlineSmall,
        ),
        Text(
          t(
            'Eligibility and representative mandate are separate. Submission is preparation only, not verification or NGO authority.',
            'اہلیت اور نمائندگی الگ ہیں۔ جمع کرنا صرف تیاری ہے، تصدیق یا اختیار نہیں۔',
          ),
        ),
        Text(
          t(
            'Unavailable: no approved evidence rubric, file intake, scanning, storage, retention or reviewer IAM. No upload or review shortcut.',
            'فائل اور جائزہ غیر دستیاب ہیں۔',
          ),
        ),
        if (widget.gateway == null)
          Text(
            t(
              'Live verification transport is not connected.',
              'براہ راست رابطہ دستیاب نہیں۔',
            ),
          ),
        if (_error)
          Text(
            t(
              'Unavailable or conflicting. Reload current status; no automatic replay.',
              'غیر دستیاب یا متصادم؛ حالت دوبارہ دیکھیں۔',
            ),
          ),
        if (_busy) const LinearProgressIndicator(),
        if (!widget.review)
          FilledButton(
            onPressed: disabled
                ? null
                : () =>
                      run(() async => (await widget.gateway!.cases()).results),
            child: const Text('Load own cases'),
          ),
        if (!widget.review)
          for (final purpose in [
            'organization_eligibility',
            'representative_mandate',
          ])
            TextButton(
              onPressed: disabled || widget.source == null
                  ? null
                  : () => run(
                      () async => [
                        await widget.gateway!.create(
                          VerificationCaseInput.fromJson({
                            ...widget.source!.toJson(),
                            'purpose': purpose,
                          }),
                          key(),
                        ),
                        ..._cases,
                      ],
                    ),
              child: Text(purpose),
            ),
        for (final c in _cases)
          Card(
            child: Column(
              children: [
                Text('${c.purpose} · ${c.track} · ${c.state}'),
                Text('Revision ${c.revision}'),
                TextButton(
                  onPressed: disabled
                      ? null
                      : () {
                          final generation = _generation;
                          final gateway = widget.gateway!;
                          run(() async {
                            final requirements = await gateway.requirements(
                              c.id,
                            );
                            final preparation = await gateway.preparation(c.id);
                            final history = await gateway.history(c.id);
                            if (mounted && generation == _generation) {
                              setState(() {
                                _detailId = c.id;
                                _requirements = requirements;
                                _preparation = preparation.results;
                                _history = history.results;
                              });
                            }
                            return _cases;
                          });
                        },
                  child: const Text('Requirements and history'),
                ),
                TextButton(
                  onPressed: disabled || c.state != 'draft'
                      ? null
                      : () => run(() async {
                          await widget.gateway!.prepare(
                            c.id,
                            EvidencePreparationInput.fromJson({
                              'case_revision': c.revision,
                              'prepared_offline': false,
                            }),
                            key(),
                          );
                          return [];
                        }),
                  child: const Text('Add non-file preparation marker'),
                ),
                if (_detailId == c.id) ...[
                  Text(
                    '${_requirements?.rubricStatus} · ${_requirements?.submissionEffect}',
                  ),
                  for (final marker in _preparation) ...[
                    Text('${marker.state} · ${marker.preparedOffline}'),
                    for (final withdraw in [false, true])
                      TextButton(
                        onPressed:
                            disabled ||
                                c.state != 'draft' ||
                                marker.state != 'planned'
                            ? null
                            : () => run(() async {
                                await widget.gateway!.replace(
                                  c.id,
                                  marker.id,
                                  EvidencePreparationEdit.fromJson({
                                    'case_revision': c.revision,
                                    'revision': marker.revision,
                                    'prepared_offline': !marker.preparedOffline,
                                  }),
                                  withdraw,
                                );
                                return [];
                              }),
                        child: Text(
                          withdraw ? 'Withdraw marker' : 'Replace marker',
                        ),
                      ),
                  ],
                  for (final event in _history)
                    Text('${event.reasonCode} · ${event.revision}'),
                  const Text(
                    'Bounded first page. Reload current cases after marker changes.',
                  ),
                ],
                FilledButton(
                  onPressed: disabled || c.state != 'draft'
                      ? null
                      : () => run(
                          () async => [
                            await widget.gateway!.change(
                              c.id,
                              'submit',
                              c.revision,
                            ),
                          ],
                        ),
                  child: const Text('Submit preparation only'),
                ),
                TextButton(
                  onPressed: disabled || c.state == 'withdrawn'
                      ? null
                      : () => run(
                          () async => [
                            await widget.gateway!.change(
                              c.id,
                              'withdraw',
                              c.revision,
                            ),
                          ],
                        ),
                  child: const Text('Withdraw case'),
                ),
              ],
            ),
          ),
        const Text(
          'Needs-information, replacement evidence, decisions, appeals and re-verification are unavailable pending approved contracts. Native credentials remain native-backed; no verification transport or credential persistence is added.',
        ),
      ],
    );
  }
}
