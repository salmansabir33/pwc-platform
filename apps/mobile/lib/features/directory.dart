import 'package:flutter/material.dart';
import '../core/api.dart';
import '../core/directory_api.dart';
import '../core/contracts.g.dart';
import '../design/controls.dart';

class DirectoryScreen extends StatefulWidget {
  final DirectoryGateway? gateway;
  final bool urdu;
  const DirectoryScreen({super.key, this.gateway, this.urdu = false});
  @override
  State<DirectoryScreen> createState() => _DirectoryScreenState();
}

class _DirectoryScreenState extends State<DirectoryScreen> {
  final _query = TextEditingController();
  final _city = TextEditingController();
  final _rows = <PublicOrganization>[];
  String _classification = '';
  String? _cursor;
  String? _retryCursor;
  bool _busy = false;
  bool _error = false;
  bool _loaded = false;
  bool _profileOpen = false;
  int _generation = 0;
  String t(String en, String ur) => widget.urdu ? ur : en;

  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      if (mounted) load();
    });
  }

  void clear() {
    _generation++;
    widget.gateway?.cancel();
    _rows.clear();
    _cursor = null;
    _retryCursor = null;
    _busy = false;
    _error = false;
    _loaded = false;
  }

  @override
  void didUpdateWidget(covariant DirectoryScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.gateway != widget.gateway || oldWidget.urdu != widget.urdu) {
      oldWidget.gateway?.cancel();
      clear();
      _query.clear();
      _city.clear();
      _classification = '';
      Future.microtask(() {
        if (mounted) load();
      });
    }
  }

  @override
  void dispose() {
    _generation++;
    widget.gateway?.cancel();
    _query.dispose();
    _city.dispose();
    super.dispose();
  }

  Future<void> load([String? cursor]) async {
    final api = widget.gateway;
    if (api == null || _busy) return;
    final ticket = ++_generation;
    setState(() {
      _busy = true;
      _error = false;
      _retryCursor = cursor;
      if (cursor == null) {
        _rows.clear();
        _cursor = null;
      }
    });
    try {
      final page = await api.search(
        _query.text,
        _city.text,
        classification: _classification,
        cursor: cursor,
      );
      if (mounted && ticket == _generation) {
        // Reject cursor cycles; overlapping pages may repeat a public ID.
        if (cursor != null && page.nextCursor == cursor) {
          throw const ApiFailure('INVALID_RESPONSE');
        }
        setState(() {
          final ids = _rows.map((row) => row.id).toSet();
          _rows.addAll(page.results.where((row) => ids.add(row.id)));
          _cursor = page.nextCursor;
          _loaded = true;
        });
      }
    } catch (_) {
      if (mounted && ticket == _generation) {
        setState(() {
          _error = true;
        });
      }
    } finally {
      if (mounted && ticket == _generation) {
        setState(() {
          _busy = false;
        });
      }
    }
  }

  Future<void> profile(String id) async {
    final api = widget.gateway;
    if (api == null || _profileOpen) return;
    _profileOpen = true;
    _generation++;
    api.cancel();
    await Navigator.of(context).push<void>(
      MaterialPageRoute(
        builder: (_) =>
            DirectoryProfileScreen(gateway: api, id: id, urdu: widget.urdu),
      ),
    );
    // Refresh public eligibility after returning, rather than restore a stale card.
    if (mounted) {
      _profileOpen = false;
      setState(clear);
      await load();
    }
  }

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(
        t(
          'NGO registry · public information',
          'تنظیموں کی فہرست · عوامی معلومات',
        ),
        style: Theme.of(context).textTheme.headlineSmall,
      ),
      Notice(
        t(
          'Public information only. Not membership, administrator access or verification consent. New applications and claims remain unavailable.',
          'صرف عوامی معلومات۔ یہ رکنیت یا منتظم کی رسائی نہیں۔ نئی درخواستیں دستیاب نہیں۔',
        ),
      ),
      if (widget.gateway == null)
        Notice(
          t(
            'Public directory transport unavailable. Personal and NGO-private operations are not enabled.',
            'عوامی فہرست کا نیٹ ورک دستیاب نہیں۔ ذاتی اور تنظیم کی نجی کارروائیاں بند ہیں۔',
          ),
        ),
      TextField(
        controller: _query,
        maxLength: 250,
        decoration: InputDecoration(labelText: t('NGO name', 'تنظیم کا نام')),
        onChanged: (_) => setState(clear),
      ),
      TextField(
        controller: _city,
        maxLength: 250,
        decoration: InputDecoration(labelText: t('City', 'شہر')),
        onChanged: (_) => setState(clear),
      ),
      DropdownButtonFormField<String>(
        key: ValueKey('${widget.urdu}:$_classification'),
        initialValue: _classification,
        decoration: InputDecoration(
          labelText: t('Registration classification', 'رجسٹریشن کی قسم'),
        ),
        items: [
          DropdownMenuItem(
            value: '',
            child: Text(t('All classifications', 'تمام اقسام')),
          ),
          DropdownMenuItem(
            value: 'registered',
            child: Text(t('Registered', 'رجسٹرڈ')),
          ),
          DropdownMenuItem(
            value: 'unregistered',
            child: Text(t('Unregistered', 'غیر رجسٹرڈ')),
          ),
        ],
        onChanged: (value) => setState(() {
          clear();
          _classification = value ?? '';
        }),
      ),
      FilledButton(
        onPressed: widget.gateway == null || _busy ? null : () => load(),
        child: Text(t('Search registry', 'فہرست تلاش کریں')),
      ),
      if (_busy) const LinearProgressIndicator(),
      if (_error) ...[
        Notice(
          t(
            'Registry unavailable. Check your connection and retry.',
            'فہرست دستیاب نہیں۔ انٹرنیٹ رابطہ جانچ کر دوبارہ کوشش کریں۔',
          ),
          alert: true,
        ),
        TextButton(
          onPressed: _busy ? null : () => load(_retryCursor),
          child: Text(t('Retry', 'دوبارہ کوشش کریں')),
        ),
      ],
      if (_loaded && !_busy && !_error && _rows.isEmpty)
        Notice(
          _query.text.isEmpty && _city.text.isEmpty && _classification.isEmpty
              ? t(
                  'No public organizations available.',
                  'کوئی عوامی تنظیم دستیاب نہیں۔',
                )
              : t(
                  'No public organizations match.',
                  'کوئی مماثل عوامی تنظیم نہیں۔',
                ),
        ),
      for (final row in _rows)
        Card(
          child: ListTile(
            title: Text(row.name),
            subtitle: Text(row.city),
            trailing: PwcBadge(
              row.classification == 'registered'
                  ? t('Registered', 'رجسٹرڈ')
                  : t('Unregistered', 'غیر رجسٹرڈ'),
            ),
            onTap: () => profile(row.id),
          ),
        ),
      if (_cursor != null && !_error)
        TextButton(
          onPressed: _busy ? null : () => load(_cursor),
          child: Text(t('Load more', 'مزید دکھائیں')),
        ),
    ],
  );
}

class DirectoryProfileScreen extends StatefulWidget {
  final DirectoryGateway gateway;
  final String id;
  final bool urdu;
  const DirectoryProfileScreen({
    super.key,
    required this.gateway,
    required this.id,
    this.urdu = false,
  });
  @override
  State<DirectoryProfileScreen> createState() => _DirectoryProfileScreenState();
}

class _DirectoryProfileScreenState extends State<DirectoryProfileScreen> {
  PublicOrganization? _row;
  bool _busy = true;
  bool _missing = false;
  bool _active = true;
  int _generation = 0;
  String t(String en, String ur) => widget.urdu ? ur : en;
  @override
  void initState() {
    super.initState();
    load();
  }

  @override
  void didUpdateWidget(covariant DirectoryProfileScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.id != widget.id ||
        oldWidget.gateway != widget.gateway ||
        oldWidget.urdu != widget.urdu) {
      oldWidget.gateway.cancel();
      load();
    }
  }

  Future<void> load() async {
    if (!_active) return;
    final ticket = ++_generation;
    setState(() {
      _row = null;
      _busy = true;
      _missing = false;
    });
    try {
      final row = await widget.gateway.detail(widget.id);
      if (mounted && ticket == _generation) {
        setState(() {
          _row = row;
        });
      }
    } catch (error) {
      if (mounted && ticket == _generation) {
        setState(() {
          _missing = error is ApiFailure && error.status == 404;
        });
      }
    } finally {
      if (mounted && ticket == _generation) {
        setState(() {
          _busy = false;
        });
      }
    }
  }

  void _release() {
    if (!_active) return;
    _active = false;
    _generation++;
    widget.gateway.cancel();
  }

  @override
  void dispose() {
    _release();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => PopScope<void>(
    onPopInvokedWithResult: (didPop, _) {
      // Cancel before the directory resumes, not after the exit animation:
      // a late dispose must not cancel the refreshed list's newer request.
      if (didPop) _release();
    },
    child: Scaffold(
      appBar: AppBar(
        title: Text(t('Public NGO profile', 'تنظیم کا عوامی تعارف')),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(24),
          children: [
            if (_busy) const LinearProgressIndicator(),
            if (!_busy && _row == null) ...[
              Notice(
                _missing
                    ? t(
                        'Public profile no longer available.',
                        'عوامی تعارف اب دستیاب نہیں۔',
                      )
                    : t(
                        'Profile unavailable. Check your connection and retry.',
                        'تعارف دستیاب نہیں۔ انٹرنیٹ رابطہ جانچ کر دوبارہ کوشش کریں۔',
                      ),
                alert: true,
              ),
              TextButton(
                onPressed: load,
                child: Text(t('Retry', 'دوبارہ کوشش کریں')),
              ),
            ],
            if (_row != null) ...[
              Text(
                _row!.name,
                style: Theme.of(context).textTheme.headlineSmall,
              ),
              Text('${t('City', 'شہر')}: ${_row!.city}'),
              Text(
                _row!.classification == 'registered'
                    ? t('Registered', 'رجسٹرڈ')
                    : t('Unregistered', 'غیر رجسٹرڈ'),
              ),
              Notice(
                t(
                  'Public information only. No private membership or verification evidence.',
                  'صرف عوامی معلومات۔ نجی رکنیت یا تصدیقی ثبوت شامل نہیں۔',
                ),
              ),
            ],
          ],
        ),
      ),
    ),
  );
}
