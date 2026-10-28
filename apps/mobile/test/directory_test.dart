import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
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

class FakeDirectory implements DirectoryGateway {
  int calls = 0;
  Completer<RegistrySearchPage>? pending;
  bool fail = false;
  @override
  void cancel() {}
  @override
  Future<RegistrySearchPage> search(
    String q,
    String city, {
    String? cursor,
  }) async {
    calls++;
    if (fail) throw StateError('private server note');
    if (pending != null) return pending!.future;
    return RegistrySearchPage.fromJson({
      'results': [row],
      'next_cursor': null,
    });
  }
}

Widget screen({DirectoryGateway? gateway, bool urdu = false}) => MaterialApp(
  home: Scaffold(
    body: SingleChildScrollView(
      child: DirectoryScreen(gateway: gateway, urdu: urdu),
    ),
  ),
);
void main() {
  test(
    'native public reader is exact HTTPS GET with no personal credentials',
    () async {
      final client = MockClient((request) async {
        expect(
          request.url.toString(),
          'https://api.example.invalid/api/v1/directory/?q=Synthetic&city=City',
        );
        expect(request.method, 'GET');
        expect(request.headers.containsKey('authorization'), isFalse);
        expect(request.headers.containsKey('cookie'), isFalse);
        expect(request.followRedirects, isFalse);
        return http.Response(
          jsonEncode({
            'results': [row],
            'next_cursor': null,
          }),
          200,
          headers: {'content-type': 'application/json'},
        );
      });
      final api = NativeDirectoryGateway(
        'https://api.example.invalid',
        factory: () => client,
      );
      expect(
        (await api.search('Synthetic', 'City')).results.single.name,
        'Synthetic NGO',
      );
      api.dispose();
    },
  );
  test(
    'reject HTTP, credentials, paths, redirects and noncanonical response',
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
      for (final response in [
        http.Response('private', 302),
        http.Response(
          '<html>private</html>',
          200,
          headers: {'content-type': 'text/html'},
        ),
        http.Response(
          jsonEncode({
            'results': [
              {...row, 'email': 'private'},
            ],
            'next_cursor': null,
          }),
          200,
          headers: {'content-type': 'application/json'},
        ),
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
  testWidgets(
    'default unavailable and opt-in public result; no private authority',
    (tester) async {
      await tester.pumpWidget(screen());
      expect(
        tester.widget<FilledButton>(find.byType(FilledButton)).onPressed,
        isNull,
      );
      final api = FakeDirectory();
      await tester.pumpWidget(screen(gateway: api));
      await tester.tap(find.text('Search registry'));
      await tester.pumpAndSettle();
      expect(find.text('Synthetic NGO'), findsOneWidget);
      expect(api.calls, 1);
      expect(find.textContaining('Not membership'), findsOneWidget);
    },
  );
  testWidgets(
    'errors minimized, results clear on edits and late locale changes',
    (tester) async {
      final api = FakeDirectory()..fail = true;
      await tester.pumpWidget(screen(gateway: api));
      await tester.tap(find.text('Search registry'));
      await tester.pumpAndSettle();
      expect(find.textContaining('private server note'), findsNothing);
      expect(find.textContaining('Registry unavailable'), findsOneWidget);
      api.fail = false;
      await tester.tap(find.text('Search registry'));
      await tester.pumpAndSettle();
      expect(find.text('Synthetic NGO'), findsOneWidget);
      await tester.enterText(find.byType(TextField).first, 'other');
      await tester.pump();
      expect(find.text('Synthetic NGO'), findsNothing);
      api.pending = Completer<RegistrySearchPage>();
      await tester.tap(find.text('Search registry'));
      await tester.pump();
      await tester.pumpWidget(screen(gateway: api, urdu: true));
      api.pending!.complete(
        RegistrySearchPage.fromJson({
          'results': [row],
          'next_cursor': null,
        }),
      );
      await tester.pumpAndSettle();
      expect(find.text('Synthetic NGO'), findsNothing);
    },
  );
}
