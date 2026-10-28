import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pwc_mobile/features/administration_boundary.dart';

void main() {
  for (final state in AdministrationBoundaryState.values) {
    for (final urdu in [false, true]) {
      testWidgets('admin boundary $state urdu=$urdu has no authority actions', (
        tester,
      ) async {
        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: SingleChildScrollView(
                child: Directionality(
                  textDirection: urdu ? TextDirection.rtl : TextDirection.ltr,
                  child: AdministrationBoundaryScreen(state: state, urdu: urdu),
                ),
              ),
            ),
          ),
        );
        expect(
          find.text(
            urdu
                ? 'صرف حالتوں کی تیاری۔ فعال اختیار موجود نہیں۔'
                : 'UI-state preparation only. No active authority.',
          ),
          findsOneWidget,
        );
        expect(find.byType(FilledButton), findsNothing);
        expect(find.byType(TextButton), findsNothing);
        expect(tester.takeException(), isNull);
      });
    }
  }
}
