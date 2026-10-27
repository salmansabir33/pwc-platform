import 'package:flutter/material.dart';
import '../core/contracts.g.dart';
import '../design/controls.dart';

// Read-only port; deliberately absent from NativeApi's personal operation list.
abstract interface class WorkspaceHistoryGateway {
  Future<WorkspacePage> load(String kind, {String? cursor});
}

class WorkspaceHistoryScreen extends StatefulWidget {
  final WorkspaceHistoryGateway? gateway;
  final String scope;
  final bool urdu;
  const WorkspaceHistoryScreen({
    super.key,
    this.gateway,
    this.scope = 'unavailable',
    this.urdu = false,
  });
  @override
  State<WorkspaceHistoryScreen> createState() => _WorkspaceHistoryScreenState();
}

class _WorkspaceHistoryScreenState extends State<WorkspaceHistoryScreen> {
  WorkspacePage? _page;
  String _kind = 'draft';
  bool _busy = false;
  bool _error = false;
  int _generation = 0;
  String t(String en, String ur) => widget.urdu ? ur : en;
  @override
  void didUpdateWidget(covariant WorkspaceHistoryScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.scope != widget.scope ||
        oldWidget.gateway != widget.gateway ||
        oldWidget.urdu != widget.urdu) {
      _generation++;
      _page = null;
      _busy = false;
      _error = false;
    }
  }

  @override
  void dispose() {
    _generation++;
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
      final page = await api.load(_kind, cursor: cursor);
      if (mounted && ticket == _generation)
        setState(() {
          _page = page;
        });
    } catch (_) {
      if (mounted && ticket == _generation)
        setState(() {
          _error = true;
        });
    } finally {
      if (mounted && ticket == _generation)
        setState(() {
          _busy = false;
        });
    }
  }

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(
        t('My application history', 'میری درخواستوں کی تاریخ'),
        style: Theme.of(context).textTheme.headlineSmall,
      ),
      Notice(
        t(
          'Personal history only. No membership, administration, invitations, finance or grants. New intake remains unavailable.',
          'صرف ذاتی تاریخ۔ انتظامیہ، دعوتیں اور مالی اختیارات دستیاب نہیں۔',
        ),
      ),
      if (widget.gateway == null)
        Notice(
          t(
            'Historical domain transport unavailable pending integration acceptance.',
            'منظوری تک سابقہ درخواستوں کا نیٹ ورک بند ہے۔',
          ),
        ),
      DropdownButtonFormField<String>(
        value: _kind,
        decoration: InputDecoration(
          labelText: t('Application type', 'درخواست کی قسم'),
        ),
        items: [
          DropdownMenuItem(
            value: 'draft',
            child: Text(t('Historical drafts', 'سابقہ مسودے')),
          ),
          DropdownMenuItem(
            value: 'claim',
            child: Text(t('Historical claims', 'سابقہ دعوے')),
          ),
        ],
        onChanged: _busy
            ? null
            : (value) {
                if (value != null)
                  setState(() {
                    _kind = value;
                    _page = null;
                  });
              },
      ),
      FilledButton(
        onPressed: widget.gateway == null || _busy ? null : () => load(),
        child: Text(t('Refresh history', 'تاریخ دوبارہ دیکھیں')),
      ),
      if (_busy) const LinearProgressIndicator(),
      if (_error)
        Notice(
          t(
            'History unavailable or access restricted. No command retried.',
            'تاریخ دستیاب نہیں یا رسائی محدود ہے۔',
          ),
          alert: true,
        ),
      if (_page != null && _page!.results.isEmpty)
        Notice(
          t(
            'No matching historical applications.',
            'کوئی مماثل سابقہ درخواست نہیں۔',
          ),
        ),
      for (final item in _page?.results ?? <WorkspaceApplication>[])
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.name ??
                      t(
                        'Claim target details restricted',
                        'دعوے کی تنظیم کی تفصیل محدود ہے',
                      ),
                ),
                PwcBadge(
                  label: item.state,
                  warning: ['rejected', 'withdrawn'].contains(item.state),
                ),
                Text('${t('Revision', 'نظر ثانی')}: ${item.revision}'),
                for (final c in item.verification)
                  Text(
                    '${c.purpose} · ${c.state}${c.stale ? t(' · Stale source', ' · پرانا ماخذ') : ''}',
                  ),
              ],
            ),
          ),
        ),
      if (_page?.nextCursor != null)
        TextButton(
          onPressed: _busy ? null : () => load(_page!.nextCursor),
          child: Text(t('Next history page', 'تاریخ کا اگلا صفحہ')),
        ),
    ],
  );
}
