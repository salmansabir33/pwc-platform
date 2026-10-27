import 'package:flutter/material.dart';
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
  RegistrySearchPage? _page;
  bool _busy = false;
  bool _error = false;
  int _generation = 0;
  String t(String en, String ur) => widget.urdu ? ur : en;
  void clear() {
    _generation++;
    widget.gateway?.cancel();
    _page = null;
    _busy = false;
    _error = false;
  }

  @override
  void didUpdateWidget(covariant DirectoryScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.gateway != widget.gateway || oldWidget.urdu != widget.urdu) {
      oldWidget.gateway?.cancel();
      clear();
      _query.clear();
      _city.clear();
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
      _page = null;
    });
    try {
      final page = await api.search(_query.text, _city.text, cursor: cursor);
      if (mounted && ticket == _generation) {
        setState(() {
          _page = page;
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
      FilledButton(
        onPressed: widget.gateway == null || _busy ? null : () => load(),
        child: Text(t('Search registry', 'فہرست تلاش کریں')),
      ),
      if (_busy) const LinearProgressIndicator(),
      if (_error)
        Notice(
          t(
            'Registry unavailable. Retry without changing any authority.',
            'فہرست دستیاب نہیں۔ دوبارہ کوشش کریں۔',
          ),
          alert: true,
        ),
      if (_page != null && _page!.results.isEmpty)
        Notice(
          t('No public organizations match.', 'کوئی مماثل عوامی تنظیم نہیں۔'),
        ),
      for (final row in _page?.results ?? <PublicOrganization>[])
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(row.name),
                Text(row.city),
                PwcBadge(
                  row.classification == 'registered'
                      ? t('Registered', 'رجسٹرڈ')
                      : t('Unregistered', 'غیر رجسٹرڈ'),
                ),
              ],
            ),
          ),
        ),
      if (_page?.nextCursor != null)
        TextButton(
          onPressed: _busy ? null : () => load(_page!.nextCursor),
          child: Text(t('Next page', 'اگلا صفحہ')),
        ),
    ],
  );
}
