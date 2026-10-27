import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pwc_mobile/core/contracts.g.dart';
import 'package:pwc_mobile/features/verification.dart';
import 'registry_test.dart' show fixture;

class FakeVerification implements VerificationGateway {
  bool fail = false;
  Completer<VerificationCasePage>? pending;
  int calls = 0;
  @override
  Future<VerificationCasePage> cases() async {
    calls++;
    if (fail) throw StateError('private');
    if (pending != null) return pending!.future;
    return VerificationCasePage.fromJson({'results':[fixture('verificationCreateCase')], 'next_cursor':null});
  }
  @override
  Future<VerificationCase> change(String id, String command, int revision) async {
    if (revision != 1) throw StateError('stale');
    return VerificationCase.fromJson(fixture(command == 'submit' ? 'verificationSubmit' : 'verificationWithdraw'));
  }
}
void main() {
  testWidgets('04B mounted unavailable no evidence upload', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: Scaffold(body: VerificationScreen())));
    expect(tester.widget<FilledButton>(find.widgetWithText(FilledButton,'Load own cases')).onPressed,isNull);
    expect(find.textContaining('no approved evidence rubric'),findsOneWidget);
  });
  testWidgets('04B synthetic status uses revision and submission is not verification', (tester) async {
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: VerificationScreen(gateway:FakeVerification()))));
    await tester.tap(find.text('Load own cases')); await tester.pumpAndSettle();
    expect(find.textContaining('organization_eligibility'),findsOneWidget);
    await tester.tap(find.text('Submit preparation only')); await tester.pumpAndSettle();
    expect(find.textContaining('submitted'),findsOneWidget);
    expect(tester.widget<FilledButton>(find.widgetWithText(FilledButton,'Submit preparation only')).onPressed,isNull);
  });
  testWidgets('04B reviewer has no bootstrap path', (tester) async {
    final api=FakeVerification();
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: VerificationScreen(gateway:api,review:true))));
    expect(find.byType(FilledButton),findsNothing); expect(api.calls,0);
  });
  testWidgets('04B conflict is safe and not retried', (tester) async {
    final api=FakeVerification()..fail=true;
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: VerificationScreen(gateway:api))));
    await tester.tap(find.text('Load own cases'));await tester.pumpAndSettle();
    expect(find.textContaining('Reload current status'),findsOneWidget);expect(find.text('private'),findsNothing);expect(api.calls,1);
  });
  testWidgets('04B invalidation discards late case data', (tester) async {
    final api=FakeVerification()..pending=Completer<VerificationCasePage>();
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: VerificationScreen(gateway:api,scope:'a'))));
    await tester.tap(find.text('Load own cases'));await tester.pump();
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: VerificationScreen(gateway:api,scope:'b'))));
    api.pending!.complete(VerificationCasePage.fromJson({'results':[fixture('verificationCreateCase')],'next_cursor':null}));
    await tester.pumpAndSettle();expect(find.textContaining('organization_eligibility'),findsNothing);
  });
  test('04B manifest is separate from native personal and registry APIs', () {
    expect(verificationOperations.length,15);
    expect(personalOperations.any((dynamic o)=>o['path'].toString().contains('verification')),false);
    expect(registryOperations.any((dynamic o)=>o['path'].toString().contains('verification')),false);
  });
}
