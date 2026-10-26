import 'dart:convert';
import 'package:flutter/services.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'contracts.g.dart';

abstract interface class CredentialStore {
  Future<MobileSession?> read();
  Future<void> replace(MobileSession session);
  Future<void> clear();
}

class NativeCredentialStore implements CredentialStore {
  static const _channel = MethodChannel('pwc/privacy');
  static const _key = 'pwc.credentials.v1';
  final FlutterSecureStorage _storage;
  NativeCredentialStore({FlutterSecureStorage? storage}) : _storage = storage ?? const FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
    iOptions: IOSOptions(accessibility: KeychainAccessibility.unlocked_this_device, synchronizable: false),
  );
  Future<String> _installation() async {
    final id = await _channel.invokeMethod<String>('installation');
    if (id == null || id.isEmpty) throw StateError('Native installation binding unavailable');
    return id;
  }
  @override
  Future<MobileSession?> read() async {
    final binding = await _installation();
    final text = await _storage.read(key: _key);
    if (text == null) return null;
    try {
      final data = jsonDecode(text) as Map<String, dynamic>;
      if (data['version'] != 1 || data['installation'] != binding) {
        await clear();
        return null;
      }
      return MobileSession.fromJson(Map<String, Object?>.from(data['session'] as Map));
    } catch (_) { await clear(); rethrow; }
  }
  @override
  Future<void> replace(MobileSession session) async {
    final binding = await _installation();
    final text = jsonEncode({'version': 1, 'installation': binding, 'session': session.toJson()});
    // One native record, never independently persisted access/refresh keys.
    await _storage.write(key: _key, value: text);
    if (await _storage.read(key: _key) != text) {
      await clear();
      throw StateError('Secure storage verification failed');
    }
  }
  @override
  Future<void> clear() async {
    // flutter_secure_storage Android 9.2.4 uses SharedPreferences.apply().
    // A durable, non-secret native generation barrier prevents a crash from
    // resurrecting the old encrypted record even if its deletion is not flushed.
    final barrier = await _channel.invokeMethod<String>('invalidate');
    if (barrier == null || barrier.isEmpty) { throw StateError('Durable invalidation unavailable'); }
    await _storage.delete(key: _key);
  }
}
