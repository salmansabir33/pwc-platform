import 'package:flutter_test/flutter_test.dart';
import 'package:pwc_mobile/core/contracts.g.dart';
import 'package:pwc_mobile/core/contract_validation.dart';
import 'package:pwc_mobile/core/api.dart';
import 'dart:io';
import 'dart:convert';

void main() {
  final fixtures =
      jsonDecode(
            File(
              '../../packages/api-contracts/examples-v1.json',
            ).readAsStringSync(),
          )
          as Map;
  for (final item in fixtures['cases'] as List) {
    final op = personalOperations.cast<Map<String, dynamic>>().where(
      (o) => o['id'] == item['operationId'],
    );
    if (op.isEmpty) continue;
    final name = item['kind'] == 'request'
        ? op.first['request']
        : (op.first['responses'] as Map)['${item['status']}'];
    if (name == null || name == '') continue;
    test(
      'canonical ${item['operationId']} ${item['kind']} ${item['status']}',
      () {
        validateContract(
          item['body'],
          canonicalSchemas[name] as Map<String, dynamic>,
          canonicalSchemas,
        );
      },
    );
  }
  test('synthetic NGO, browser and csrf APIs are not callable', () {
    expect(
      personalOperations.every(
        (o) =>
            !(o['path'] as String).contains('ngo') &&
            !(o['path'] as String).contains('/web/') &&
            !(o['path'] as String).contains('/csrf/'),
      ),
      true,
    );
  });
  test('credential models redact strings', () {
    final model = Login.fromJson({
      'email': 'person@example.invalid',
      'password': 'synthetic-password',
    });
    expect(model.toString(), isNot(contains('synthetic-password')));
  });
  for (final data in [
    <String, Object?>{},
    {'email': 'a', 'password': ''},
    {'email': 'a', 'password': 'b', 'is_admin': true},
    {'email': 17, 'password': 'b'},
  ]) {
    test(
      'reject malformed login ${data.keys}',
      () => expect(() => Login.fromJson(data), throwsA(isA<ContractFailure>())),
    );
  }
  for (final base in [
    'http://example.invalid',
    'https://user:pass@example.invalid',
    'https://example.invalid/api',
    'https://example.invalid?token=a',
    'https://example.invalid#x',
    '',
  ]) {
    test(
      'reject unsafe base $base',
      () => expect(() => NativeApi(base), throwsA(isA<ApiFailure>())),
    );
  }
}
