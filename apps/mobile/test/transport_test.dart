import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:pwc_mobile/core/api.dart';
import 'package:pwc_mobile/core/contract_validation.dart';
import 'fakes.dart';

void main() {
  test(
    'native public issuance sends no bearer, cookie or provenance',
    () async {
      final api = NativeApi(
        'https://api.example.invalid',
        factory: () => MockClient((request) async {
          expect(request.url.path, '/api/v1/auth/mobile/login/');
          expect(request.headers['Authorization'], null);
          expect(request.headers['Cookie'], null);
          expect(request.headers['Origin'], null);
          expect(request.headers['Referer'], null);
          expect(request.followRedirects, false);
          expect(request.headers['Cache-Control'], 'no-store');
          return http.Response(
            jsonEncode(sessionData()),
            200,
            headers: {'content-type': 'application/json'},
          );
        }),
      );
      await api.call('mobileLogin', {
        'email': 'person@example.invalid',
        'password': 'synthetic-password',
      });
    },
  );
  test('protected request has exactly native bearer', () async {
    final api = NativeApi(
      'https://api.example.invalid',
      factory: () => MockClient((request) async {
        expect(request.headers['Authorization'], 'Bearer synthetic-access');
        expect(request.body, isEmpty);
        return http.Response(
          jsonEncode(meData()),
          200,
          headers: {'content-type': 'application/json'},
        );
      }),
    );
    await api.call('me', {}, access: 'synthetic-access');
  });
  test('public and bearer transport cannot be mixed', () async {
    final api = NativeApi('https://api.example.invalid');
    await expectLater(
      api.call('mobileRefresh', {
        'refresh_token': 'synthetic-refresh',
      }, access: 'synthetic-access'),
      throwsA(isA<ApiFailure>()),
    );
    await expectLater(api.call('me', {}), throwsA(isA<ApiFailure>()));
  });
  test('unknown and synthetic endpoints cannot dispatch', () async {
    final api = NativeApi('https://api.example.invalid');
    for (final name in [
      'discoverSyntheticContexts',
      'webLogin',
      'csrf',
      '../../ngo',
    ]) {
      await expectLater(api.call(name, {}), throwsA(isA<ApiFailure>()));
    }
  });
  for (final status in [301, 302, 401, 403, 429, 500]) {
    test('HTTP $status is not success or automatic retry', () async {
      var calls = 0;
      final api = NativeApi(
        'https://api.example.invalid',
        factory: () => MockClient((r) async {
          calls++;
          return http.Response('<private-secret>', status);
        }),
      );
      await expectLater(
        api.call('me', {}, access: 'synthetic-access'),
        throwsA(isA<ApiFailure>()),
      );
      expect(calls, 1);
    });
  }
  test('invalid successful JSON does not produce authority', () async {
    final api = NativeApi(
      'https://api.example.invalid',
      factory: () => MockClient(
        (r) async => http.Response(
          '{}',
          200,
          headers: {'content-type': 'application/json'},
        ),
      ),
    );
    await expectLater(
      api.call('me', {}, access: 'synthetic-access'),
      throwsA(isA<ContractFailure>()),
    );
  });
  test('HTML success cannot be treated as an API response', () async {
    final api = NativeApi(
      'https://api.example.invalid',
      factory: () => MockClient((r) async => http.Response('secret', 200)),
    );
    await expectLater(
      api.call('me', {}, access: 'synthetic-access'),
      throwsA(isA<ContractFailure>()),
    );
  });
  test('oversized successful response is rejected before decoding', () async {
    final api = NativeApi(
      'https://api.example.invalid',
      factory: () => MockClient(
        (r) async => http.Response(
          'x' * 262145,
          200,
          headers: {'content-type': 'application/json'},
        ),
      ),
    );
    await expectLater(
      api.call('me', {}, access: 'synthetic-access'),
      throwsA(
        isA<ApiFailure>().having((e) => e.code, 'code', 'RESPONSE_LIMIT'),
      ),
    );
  });
  test(
    'server messages and field echoes are never surfaced as exceptions',
    () async {
      final api = NativeApi(
        'https://api.example.invalid',
        factory: () => MockClient(
          (r) async => http.Response(
            jsonEncode({
              'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'synthetic-secret',
                'field_errors': {
                  'password': ['synthetic-secret'],
                },
              },
            }),
            400,
            headers: {'content-type': 'application/json'},
          ),
        ),
      );
      try {
        await api.call('mobileLogin', {
          'email': 'person@example.invalid',
          'password': 'synthetic-password',
        });
        fail('must reject');
      } on ApiFailure catch (error) {
        expect(error.code, 'VALIDATION_ERROR');
        expect(error.toString(), isNot(contains('synthetic-secret')));
      }
    },
  );
}
