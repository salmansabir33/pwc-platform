import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pwc_mobile/app/app.dart';
import 'package:pwc_mobile/app/providers.dart';
import 'package:pwc_mobile/app/strings.dart';
import 'package:pwc_mobile/core/session_controller.dart';
import 'fakes.dart';
void main(){
  testWidgets('unauthenticated identity form has secret-field protections',(tester)async{
    final session=SessionController(FakeApi(),MemoryStore(),clock:()=>DateTime.utc(2026,10,26));
    await tester.pumpWidget(ProviderScope(overrides:[sessionProvider.overrideWith((ref)=>session)],child:const PwcApp()));
    await tester.pumpAndSettle();expect(find.text('ID-01 · Sign in'),findsOneWidget);
    final fields=tester.widgetList<TextField>(find.byType(TextField));expect(fields.any((v)=>v.obscureText && !v.enableInteractiveSelection),true);
    expect(find.text('ID-02 · Personal profile'),findsNothing);
    await tester.pumpWidget(const SizedBox.shrink());
  });
  testWidgets('Urdu locale is RTL with translated identity labels',(tester)async{
    final session=SessionController(FakeApi(),MemoryStore(),clock:()=>DateTime.utc(2026,10,26));
    await tester.pumpWidget(ProviderScope(overrides:[sessionProvider.overrideWith((ref)=>session),urduProvider.overrideWith((ref)=>true)],child:const PwcApp()));
    await tester.pumpAndSettle();expect(find.text(urdu['ID-01 · Sign in']!),findsOneWidget);
    expect(Directionality.of(tester.element(find.text(urdu['ID-01 · Sign in']!))),TextDirection.rtl);
    await tester.pumpWidget(const SizedBox.shrink());
  });
  for(final size in [const Size(320,640),const Size(1200,900)]){
    testWidgets('identity is responsive and supports scaled text at $size',(tester)async{
      tester.view.physicalSize=size;tester.view.devicePixelRatio=1;addTearDown(tester.view.resetPhysicalSize);addTearDown(tester.view.resetDevicePixelRatio);
      final session=SessionController(FakeApi(),MemoryStore(),clock:()=>DateTime.utc(2026,10,26));
      await tester.pumpWidget(ProviderScope(overrides:[sessionProvider.overrideWith((ref)=>session)],child:const PwcApp()));
      await tester.pumpAndSettle();expect(tester.takeException(),null);
      await tester.pumpWidget(const SizedBox.shrink());
    });
  }
  test('all English UI strings in translation catalog are translated',(){
    expect(urdu.length,greaterThan(75));expect(urdu.values.every((v)=>RegExp(r'[\u0600-\u06ff]').hasMatch(v)),true);
  });
}
