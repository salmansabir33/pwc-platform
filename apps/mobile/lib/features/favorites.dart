import 'package:flutter/material.dart';
import '../core/contracts.g.dart';
import '../core/directory_api.dart';
import '../core/favorites.dart';
import '../design/controls.dart';
import 'directory.dart';
import 'favorite_button.dart';

class FavoritesScreen extends StatefulWidget {
  final FavoritesController favorites;
  final DirectoryGateway? gateway;
  final bool urdu;
  const FavoritesScreen({
    super.key,
    required this.favorites,
    this.gateway,
    this.urdu = false,
  });
  @override
  State<FavoritesScreen> createState() => _FavoritesScreenState();
}

class _FavoritesScreenState extends State<FavoritesScreen>
    with WidgetsBindingObserver {
  final _rows = <String, PublicOrganization>{};
  Set<String> _seen = {};
  bool _busy = false;
  bool _profile = false;
  bool _active = true;
  int _generation = 0;
  String t(String en, String ur) => widget.urdu ? ur : en;
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    widget.favorites.addListener(changed);
    Future.microtask(() {
      if (mounted) load();
    });
  }

  void changed() {
    if (!mounted) return;
    final ids = widget.favorites.ids;
    if (ids.length != _seen.length || !ids.containsAll(_seen)) {
      if (!_profile) load();
    }
    setState(() {});
  }

  @override
  void didUpdateWidget(covariant FavoritesScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.favorites != widget.favorites ||
        oldWidget.gateway != widget.gateway ||
        oldWidget.urdu != widget.urdu) {
      oldWidget.favorites.removeListener(changed);
      widget.favorites.addListener(changed);
      oldWidget.gateway?.cancel();
      load();
    }
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state != AppLifecycleState.resumed) {
      _generation++;
      widget.gateway?.cancel();
      setState(() {
        _rows.clear();
        _busy = false;
      });
    } else if (!_profile && _active) {
      load();
    }
  }

  Future<void> load() async {
    if (!_active || _profile) return;
    final ticket = ++_generation;
    widget.gateway?.cancel();
    final ids = widget.favorites.ids;
    setState(() {
      _seen = ids;
      _rows.clear();
      _busy = widget.gateway != null && ids.isNotEmpty;
    });
    if (widget.gateway == null) return;
    for (final id in ids) {
      try {
        final row = await widget.gateway!.detail(id);
        if (!mounted || ticket != _generation) return;
        if (row.id == id && widget.favorites.ids.contains(id)) {
          setState(() {
            _rows[id] = row;
          });
        }
      } catch (_) {
        /* Only the local ID remains; never restore cached fields. */
      }
      if (!mounted || ticket != _generation) return;
    }
    if (mounted && ticket == _generation) {
      setState(() {
        _busy = false;
      });
    }
  }

  void release() {
    if (!_active) return;
    _active = false;
    _generation++;
    widget.gateway?.cancel();
  }

  Future<void> profile(String id) async {
    if (_profile || widget.gateway == null) return;
    _profile = true;
    _generation++;
    widget.gateway?.cancel();
    await Navigator.of(context).push<void>(
      MaterialPageRoute(
        builder: (_) => DirectoryProfileScreen(
          gateway: widget.gateway!,
          id: id,
          urdu: widget.urdu,
          favorites: widget.favorites,
        ),
      ),
    );
    if (mounted) {
      _profile = false;
      await load();
    }
  }

  @override
  void dispose() {
    release();
    widget.favorites.removeListener(changed);
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => PopScope<void>(
    onPopInvokedWithResult: (didPop, _) {
      if (didPop) release();
    },
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          t('Favorite NGOs', 'پسندیدہ تنظیمیں'),
          style: Theme.of(context).textTheme.headlineSmall,
        ),
        Notice(
          t(
            'Saved on this device only. No account, membership or server-side Saved. Only public NGO IDs are stored.',
            'صرف اس آلے پر محفوظ۔ اکاؤنٹ، رکنیت یا سرور پر محفوظ فہرست نہیں۔ صرف عوامی تنظیموں کی شناخت محفوظ ہے۔',
          ),
        ),
        if (!widget.favorites.ready || widget.favorites.failed) ...[
          Notice(
            t(
              'Local favorites unavailable. Retry local storage.',
              'مقامی پسندیدہ فہرست دستیاب نہیں۔ دوبارہ کوشش کریں۔',
            ),
            alert: true,
          ),
          TextButton(
            onPressed: widget.favorites.busy ? null : widget.favorites.load,
            child: Text(t('Retry storage', 'مقامی ذخیرہ دوبارہ آزمائیں')),
          ),
        ],
        if (widget.favorites.busy || _busy) const LinearProgressIndicator(),
        if (widget.favorites.ready && widget.favorites.ids.isEmpty)
          Notice(t('No favorite NGOs yet.', 'ابھی کوئی پسندیدہ تنظیم نہیں۔')),
        if (widget.favorites.ids.isNotEmpty) ...[
          if (widget.gateway == null)
            Notice(
              t(
                'Public directory transport unavailable. Local IDs remain saved.',
                'عوامی فہرست کا نیٹ ورک دستیاب نہیں۔ مقامی شناخت محفوظ ہے۔',
              ),
            ),
          TextButton(
            onPressed: _busy ? null : load,
            child: Text(t('Refresh / retry', 'تازہ کریں / دوبارہ کوشش کریں')),
          ),
          for (final id in widget.favorites.ids)
            Card(
              child: ListTile(
                title: Text(
                  _rows[id]?.name ??
                      (_busy
                          ? t('Loading NGO…', 'تنظیم لوڈ ہو رہی ہے…')
                          : t('NGO unavailable', 'تنظیم دستیاب نہیں')),
                ),
                subtitle: Text(_rows[id]?.city ?? id),
                trailing: FavoriteButton(
                  favorites: widget.favorites,
                  id: id,
                  urdu: widget.urdu,
                ),
                onTap: _rows[id] == null ? null : () => profile(id),
              ),
            ),
        ],
      ],
    ),
  );
}
