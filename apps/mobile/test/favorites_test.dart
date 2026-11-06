import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pwc_mobile/core/api.dart';
import 'package:pwc_mobile/core/contracts.g.dart';
import 'package:pwc_mobile/core/favorites.dart';
import 'package:pwc_mobile/features/directory.dart';
import 'package:pwc_mobile/features/favorites.dart';
import 'directory_test.dart' show FakeDirectory, row;

class MemoryFavorites implements FavoriteStore {
  String? value;
  bool fail = false;
  @override
  Future<String?> read() async {
    if (fail) throw StateError('private storage detail');
    return value;
  }

  @override
  Future<void> write(String text) async {
    if (fail) throw StateError('private storage detail');
    value = text;
  }
}

Future<FavoritesController> saved(MemoryFavorites store) async {
  final controller = FavoritesController(store);
  await controller.load();
  await controller.setFavorite(row['id']!, true);
  return controller;
}

Widget favorites(
  FavoritesController controller,
  FakeDirectory? api, {
  bool urdu = false,
}) => MaterialApp(
  home: Scaffold(
    body: SingleChildScrollView(
      child: FavoritesScreen(favorites: controller, gateway: api, urdu: urdu),
    ),
  ),
);

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  test('IDs only, duplicates prevented, restart and removal persist', () async {
    final store = MemoryFavorites();
    final first = await saved(store);
    await first.setFavorite(row['id']!, true);
    expect(jsonDecode(store.value!), [row['id']]);
    expect(store.value, isNot(contains('Synthetic NGO')));
    final restarted = FavoritesController(store);
    await restarted.load();
    expect(restarted.ids, {row['id']});
    await restarted.setFavorite(row['id']!, false);
    final third = FavoritesController(store);
    await third.load();
    expect(third.ids, isEmpty);
    first.dispose();
    restarted.dispose();
    third.dispose();
  });
  test(
    'invalid IDs, malformed records and oversized records fail closed',
    () async {
      for (final value in ['{}', '["private"]', 'x' * 8001]) {
        final store = MemoryFavorites()..value = value;
        final controller = FavoritesController(store);
        await controller.load();
        expect(controller.ready, isFalse);
        expect(controller.ids, isEmpty);
        controller.dispose();
      }
      final store = MemoryFavorites();
      final controller = await saved(store);
      await controller.setFavorite('../private', true);
      expect(controller.ids.length, 1);
      controller.dispose();
    },
  );
  test(
    'write failure does not optimistically remove saved ID and retries',
    () async {
      final store = MemoryFavorites();
      final controller = await saved(store);
      store.fail = true;
      await controller.setFavorite(row['id']!, false);
      expect(controller.failed, isTrue);
      expect(controller.ids, {row['id']});
      store.fail = false;
      await controller.setFavorite(row['id']!, false);
      expect(controller.ids, isEmpty);
      controller.dispose();
    },
  );
  test(
    'native persistence uses isolated key and survives new adapter/controller',
    () async {
      const channel = MethodChannel(
        'plugins.it_nomads.com/flutter_secure_storage',
      );
      final memory = <String, String>{'pwc.credentials.v1': 'untouched'};
      final methods = <String>[];
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(channel, (call) async {
            methods.add(call.method);
            final args = Map<String, dynamic>.from(call.arguments as Map);
            if (call.method == 'write') {
              memory[args['key'] as String] = args['value'] as String;
              return null;
            }
            if (call.method == 'read') return memory[args['key']];
            throw StateError('No deletion or credential operations');
          });
      addTearDown(
        () => TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
            .setMockMethodCallHandler(channel, null),
      );
      final first = FavoritesController(const NativeFavoriteStore());
      await first.load();
      await first.setFavorite(row['id']!, true);
      first.dispose();
      final restarted = FavoritesController(const NativeFavoriteStore());
      await restarted.load();
      expect(restarted.ids, {row['id']});
      expect(memory['pwc.credentials.v1'], 'untouched');
      expect(jsonDecode(memory[NativeFavoriteStore.key]!), [row['id']]);
      expect(methods.toSet(), {'read', 'write'});
      restarted.dispose();
    },
  );
  testWidgets('directory and fresh profile can bookmark and unbookmark', (
    tester,
  ) async {
    final controller = FavoritesController(MemoryFavorites());
    await controller.load();
    final api = FakeDirectory();
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SingleChildScrollView(
            child: DirectoryScreen(gateway: api, favorites: controller),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.byTooltip('Favorite NGO'));
    await tester.tap(find.byTooltip('Favorite NGO'));
    await tester.pumpAndSettle();
    expect(controller.ids, {row['id']});
    await tester.tap(find.text('Synthetic NGO'));
    await tester.pumpAndSettle();
    expect(find.text('Fresh public name'), findsOneWidget);
    await tester.tap(find.byTooltip('Remove favorite'));
    await tester.pumpAndSettle();
    expect(controller.ids, isEmpty);
    await tester.pumpWidget(const SizedBox());
    controller.dispose();
  });
  testWidgets('empty and disabled public transport are explicit', (
    tester,
  ) async {
    final controller = FavoritesController(MemoryFavorites());
    await controller.load();
    await tester.pumpWidget(favorites(controller, null));
    await tester.pumpAndSettle();
    expect(find.text('No favorite NGOs yet.'), findsOneWidget);
    await controller.setFavorite(row['id']!, true);
    await tester.pumpAndSettle();
    expect(find.textContaining('transport unavailable'), findsOneWidget);
    expect(find.text('NGO unavailable'), findsOneWidget);
    await tester.pumpWidget(const SizedBox());
    controller.dispose();
  });
  testWidgets(
    'unavailable NGO never displays previous fields, retry fetches fresh',
    (tester) async {
      final controller = await saved(MemoryFavorites());
      final api = FakeDirectory();
      await tester.pumpWidget(favorites(controller, api));
      await tester.pumpAndSettle();
      expect(find.text('Fresh public name'), findsOneWidget);
      api.missing = true;
      await tester.tap(find.text('Refresh / retry'));
      await tester.pumpAndSettle();
      expect(find.text('Fresh public name'), findsNothing);
      expect(find.text('NGO unavailable'), findsOneWidget);
      api.missing = false;
      await tester.tap(find.text('Refresh / retry'));
      await tester.pumpAndSettle();
      expect(find.text('Fresh public name'), findsOneWidget);
      await tester.pumpWidget(const SizedBox());
      controller.dispose();
    },
  );
  testWidgets('late detail response after removal cannot reintroduce NGO', (
    tester,
  ) async {
    final controller = await saved(MemoryFavorites());
    final pending = Completer<PublicOrganization>();
    final api = FakeDirectory()..pendingDetail = pending;
    await tester.pumpWidget(favorites(controller, api));
    await tester.pump();
    expect(find.byType(LinearProgressIndicator), findsOneWidget);
    await controller.setFavorite(row['id']!, false);
    await tester.pump();
    pending.complete(PublicOrganization.fromJson(row));
    await tester.pumpAndSettle();
    expect(find.text('Synthetic NGO'), findsNothing);
    expect(find.text('No favorite NGOs yet.'), findsOneWidget);
    await tester.pumpWidget(const SizedBox());
    controller.dispose();
  });
  testWidgets('offline details expose only IDs and remain removable in Urdu', (
    tester,
  ) async {
    final controller = await saved(MemoryFavorites());
    final api = FakeDirectory()..fail = true;
    await tester.pumpWidget(favorites(controller, api, urdu: true));
    await tester.pumpAndSettle();
    expect(find.text('تنظیم دستیاب نہیں'), findsOneWidget);
    expect(find.textContaining('private storage detail'), findsNothing);
    await tester.tap(find.byTooltip('پسندیدہ سے ہٹائیں'));
    await tester.pumpAndSettle();
    expect(controller.ids, isEmpty);
    await tester.pumpWidget(const SizedBox());
    controller.dispose();
  });
  testWidgets('late detail after navigation disposal is ignored', (
    tester,
  ) async {
    final controller = await saved(MemoryFavorites());
    final pending = Completer<PublicOrganization>();
    await tester.pumpWidget(
      favorites(controller, FakeDirectory()..pendingDetail = pending),
    );
    await tester.pump();
    await tester.pumpWidget(const MaterialApp(home: Text('Away')));
    pending.completeError(const ApiFailure('NETWORK_UNAVAILABLE'));
    await tester.pumpAndSettle();
    expect(find.text('Away'), findsOneWidget);
    expect(tester.takeException(), isNull);
    controller.dispose();
  });
}
