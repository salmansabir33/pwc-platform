import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:pwc_mobile/core/directory_api.dart';
import 'package:pwc_mobile/core/contracts.g.dart';
import 'package:pwc_mobile/core/api.dart';
import 'package:pwc_mobile/features/directory.dart';

const row = {
  'id': '00000000-0000-4000-8000-000000000001',
  'name': 'Synthetic NGO',
  'city': 'City',
  'classification': 'registered',
};
final second = {
  ...row,
  'id': '00000000-0000-4000-8000-000000000002',
  'name': 'Second NGO',
};
RegistrySearchPage page(List<Map<String, Object?>> rows, [String? cursor]) =>
    RegistrySearchPage.fromJson({'results': rows, 'next_cursor': cursor});
http.Response jsonReply(Object body, [int status = 200]) => http.Response(
  jsonEncode(body),
  status,
  headers: {'content-type': 'application/json; charset=utf-8'},
);

class FakeDirectory implements DirectoryGateway {
  final calls = <Map<String, String?>>[];
  final pending = <Completer<RegistrySearchPage>>[];
  int cancellations = 0;
  int details = 0;
  bool fail = false;
  bool failMore = false;
  bool empty = false;
  bool paginate = false;
  bool missing = false;
  Completer<PublicOrganization>? pendingDetail;
  @override
  void cancel() {
    cancellations++;
  }

  @override
  Future<PublicOrganization> detail(String id) async {
    details++;
    if (pendingDetail != null) return pendingDetail!.future;
    if (missing) throw const ApiFailure('DIRECTORY_UNAVAILABLE', 404);
    if (fail) throw StateError('private backend note');
    return PublicOrganization.fromJson({
      ...row,
      'id': id,
      'name': 'Fresh public name',
    });
  }

  @override
  Future<RegistrySearchPage> search(
    String q,
    String city, {
    String classification = '',
    String? cursor,
  }) async {
    calls.add({
      'q': q,
      'city': city,
      'classification': classification,
      'cursor': cursor,
    });
    if (pending.isNotEmpty) return pending.removeAt(0).future;
    if (fail || (cursor != null && failMore)) {
      throw StateError('private backend note');
    }
    if (empty) return page([]);
    if (cursor != null) return page([row, second]);
    return page([row], paginate ? 'cursor-one' : null);
  }
}

Widget screen({DirectoryGateway? gateway, bool urdu = false}) => MaterialApp(
  locale: Locale(urdu ? 'ur' : 'en'),
  supportedLocales: const [Locale('en'), Locale('ur')],
  localizationsDelegates: GlobalMaterialLocalizations.delegates,
  home: Scaffold(
    body: SingleChildScrollView(
      child: DirectoryScreen(gateway: gateway, urdu: urdu),
    ),
  ),
);
Future<void> tap(WidgetTester tester, String label) async {
  final finder = find.text(label);
  await tester.ensureVisible(finder);
  await tester.tap(finder);
  await tester.pumpAndSettle();
}

void main() {
  test(
    'public search uses exact generated GET and only supported filters',
    () async {
      final api = NativeDirectoryGateway(
        'https://api.example.invalid',
        factory: () => MockClient((request) async {
          expect(
            request.url.toString(),
            'https://api.example.invalid/api/v1/directory/?q=Synthetic&city=City&classification=registered&cursor=next',
          );
          expect(request.method, 'GET');
          expect(request.headers.containsKey('authorization'), isFalse);
          expect(request.headers.containsKey('cookie'), isFalse);
          expect(request.followRedirects, isFalse);
          return jsonReply({
            'results': [row],
            'next_cursor': null,
          });
        }),
      );
      expect(
        (await api.search(
          'Synthetic',
          'City',
          classification: 'registered',
          cursor: 'next',
        )).results.single.name,
        'Synthetic NGO',
      );
      api.dispose();
    },
  );
  test(
    'detail uses exact public UUID route and rejects mismatched identity or private fields',
    () async {
      for (final body in [
        row,
        {...row, 'email': 'private'},
        {...row, 'id': second['id']},
      ]) {
        final api = NativeDirectoryGateway(
          'https://api.example.invalid',
          factory: () => MockClient((request) async {
            expect(
              request.url.toString(),
              'https://api.example.invalid/api/v1/organizations/${row['id']}/',
            );
            expect(request.headers.containsKey('authorization'), isFalse);
            expect(request.headers.containsKey('cookie'), isFalse);
            expect(request.followRedirects, isFalse);
            return jsonReply(body);
          }),
        );
        if (identical(body, row)) {
          expect((await api.detail(row['id']!)).name, 'Synthetic NGO');
        } else {
          await expectLater(api.detail(row['id']!), throwsA(isA<ApiFailure>()));
        }
        api.dispose();
      }
    },
  );
  test(
    'invalid origins and unsupported filters/IDs never request arbitrary resources',
    () async {
      for (final origin in [
        'http://api.example.invalid',
        'https://[',
        'https://user:pass@api.example.invalid',
        'https://api.example.invalid/path',
        'https://api.example.invalid?q=x',
      ]) {
        expect(
          () => NativeDirectoryGateway(origin),
          throwsA(isA<ApiFailure>()),
        );
      }
      final api = NativeDirectoryGateway(
        'https://api.example.invalid',
        factory: () => throw StateError('Must not request'),
      );
      await expectLater(
        api.search('', '', classification: 'private'),
        throwsA(isA<ApiFailure>()),
      );
      await expectLater(api.detail('../private'), throwsA(isA<ApiFailure>()));
      api.dispose();
    },
  );
  test(
    'invalid content, redirects, oversized bodies and duplicate rows fail closed',
    () async {
      for (final response in [
        http.Response('private', 302),
        http.Response('private', 404),
        http.Response(
          '<html>private</html>',
          200,
          headers: {'content-type': 'text/html'},
        ),
        http.Response(
          '{}',
          200,
          headers: {'content-type': 'application/json-invalid'},
        ),
        jsonReply({
          'results': [
            {...row, 'evidence': 'private'},
          ],
          'next_cursor': null,
        }),
        jsonReply({
          'results': [row, row],
          'next_cursor': null,
        }),
        jsonReply({
          'results': [row],
          'next_cursor': 123,
        }),
        jsonReply('x' * 131073),
      ]) {
        final api = NativeDirectoryGateway(
          'https://api.example.invalid',
          factory: () => MockClient((_) async => response),
        );
        await expectLater(api.search('', ''), throwsA(isA<ApiFailure>()));
        api.dispose();
      }
    },
  );
  test(
    'cancellation rejects late responses without canceling newer results',
    () async {
      final old = Completer<http.Response>();
      int count = 0;
      final api = NativeDirectoryGateway(
        'https://api.example.invalid',
        factory: () => MockClient((_) async {
          if (count++ == 0) return old.future;
          return jsonReply({
            'results': [second],
            'next_cursor': null,
          });
        }),
      );
      final first = api.search('old', '');
      final rejected = expectLater(first, throwsA(isA<ApiFailure>()));
      await Future<void>.delayed(Duration.zero);
      api.cancel();
      expect((await api.search('new', '')).results.single.name, 'Second NGO');
      old.complete(
        jsonReply({
          'results': [row],
          'next_cursor': null,
        }),
      );
      await rejected;
      api.dispose();
    },
  );

  testWidgets('opt-in auto-load and default disabled transport', (
    tester,
  ) async {
    await tester.pumpWidget(screen());
    await tester.pumpAndSettle();
    expect(
      tester.widget<FilledButton>(find.byType(FilledButton)).onPressed,
      isNull,
    );
    expect(find.textContaining('transport unavailable'), findsOneWidget);
    final api = FakeDirectory();
    await tester.pumpWidget(screen(gateway: api));
    await tester.pumpAndSettle();
    expect(find.text('Synthetic NGO'), findsOneWidget);
    expect(api.calls.length, 1);
    expect(find.textContaining('Not membership'), findsOneWidget);
  });
  testWidgets(
    'search and classification reset stale rows and use actual filters',
    (tester) async {
      final api = FakeDirectory();
      await tester.pumpWidget(screen(gateway: api));
      await tester.pumpAndSettle();
      await tester.enterText(find.byType(TextField).first, 'Welfare');
      await tester.enterText(find.byType(TextField).last, 'Faisalabad');
      await tester.pump();
      expect(find.text('Synthetic NGO'), findsNothing);
      await tester.ensureVisible(find.byType(DropdownButtonFormField<String>));
      await tester.tap(find.byType(DropdownButtonFormField<String>));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Unregistered').last);
      await tester.pumpAndSettle();
      await tap(tester, 'Search registry');
      expect(api.calls.last, {
        'q': 'Welfare',
        'city': 'Faisalabad',
        'classification': 'unregistered',
        'cursor': null,
      });
    },
  );
  testWidgets(
    'load more appends deduplicated rows and retry preserves cursor and first page',
    (tester) async {
      final api = FakeDirectory()
        ..paginate = true
        ..failMore = true;
      await tester.pumpWidget(screen(gateway: api));
      await tester.pumpAndSettle();
      await tap(tester, 'Load more');
      expect(find.text('Synthetic NGO'), findsOneWidget);
      expect(find.textContaining('private backend note'), findsNothing);
      expect(api.calls.last['cursor'], 'cursor-one');
      api.failMore = false;
      await tap(tester, 'Retry');
      expect(api.calls.last['cursor'], 'cursor-one');
      expect(find.text('Synthetic NGO'), findsOneWidget);
      expect(find.text('Second NGO'), findsOneWidget);
      expect(find.text('Load more'), findsNothing);
    },
  );
  testWidgets(
    'empty and no-match states distinguish loading from an empty response',
    (tester) async {
      final api = FakeDirectory()..empty = true;
      await tester.pumpWidget(screen(gateway: api));
      await tester.pumpAndSettle();
      expect(find.text('No public organizations available.'), findsOneWidget);
      await tester.enterText(find.byType(TextField).first, 'Missing');
      await tap(tester, 'Search registry');
      expect(find.text('No public organizations match.'), findsOneWidget);
    },
  );
  testWidgets('network failure retries and never renders raw diagnostic', (
    tester,
  ) async {
    final api = FakeDirectory()..fail = true;
    await tester.pumpWidget(screen(gateway: api));
    await tester.pumpAndSettle();
    expect(find.textContaining('Registry unavailable'), findsOneWidget);
    expect(find.textContaining('private backend note'), findsNothing);
    api.fail = false;
    await tap(tester, 'Retry');
    expect(find.text('Synthetic NGO'), findsOneWidget);
  });
  testWidgets('rapid searches isolate late responses', (tester) async {
    final old = Completer<RegistrySearchPage>();
    final current = Completer<RegistrySearchPage>();
    final api = FakeDirectory()..pending.addAll([old, current]);
    await tester.pumpWidget(screen(gateway: api));
    await tester.pump();
    expect(find.byType(LinearProgressIndicator), findsOneWidget);
    await tester.enterText(find.byType(TextField).first, 'new');
    await tester.pump(); // Rebuild the button after canceling the old search.
    await tester.tap(find.text('Search registry'));
    await tester.pump();
    expect(api.calls.length, 2);
    expect(api.calls.last['q'], 'new');
    old.complete(page([row]));
    await tester.pump();
    expect(find.text('Synthetic NGO'), findsNothing);
    current.complete(page([second]));
    await tester.pumpAndSettle();
    expect(find.text('Second NGO'), findsOneWidget);
  });
  testWidgets(
    'profile fetches fresh public fields, returns and refreshes the list',
    (tester) async {
      final api = FakeDirectory();
      await tester.pumpWidget(screen(gateway: api));
      await tester.pumpAndSettle();
      await tap(tester, 'Synthetic NGO');
      expect(find.text('Public NGO profile'), findsOneWidget);
      expect(find.text('Fresh public name'), findsOneWidget);
      expect(api.details, 1);
      await tester.pageBack();
      await tester.pumpAndSettle();
      expect(api.calls.length, 2);
      expect(find.text('Synthetic NGO'), findsOneWidget);
    },
  );
  testWidgets('withdrawn detail never falls back to list data', (tester) async {
    final api = FakeDirectory()..missing = true;
    await tester.pumpWidget(screen(gateway: api));
    await tester.pumpAndSettle();
    await tap(tester, 'Synthetic NGO');
    expect(find.text('Public profile no longer available.'), findsOneWidget);
    expect(find.text('Synthetic NGO'), findsNothing);
    api.missing = false;
    await tap(tester, 'Retry');
    expect(find.text('Fresh public name'), findsOneWidget);
  });
  testWidgets('late detail completion after back cannot replace directory', (
    tester,
  ) async {
    final api = FakeDirectory()
      ..pendingDetail = Completer<PublicOrganization>();
    await tester.pumpWidget(screen(gateway: api));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Synthetic NGO'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 400));
    await tester.pageBack();
    await tester.pumpAndSettle();
    api.pendingDetail!.complete(
      PublicOrganization.fromJson({...row, 'name': 'Late profile'}),
    );
    await tester.pumpAndSettle();
    expect(find.text('Late profile'), findsNothing);
    expect(find.text('Synthetic NGO'), findsOneWidget);
  });
  testWidgets('locale reset isolates old search and uses Urdu presentation', (
    tester,
  ) async {
    final old = Completer<RegistrySearchPage>();
    final api = FakeDirectory()
      ..pending.add(old)
      ..empty = true;
    await tester.pumpWidget(screen(gateway: api));
    await tester.pump();
    await tester.pumpWidget(screen(gateway: api, urdu: true));
    old.complete(page([row]));
    await tester.pumpAndSettle();
    expect(find.text('Synthetic NGO'), findsNothing);
    expect(find.text('کوئی عوامی تنظیم دستیاب نہیں۔'), findsOneWidget);
    expect(find.text('رجسٹریشن کی قسم'), findsOneWidget);
  });
  testWidgets(
    'profile network failure is retryable and hides diagnostic text',
    (tester) async {
      final api = FakeDirectory();
      await tester.pumpWidget(screen(gateway: api));
      await tester.pumpAndSettle();
      api.fail = true;
      await tap(tester, 'Synthetic NGO');
      expect(find.textContaining('Profile unavailable'), findsOneWidget);
      expect(find.textContaining('private backend note'), findsNothing);
      expect(find.text('Synthetic NGO'), findsNothing);
      api.fail = false;
      await tap(tester, 'Retry');
      expect(find.text('Fresh public name'), findsOneWidget);
    },
  );

  testWidgets('gateway replacement discards old pending results', (
    tester,
  ) async {
    final old = Completer<RegistrySearchPage>();
    final previous = FakeDirectory()..pending.add(old);
    final current = FakeDirectory()..empty = true;
    await tester.pumpWidget(screen(gateway: previous));
    await tester.pump();
    await tester.pumpWidget(screen(gateway: current));
    old.complete(page([row]));
    await tester.pumpAndSettle();
    expect(find.text('Synthetic NGO'), findsNothing);
    expect(find.text('No public organizations available.'), findsOneWidget);
    expect(previous.cancellations, greaterThan(0));
  });

  testWidgets('Urdu directory and profile fit narrow RTL layouts', (
    tester,
  ) async {
    tester.view.devicePixelRatio = 1;
    tester.view.physicalSize = const Size(320, 800);
    addTearDown(tester.view.resetDevicePixelRatio);
    addTearDown(tester.view.resetPhysicalSize);
    final api = FakeDirectory();
    await tester.pumpWidget(screen(gateway: api, urdu: true));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    expect(
      Directionality.of(tester.element(find.text('فہرست تلاش کریں'))),
      TextDirection.rtl,
    );
    await tap(tester, 'Synthetic NGO');
    expect(find.text('تنظیم کا عوامی تعارف'), findsOneWidget);
    expect(find.text('رجسٹرڈ'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
  testWidgets(
    'profile exit animation cannot cancel the returning list request',
    (tester) async {
      final returning = Completer<http.Response>();
      var listCalls = 0;
      final api = NativeDirectoryGateway(
        'https://api.example.invalid',
        factory: () => MockClient((request) async {
          if (request.url.path == '/api/v1/directory/') {
            if (listCalls++ == 0) {
              return jsonReply({
                'results': [row],
                'next_cursor': null,
              });
            }
            return returning.future;
          }
          return jsonReply({...row, 'name': 'Fresh public name'});
        }),
      );
      await tester.pumpWidget(screen(gateway: api));
      await tester.pumpAndSettle();
      await tap(tester, 'Synthetic NGO');
      await tester.pageBack();
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 500));
      returning.complete(
        jsonReply({
          'results': [second],
          'next_cursor': null,
        }),
      );
      await tester.pumpAndSettle();
      expect(find.text('Second NGO'), findsOneWidget);
      expect(find.textContaining('Registry unavailable'), findsNothing);
      api.dispose();
    },
  );
}
