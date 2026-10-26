import 'package:flutter/material.dart';
import '../core/contracts.g.dart';

// Testable claimant-only port, deliberately NOT added to PersonalApi/NativeApi.
// Production transport, real intake and reviewer/authority activation stay gated.
abstract interface class RegistryGateway {
  Future<RegistrySearchPage> search(
    String query,
    String city, {
    String? cursor,
  });
  Future<RegistryDraft> edit(String id, RegistryDraftEdit input);
  Future<RegistryEventPage> history(String kind, String id);
  Future<RegistryDraft> create(RegistryDraftInput input);
  Future<RegistryClaim> claim(String organizationId);
  Future<RegistryDraftPage> drafts({String? cursor});
  Future<RegistryClaimPage> claims({String? cursor});
  Future<RegistryDraft> change(String id, String command, int revision);
  Future<RegistryClaim> withdrawClaim(String id, int revision);
}

class RegistryScreen extends StatefulWidget {
  final RegistryGateway? gateway;
  final String scope;
  final bool urdu;
  const RegistryScreen({
    super.key,
    this.gateway,
    this.scope = 'unavailable',
    this.urdu = false,
  });
  @override
  State<RegistryScreen> createState() => _RegistryScreenState();
}

class _RegistryScreenState extends State<RegistryScreen> {
  final _query = TextEditingController();
  final _name = TextEditingController();
  final _city = TextEditingController();
  final _legal = TextEditingController();
  final _aliases = TextEditingController();
  final _jurisdiction = TextEditingController();
  final _email = TextEditingController();
  final _phone = TextEditingController();
  RegistryDraft? _editing;
  String? _hitCursor, _draftCursor, _claimCursor;
  List<RegistryEvent> _history = [];
  String _classification = 'unregistered';
  List<PublicOrganization> _hits = [];
  List<RegistryDraft> _drafts = [];
  List<RegistryClaim> _claims = [];
  bool _busy = false;
  String _message = '';
  int _generation = 0;
  String t(String en, String ur) => widget.urdu ? ur : en;
  @override
  void didUpdateWidget(covariant RegistryScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.scope != widget.scope ||
        oldWidget.gateway != widget.gateway ||
        oldWidget.urdu != widget.urdu) {
      _generation++;
      _hits = [];
      _drafts = [];
      _claims = [];
      _message = '';
      _busy = false;
      _name.clear();
      _city.clear();
      _query.clear();
      _legal.clear();
      _aliases.clear();
      _jurisdiction.clear();
      _email.clear();
      _phone.clear();
      _editing = null;
      _history = [];
      _hitCursor = null;
      _draftCursor = null;
      _claimCursor = null;
    }
  }

  @override
  void dispose() {
    _generation++;
    _query.dispose();
    _name.dispose();
    _city.dispose();
    _legal.dispose();
    _aliases.dispose();
    _jurisdiction.dispose();
    _email.dispose();
    _phone.dispose();
    super.dispose();
  }

  Future<void> run(Future<void> Function(int) work) async {
    if (_busy || widget.gateway == null) return;
    final generation = _generation;
    setState(() {
      _busy = true;
      _message = '';
    });
    try {
      await work(generation);
    } catch (_) {
      if (mounted && generation == _generation) {
        setState(() {
          _message = t(
            'Request unavailable or conflicting. Reload status before retrying. No automatic replay.',
            'درخواست دستیاب نہیں۔ دوبارہ کوشش سے پہلے حالت دیکھیں۔',
          );
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

  void apply(int generation, VoidCallback work) {
    if (mounted && generation == _generation) setState(work);
  }

  @override
  Widget build(BuildContext context) {
    final enabled = widget.gateway != null && !_busy;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          t('ORG-01 · Find or claim an NGO', 'ORG-01 · تنظیم تلاش کریں'),
          style: Theme.of(context).textTheme.headlineSmall,
        ),
        Text(
          t(
            'Claims do not establish ownership, verification or NGO access. Synthetic review only.',
            'درخواست ملکیت، تصدیق یا رسائی نہیں۔ صرف فرضی جائزہ۔',
          ),
        ),
        if (widget.gateway == null)
          Text(
            t(
              'Unavailable: registry transport and real intake are not activated.',
              'غیر دستیاب: نیٹ ورک اور حقیقی درخواستیں بند ہیں۔',
            ),
          ),
        if (_busy) const LinearProgressIndicator(),
        if (_message.isNotEmpty)
          Semantics(liveRegion: true, child: Text(_message)),
        TextField(
          controller: _query,
          enabled: enabled,
          maxLength: 250,
          decoration: InputDecoration(
            labelText: t('Organization search', 'تنظیم کی تلاش'),
          ),
        ),
        TextField(
          controller: _city,
          enabled: enabled,
          maxLength: 100,
          decoration: InputDecoration(labelText: t('City', 'شہر')),
        ),
        FilledButton(
          onPressed: !enabled
              ? null
              : () => run((g) async {
                  if (_query.text.trim().length < 2) {
                    throw const FormatException();
                  }
                  final page = await widget.gateway!.search(
                    _query.text,
                    _city.text,
                  );
                  apply(g, () {
                    _hits = page.results;
                    _hitCursor = page.nextCursor;
                  });
                }),
          child: Text(t('Search', 'تلاش')),
        ),
        if (_hits.isNotEmpty)
          Text(
            t(
              'Potential duplicates only. No automatic merging or control transfer.',
              'ممکنہ مماثلت؛ خودکار انضمام یا اختیار کی منتقلی نہیں۔',
            ),
          ),
        for (final hit in _hits)
          ListTile(
            title: Text(hit.name),
            subtitle: Text(hit.city),
            trailing: TextButton(
              onPressed: !enabled
                  ? null
                  : () => run((g) async {
                      final result = await widget.gateway!.claim(hit.id);
                      apply(g, () {
                        _claims = [
                          ..._claims.where((c) => c.id != result.id),
                          result,
                        ];
                      });
                    }),
              child: Text(t('Request claim', 'درخواست جمع کریں')),
            ),
          ),
        if (_hitCursor != null)
          TextButton(
            onPressed: !enabled
                ? null
                : () => run((g) async {
                    final page = await widget.gateway!.search(
                      _query.text,
                      _city.text,
                      cursor: _hitCursor,
                    );
                    apply(g, () {
                      _hits = [..._hits, ...page.results];
                      _hitCursor = page.nextCursor;
                    });
                  }),
            child: Text(t('More results', 'مزید نتائج')),
          ),
        Text(
          t('ORG-02 · Provisional draft', 'ORG-02 · عارضی مسودہ'),
          style: Theme.of(context).textTheme.titleLarge,
        ),
        TextField(
          controller: _name,
          enabled: enabled,
          maxLength: 250,
          decoration: InputDecoration(labelText: t('Display name', 'نام')),
        ),
        for (final entry in <String, TextEditingController>{
          'Legal name': _legal,
          'Aliases (comma separated)': _aliases,
          'Jurisdiction': _jurisdiction,
          'Organization contact email': _email,
          'Organization contact phone': _phone,
        }.entries)
          TextField(
            controller: entry.value,
            enabled: enabled,
            maxLength: entry.key.startsWith('Aliases')
                ? 1254
                : entry.key.contains('email')
                ? 254
                : entry.key.contains('phone')
                ? 40
                : entry.key == 'Jurisdiction'
                ? 100
                : 250,
            decoration: InputDecoration(labelText: entry.key),
          ),
        DropdownButton<String>(
          value: _classification,
          onChanged: !enabled
              ? null
              : (v) => setState(() {
                  _classification = v!;
                }),
          items: [
            DropdownMenuItem(
              value: 'unregistered',
              child: Text(
                t('Informal welfare organization', 'غیر رجسٹرڈ تنظیم'),
              ),
            ),
            DropdownMenuItem(
              value: 'registered',
              child: Text(
                t('Registered (self-declared)', 'رجسٹرڈ (ذاتی دعویٰ)'),
              ),
            ),
          ],
        ),
        FilledButton(
          onPressed: !enabled
              ? null
              : () => run((g) async {
                  final values = <String, Object?>{
                    'name': _name.text,
                    'city': _city.text,
                    'classification': _classification,
                    'legal_name': _legal.text,
                    'aliases': _aliases.text
                        .split(',')
                        .map((v) => v.trim())
                        .where((v) => v.isNotEmpty)
                        .toList(),
                    'jurisdiction': _jurisdiction.text,
                    'contact_email': _email.text,
                    'contact_phone': _phone.text,
                  };
                  final editing = _editing;
                  final result = editing == null
                      ? await widget.gateway!.create(
                          RegistryDraftInput.fromJson(values),
                        )
                      : await widget.gateway!.edit(
                          editing.id,
                          RegistryDraftEdit.fromJson({
                            ...values,
                            'revision': editing.revision,
                          }),
                        );
                  apply(g, () {
                    _drafts = [
                      ..._drafts.where((d) => d.id != result.id),
                      result,
                    ];
                    _name.clear();
                    _editing = null;
                  });
                }),
          child: Text(t('Save private draft', 'نجی مسودہ محفوظ کریں')),
        ),
        TextButton(
          onPressed: !enabled
              ? null
              : () => run((g) async {
                  final drafts = await widget.gateway!.drafts();
                  if (!mounted || g != _generation) return;
                  final claims = await widget.gateway!.claims();
                  apply(g, () {
                    _drafts = drafts.results;
                    _claims = claims.results;
                    _draftCursor = drafts.nextCursor;
                    _claimCursor = claims.nextCursor;
                  });
                }),
          child: Text(t('Reload own status', 'اپنی حالت دیکھیں')),
        ),
        for (final draft in _drafts)
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('${draft.name} · ${draft.state} · v${draft.revision}'),
              if (draft.state == 'draft')
                TextButton(
                  onPressed: !enabled
                      ? null
                      : () => setState(() {
                          _editing = draft;
                          _name.text = draft.name;
                          _city.text = draft.city;
                          _classification = draft.classification;
                          _legal.text = draft.legalName;
                          _aliases.text = draft.aliases.join(', ');
                          _jurisdiction.text = draft.jurisdiction;
                          _email.text = draft.contactEmail;
                          _phone.text = draft.contactPhone;
                        }),
                  child: Text(t('Edit own draft', 'اپنا مسودہ بدلیں')),
                ),
              TextButton(
                onPressed: !enabled
                    ? null
                    : () => run((g) async {
                        final page = await widget.gateway!.history(
                          'draft',
                          draft.id,
                        );
                        apply(g, () {
                          _history = page.results;
                        });
                      }),
                child: Text(t('Draft history', 'مسودے کی تاریخ')),
              ),
              if (draft.state == 'draft')
                TextButton(
                  onPressed: !enabled
                      ? null
                      : () => run((g) async {
                          final result = await widget.gateway!.change(
                            draft.id,
                            'submit',
                            draft.revision,
                          );
                          apply(g, () {
                            _drafts = _drafts
                                .map((d) => d.id == result.id ? result : d)
                                .toList();
                          });
                        }),
                  child: Text(
                    t(
                      'Submit for future review',
                      'مستقبل کے جائزے کے لیے جمع کریں',
                    ),
                  ),
                ),
              if (draft.state != 'withdrawn')
                TextButton(
                  onPressed: !enabled
                      ? null
                      : () => run((g) async {
                          final result = await widget.gateway!.change(
                            draft.id,
                            'withdraw',
                            draft.revision,
                          );
                          apply(g, () {
                            _drafts = _drafts
                                .map((d) => d.id == result.id ? result : d)
                                .toList();
                          });
                        }),
                  child: Text(t('Withdraw draft', 'مسودہ واپس لیں')),
                ),
            ],
          ),
        for (final claim in _claims)
          Column(
            children: [
              Text('${claim.id} · ${claim.state}'),
              TextButton(
                onPressed: !enabled
                    ? null
                    : () => run((g) async {
                        final page = await widget.gateway!.history(
                          'claim',
                          claim.id,
                        );
                        apply(g, () {
                          _history = page.results;
                        });
                      }),
                child: Text(t('Claim history', 'درخواست کی تاریخ')),
              ),
              if (['pending', 'needs_information'].contains(claim.state))
                TextButton(
                  onPressed: !enabled
                      ? null
                      : () => run((g) async {
                          final result = await widget.gateway!.withdrawClaim(
                            claim.id,
                            claim.revision,
                          );
                          apply(g, () {
                            _claims = _claims
                                .map((c) => c.id == result.id ? result : c)
                                .toList();
                          });
                        }),
                  child: Text(t('Withdraw claim', 'درخواست واپس لیں')),
                ),
            ],
          ),
        if (_draftCursor != null)
          TextButton(
            onPressed: !enabled
                ? null
                : () => run((g) async {
                    final page = await widget.gateway!.drafts(
                      cursor: _draftCursor,
                    );
                    apply(g, () {
                      _drafts = [..._drafts, ...page.results];
                      _draftCursor = page.nextCursor;
                    });
                  }),
            child: Text(t('More own drafts', 'مزید مسودے')),
          ),
        if (_claimCursor != null)
          TextButton(
            onPressed: !enabled
                ? null
                : () => run((g) async {
                    final page = await widget.gateway!.claims(
                      cursor: _claimCursor,
                    );
                    apply(g, () {
                      _claims = [..._claims, ...page.results];
                      _claimCursor = page.nextCursor;
                    });
                  }),
            child: Text(t('More own claims', 'مزید درخواستیں')),
          ),
        for (final event in _history)
          Text('${event.action} · v${event.revision}'),
        Text(
          t(
            'Evidence, review, verification, administrators, rosters and finance are unavailable.',
            'ثبوت، جائزہ، تصدیق، انتظامیہ، فہرستیں اور مالیات دستیاب نہیں۔',
          ),
        ),
      ],
    );
  }
}
