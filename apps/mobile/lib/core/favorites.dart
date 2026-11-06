import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

abstract interface class FavoriteStore {
  Future<String?> read();
  Future<void> write(String value);
}

// A separate local record: never credentials, organization fields or server Saved.
class NativeFavoriteStore implements FavoriteStore {
  static const key = 'pwc.public-ngo-favorites.v1';
  final FlutterSecureStorage storage;
  const NativeFavoriteStore({
    this.storage = const FlutterSecureStorage(
      aOptions: AndroidOptions(encryptedSharedPreferences: true),
      iOptions: IOSOptions(
        accessibility: KeychainAccessibility.unlocked_this_device,
        synchronizable: false,
      ),
    ),
  });
  @override
  Future<String?> read() => storage.read(key: key);
  @override
  Future<void> write(String value) => storage.write(key: key, value: value);
}

class FavoritesController extends ChangeNotifier {
  final FavoriteStore store;
  FavoritesController(this.store);
  static const limit = 200;
  Set<String> _ids = {};
  Set<String> get ids => Set.unmodifiable(_ids);
  bool ready = false;
  bool busy = false;
  bool failed = false;
  bool _disposed = false;
  static bool valid(String value) =>
      RegExp(r'^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$').hasMatch(value);
  void _notify() {
    if (!_disposed) notifyListeners();
  }

  Future<void> load() async {
    if (busy) return;
    busy = true;
    failed = false;
    _notify();
    try {
      final raw = await store.read();
      if (raw != null && raw.length > 8000) throw const FormatException();
      final data = raw == null ? <dynamic>[] : jsonDecode(raw);
      if (data is! List ||
          data.length > limit ||
          data.any((id) => id is! String || !valid(id)))
        throw const FormatException();
      _ids = data.cast<String>().toSet();
      ready = true;
    } catch (_) {
      failed = true;
      ready = false;
      _ids = {};
    } finally {
      busy = false;
      _notify();
    }
  }

  Future<void> setFavorite(String id, bool saved) async {
    if (!valid(id) || !ready || busy) return;
    final next = {..._ids};
    saved ? next.add(id) : next.remove(id);
    if (setEquals(next, _ids)) return;
    if (next.length > limit) {
      failed = true;
      _notify();
      return;
    }
    busy = true;
    failed = false;
    _notify();
    try {
      final value = jsonEncode(next.toList()..sort());
      await store.write(value);
      if (await store.read() != value)
        throw StateError('Local storage unavailable');
      _ids = next;
    } catch (_) {
      failed = true;
    } finally {
      busy = false;
      _notify();
    }
  }

  @override
  void dispose() {
    _disposed = true;
    super.dispose();
  }
}
