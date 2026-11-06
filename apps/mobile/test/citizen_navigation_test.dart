import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:pwc_mobile/app/app.dart';
import 'package:pwc_mobile/app/providers.dart';
import 'package:pwc_mobile/app/strings.dart';
import 'package:pwc_mobile/core/contracts.g.dart';
import 'package:pwc_mobile/core/favorites.dart';
import 'package:pwc_mobile/core/session_controller.dart';
import 'directory_test.dart' show FakeDirectory, row, page;
import 'favorites_test.dart' show MemoryFavorites;
import 'fakes.dart';

Future<void> start(
  WidgetTester tester, {
  SessionController? session,
  FakeDirectory? directory,
  FakeDirectory? favoritesApi,
  FavoritesController? favorites,
  bool urdu = false,
}) async {
  final local = favorites ?? FavoritesController(MemoryFavorites());
  if (!local.ready) await local.load();
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        sessionProvider.overrideWith(
          (ref) =>
              session ??
              SessionController(
                FakeApi(),
                MemoryStore(),
                clock: () => DateTime.utc(2026, 10, 26),
              ),
        ),
        favoritesProvider.overrideWith((ref) => local),
        directoryProvider.overrideWith((ref) => directory ?? FakeDirectory()),
        favoritesDirectoryProvider.overrideWith(
          (ref) => favoritesApi ?? FakeDirectory(),
        ),
        urduProvider.overrideWith((ref) => urdu),
      ],
      child: const PwcApp(),
    ),
  );
  await tester.pumpAndSettle();
}

Future<void> select(WidgetTester tester, String label) async {
  await tester.ensureVisible(find.text(label));
  await tester.tap(find.text(label));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets(
    'anonymous launch is public Home with no account calls or invented listings',
    (tester) async {
      final api = FakeApi();
      final session = SessionController(api, MemoryStore());
      await start(tester, session: session);
      expect(find.text('Welcome to PWC'), findsOneWidget);
      for (final label in ['Home', 'Discover', 'Favorites', 'Account']) {
        expect(find.text(label), findsOneWidget);
      }
      expect(find.text('ID-01 · Sign in'), findsNothing);
      expect(find.text('Synthetic NGO'), findsNothing);
      expect(api.calls, isEmpty);
      await tester.pumpWidget(const SizedBox());
    },
  );
  testWidgets(
    'Home Discover profile and Android back preserve directory filters',
    (tester) async {
      final api = FakeDirectory();
      await start(tester, directory: api);
      await select(tester, 'Discover');
      await tester.enterText(find.byType(TextField).first, 'Welfare');
      await select(tester, 'Search registry');
      await select(tester, 'Synthetic NGO');
      expect(find.text('Fresh public name'), findsOneWidget);
      await tester.binding.handlePopRoute();
      await tester.pumpAndSettle();
      expect(
        tester.widget<TextField>(find.byType(TextField).first).controller!.text,
        'Welfare',
      );
      await tester.binding.handlePopRoute();
      await tester.pumpAndSettle();
      expect(find.text('Welcome to PWC'), findsOneWidget);
      await tester.pumpWidget(const SizedBox());
    },
  );
  testWidgets(
    'Home Favorites profile uses existing local IDs and fresh details',
    (tester) async {
      final local = FavoritesController(MemoryFavorites());
      await local.load();
      await local.setFavorite(row['id']!, true);
      final api = FakeDirectory();
      await start(tester, favorites: local, favoritesApi: api);
      await select(tester, 'Favorites');
      await select(tester, 'Fresh public name');
      expect(find.text('Public NGO profile'), findsOneWidget);
      expect(api.details, 2);
      await tester.binding.handlePopRoute();
      await tester.pumpAndSettle();
      expect(find.text('Favorite NGOs'), findsOneWidget);
      await tester.binding.handlePopRoute();
      await tester.pumpAndSettle();
      expect(find.text('Welcome to PWC'), findsOneWidget);
      await tester.pumpWidget(const SizedBox());
    },
  );
  testWidgets(
    'Account signs in, preserves protected navigation, logout goes Home',
    (tester) async {
      final session = SessionController(
        FakeApi(),
        MemoryStore(),
        clock: () => DateTime.utc(2026, 10, 26),
      );
      await start(tester, session: session);
      await select(tester, 'Account');
      expect(find.text('ID-01 · Sign in'), findsOneWidget);
      await session.login('person@example.invalid', 'synthetic-password');
      await tester.pumpAndSettle();
      expect(find.text('ID-02 · Personal profile'), findsOneWidget);
      await select(tester, 'Security');
      expect(find.text('ID-05 · Privacy and security'), findsOneWidget);
      await session.logout();
      await tester.pumpAndSettle();
      expect(find.text('Welcome to PWC'), findsOneWidget);
      expect(find.text(userId), findsNothing);
      await select(tester, 'Account');
      expect(find.text('ID-01 · Sign in'), findsOneWidget);
      await tester.pumpWidget(const SizedBox());
    },
  );
  testWidgets('Android back from root Account returns public Home', (
    tester,
  ) async {
    await start(tester);
    await select(tester, 'Account');
    expect(find.text('ID-01 · Sign in'), findsOneWidget);
    await tester.binding.handlePopRoute();
    await tester.pumpAndSettle();
    expect(find.text('Welcome to PWC'), findsOneWidget);
    await tester.pumpWidget(const SizedBox());
  });
  testWidgets('restored account does not hijack Home or public navigation', (
    tester,
  ) async {
    final store = MemoryStore()..value = MobileSession.fromJson(sessionData());
    final session = SessionController(
      FakeApi(),
      store,
      clock: () => DateTime.utc(2026, 10, 26),
    );
    await start(tester, session: session);
    expect(session.authenticated, isTrue);
    expect(find.text('Welcome to PWC'), findsOneWidget);
    await select(tester, 'Account');
    expect(find.text('ID-02 · Personal profile'), findsOneWidget);
    await select(tester, 'Discover');
    expect(find.text('Synthetic NGO'), findsOneWidget);
    await tester.binding.handlePopRoute();
    await tester.pumpAndSettle();
    expect(find.text('ID-02 · Personal profile'), findsOneWidget);
    await tester.pumpWidget(const SizedBox());
  });
  testWidgets('anonymous protected deep links still deny every private route', (
    tester,
  ) async {
    await start(tester);
    final router = GoRouter.of(tester.element(find.text('Welcome to PWC')));
    for (final path in [
      '/personal',
      '/security',
      '/workspaces',
      '/affiliations',
      '/registry',
      '/verification',
      '/administration',
      '/application-history',
      '/membership-preparation',
    ]) {
      router.go(path);
      await tester.pumpAndSettle();
      expect(find.text('ID-01 · Sign in'), findsOneWidget);
      expect(find.text(userId), findsNothing);
    }
    await tester.pumpWidget(const SizedBox());
  });
  testWidgets('Urdu public labels are RTL and account stays translated', (
    tester,
  ) async {
    await start(tester, urdu: true);
    for (final label in ['Home', 'Discover', 'Favorites', 'Account']) {
      expect(find.text(translated(label, true)), findsOneWidget);
    }
    expect(
      Directionality.of(
        tester.element(find.text(translated('Welcome to PWC', true))),
      ),
      TextDirection.rtl,
    );
    await select(tester, translated('Account', true));
    expect(find.text(translated('ID-01 · Sign in', true)), findsOneWidget);
    await tester.pumpWidget(const SizedBox());
  });
  testWidgets('late directory response after Home reset cannot replace Home', (
    tester,
  ) async {
    final pending = Completer<RegistrySearchPage>();
    final api = FakeDirectory()..pending.add(pending);
    await start(tester, directory: api);
    await tester.tap(find.text('Discover'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 400));
    expect(find.byType(LinearProgressIndicator), findsOneWidget);
    await tester.tap(find.text('Home'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 400));
    pending.complete(page([row]));
    await tester.pumpAndSettle();
    expect(find.text('Welcome to PWC'), findsOneWidget);
    expect(find.text('Synthetic NGO'), findsNothing);
    expect(api.cancellations, greaterThan(0));
    await tester.pumpWidget(const SizedBox());
  });
}
