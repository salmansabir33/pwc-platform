import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pwc_mobile/core/contracts.g.dart';
import 'package:pwc_mobile/core/contract_validation.dart';
import 'package:pwc_mobile/features/registry.dart';

Json fixture(String operation) {
  final data = jsonDecode(File('../../packages/api-contracts/examples-v1.json').readAsStringSync()) as Map;
  return Map<String, Object?>.from((data['cases'] as List).firstWhere((c) => c['operationId'] == operation && c['kind'] == 'response')['body'] as Map);
}

class FakeRegistry implements RegistryGateway {
  Completer<RegistrySearchPage>? pending;
  bool fail = false;
  int searchCalls = 0;
  @override
  Future<RegistrySearchPage> search(String query, String city, {String? cursor}) async {
    searchCalls++;
    if (fail) throw StateError('private server note');
    if (pending != null) return pending!.future;
    return RegistrySearchPage.fromJson({'results': [{'id':'00000000-0000-4000-8000-000000000001','name':'Synthetic Welfare','city':'Faisalabad','classification':'registered'}], 'next_cursor':null});
  }
  @override
  Future<RegistryDraft> edit(String id, RegistryDraftEdit input) async => RegistryDraft.fromJson(fixture('registryCreateDraft'));
  @override
  Future<RegistryEventPage> history(String kind, String id) async => RegistryEventPage.fromJson({'results':[], 'next_cursor':null});
  @override
  Future<RegistryDraft> create(RegistryDraftInput input) async => RegistryDraft.fromJson(fixture('registryCreateDraft'));
  @override
  Future<RegistryClaim> claim(String id) async => RegistryClaim.fromJson(fixture('registryCreateClaim'));
  @override
  Future<RegistryDraftPage> drafts({String? cursor}) async => RegistryDraftPage.fromJson({'results':[fixture('registryCreateDraft')], 'next_cursor':null});
  @override
  Future<RegistryClaimPage> claims({String? cursor}) async => RegistryClaimPage.fromJson({'results':[], 'next_cursor':null});
  @override
  Future<RegistryDraft> change(String id, String command, int revision) async => RegistryDraft.fromJson(fixture(command == 'submit' ? 'registrySubmitDraft' : 'registryWithdrawDraft'));
  @override
  Future<RegistryClaim> withdrawClaim(String id, int revision) async => RegistryClaim.fromJson(fixture('registryWithdrawClaim'));
}

void main() {
  Widget screen({RegistryGateway? gateway, String scope='synthetic'}) => MaterialApp(home: Scaffold(body: SingleChildScrollView(child: RegistryScreen(gateway:gateway,scope:scope))));
  final examples = jsonDecode(File('../../packages/api-contracts/examples-v1.json').readAsStringSync()) as Map;
  for (final item in examples['cases'] as List) {
    final ops = registryOperations.cast<Map<String, dynamic>>().where((o) => o['id'] == item['operationId']);
    if (ops.isEmpty) continue;
    final name = item['kind'] == 'request' ? ops.first['request'] : (ops.first['responses'] as Map)['${item['status']}'];
    test('04A contract ${item['operationId']} ${item['kind']}', () {
      validateContract(item['body'], canonicalSchemas[name] as Map<String,dynamic>, canonicalSchemas);
    });
  }
  test('registry operations never enter native personal transport allowlist', () {
    expect(personalOperations.any((o) => (o['path'] as String).contains('/registry/')), false);
    expect(() => RegistryDraftInput.fromJson({'name':'Example','classification':'unregistered','is_admin':true}), throwsA(isA<ContractFailure>()));
  });
  testWidgets('04A production view is gated with no authority controls', (tester) async {
    await tester.pumpWidget(screen());
    expect(find.textContaining('ORG-01'), findsOneWidget);
    expect(find.textContaining('Unavailable:'), findsOneWidget);
    expect(tester.widget<FilledButton>(find.widgetWithText(FilledButton,'Search')).onPressed, isNull);
    expect(find.text('Approve'), findsNothing);
  });
  testWidgets('contract fake searches and claims without granting access', (tester) async {
    final api=FakeRegistry();
    await tester.pumpWidget(screen(gateway:api));
    await tester.enterText(find.byType(TextField).first, 'Welfare');
    await tester.tap(find.text('Search')); await tester.pumpAndSettle();
    expect(find.textContaining('Potential duplicates'), findsOneWidget);
    await tester.ensureVisible(find.text('Request claim'));
    await tester.tap(find.text('Request claim')); await tester.pumpAndSettle();
    expect(find.textContaining('pending'), findsOneWidget);
  });
  testWidgets('safe errors do not echo raw bodies or replay', (tester) async {
    final api=FakeRegistry()..fail=true;
    await tester.pumpWidget(screen(gateway:api));
    await tester.enterText(find.byType(TextField).first, 'Welfare');
    await tester.tap(find.text('Search')); await tester.pumpAndSettle();
    expect(find.textContaining('conflicting'), findsOneWidget);
    expect(find.textContaining('private server note'), findsNothing);
    expect(api.searchCalls,1);
  });
  testWidgets('late search response is discarded on personal scope invalidation', (tester) async {
    final api=FakeRegistry()..pending=Completer<RegistrySearchPage>();
    await tester.pumpWidget(screen(gateway:api));
    await tester.enterText(find.byType(TextField).first, 'Welfare');
    await tester.tap(find.text('Search')); await tester.pump();
    await tester.pumpWidget(screen(scope:'signed-out'));
    api.pending!.complete(RegistrySearchPage.fromJson({'results':[], 'next_cursor':null}));
    await tester.pumpAndSettle();
    expect(find.textContaining('Unavailable:'), findsOneWidget);
    expect(find.textContaining('Potential duplicates'), findsNothing);
  });
}
