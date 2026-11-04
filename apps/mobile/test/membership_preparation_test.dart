import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pwc_mobile/core/membership_demonstrations.g.dart';
import 'package:pwc_mobile/design/theme.dart';
import 'package:pwc_mobile/features/membership_preparation.dart';

void main() {
  test(
    'fixture selection is bounded and resettable, not a membership writer',
    () {
      final state = MembershipDemoState();
      expect(state.selected, 0);
      state.select(4);
      expect(state.selected, 4);
      expect(() => state.select(5), throwsRangeError);
      state.reset();
      expect(state.selected, 0);
      state.dispose();
      final fixture =
          jsonDecode(membershipDemonstrationsJson) as Map<String, dynamic>;
      expect(fixture['synthetic_only'], true);
      expect(fixture['commit_available'], false);
      expect((fixture['scenarios'] as List<dynamic>).length, 5);
      expect(membershipDemonstrationsJson.contains('MEMBER_A'), false);
    },
  );
  for (final urdu in [false, true]) {
    testWidgets(
      '320px, scaled, rtl=$urdu fixture review has disabled protected actions',
      (tester) async {
        tester.view.physicalSize = const Size(320, 1000);
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
        await tester.pumpWidget(
          MaterialApp(
            theme: pwcTheme(urdu: urdu),
            home: Scaffold(
              body: SingleChildScrollView(
                child: MediaQuery(
                  data: const MediaQueryData(
                    textScaler: TextScaler.linear(1.3),
                  ),
                  child: Directionality(
                    textDirection: urdu ? TextDirection.rtl : TextDirection.ltr,
                    child: MembershipPreparationScreen(urdu: urdu),
                  ),
                ),
              ),
            ),
          ),
        );
        expect(
          find.text(urdu ? 'رکنیت کی تیاری' : 'Membership preparation'),
          findsOneWidget,
        );
        expect(
          tester
              .widgetList<FilledButton>(find.byType(FilledButton))
              .every((b) => b.onPressed == null),
          true,
        );
        await tester.tap(find.byType(DropdownButtonFormField<int>));
        await tester.pumpAndSettle();
        await tester.tap(
          find
              .text(
                urdu ? 'ماخذ کی ترمیم میں تضاد' : 'Source revision conflict',
              )
              .last,
        );
        await tester.pumpAndSettle();
        expect(find.textContaining('SOURCE_REVISION_CONFLICT'), findsOneWidget);
        expect(find.textContaining('MEMBER_A'), findsNothing);
        expect(tester.takeException(), isNull);
      },
    );
  }
}
