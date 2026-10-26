import 'dart:convert';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pwc_mobile/core/storage.dart';
import 'package:pwc_mobile/core/contracts.g.dart';
import 'fakes.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const secure = MethodChannel('plugins.it_nomads.com/flutter_secure_storage');
  const privacy = MethodChannel('pwc/privacy');
  final memory = <String, String>{};
  final calls = <MethodCall>[];
  var binding = 'synthetic-install-A';
  var dropWrites = false;
  setUp(() {
    memory.clear();
    calls.clear();
    binding = 'synthetic-install-A';
    dropWrites = false;
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(privacy, (call) async {
          if (call.method == 'invalidate') binding = '$binding-next';
          return binding;
        });
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(secure, (call) async {
          calls.add(call);
          final args = Map<String, dynamic>.from(call.arguments as Map);
          final key = args['key'] as String;
          switch (call.method) {
            case 'read':
              return memory[key];
            case 'write':
              if (!dropWrites) memory[key] = args['value'] as String;
              return null;
            case 'delete':
              memory.remove(key);
              return null;
            default:
              throw StateError('Unexpected native method');
          }
        });
  });
  tearDown(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(privacy, null);
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(secure, null);
  });
  test('native adapter stores a single versioned credential pair', () async {
    final store = NativeCredentialStore();
    await store.replace(MobileSession.fromJson(sessionData()));
    expect(memory.length, 1);
    final data = jsonDecode(memory.values.single) as Map;
    expect(data['version'], 1);
    expect(data['installation'], binding);
    expect((await store.read())!.refreshToken, 'synthetic-refresh-1');
    await store.clear();
    expect(memory, isEmpty);
  });
  test(
    'reinstall binding mismatch wipes retained native credentials',
    () async {
      final store = NativeCredentialStore();
      await store.replace(MobileSession.fromJson(sessionData()));
      binding = 'synthetic-install-B';
      expect(await store.read(), null);
      expect(memory, isEmpty);
    },
  );
  test('corrupt secure record fails closed and deletes it', () async {
    final store = NativeCredentialStore();
    memory['pwc.credentials.v1'] = 'invalid-json';
    await expectLater(store.read(), throwsA(anything));
    expect(memory, isEmpty);
  });
  test('secure write must be read-back verified', () async {
    dropWrites = true;
    final store = NativeCredentialStore();
    await expectLater(
      store.replace(MobileSession.fromJson(sessionData())),
      throwsStateError,
    );
    expect(memory, isEmpty);
  });
  test('unavailable installation binding never writes a credential', () async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(privacy, (call) async => null);
    await expectLater(
      NativeCredentialStore().replace(MobileSession.fromJson(sessionData())),
      throwsStateError,
    );
    expect(memory, isEmpty);
  });
  test(
    'a pre-deletion encrypted snapshot is rejected after durable invalidation',
    () async {
      final store = NativeCredentialStore();
      await store.replace(MobileSession.fromJson(sessionData()));
      final oldRecord = memory.values.single;
      final oldBinding = binding;
      await store.clear();
      expect(binding, isNot(oldBinding));
      // Simulate a native async preference deletion lost at a crash boundary.
      memory['pwc.credentials.v1'] = oldRecord;
      expect(await store.read(), null);
      expect(memory, isEmpty);
    },
  );
}
