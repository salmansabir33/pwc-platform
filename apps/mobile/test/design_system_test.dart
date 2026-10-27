import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pwc_mobile/design/theme.dart';
import 'package:pwc_mobile/design/tokens.g.dart';
import 'package:pwc_mobile/design/controls.dart';

void main() {
  test('v1 semantics and independent accents are explicit', () {
    final ngo = pwcTheme();
    final ops = pwcTheme(operations: true);
    expect(PwcTokens.version, '1.0.0');
    expect(ngo.brightness, Brightness.light);
    expect(ngo.colorScheme.primary, PwcTokens.ngoPrimary);
    expect(ops.colorScheme.primary, PwcTokens.opsPrimary);
    expect(ngo.colorScheme.error, PwcTokens.danger);
    expect(ngo.textTheme.bodyMedium?.fontSize, 16);
    expect(ngo.textTheme.bodySmall?.fontSize, 14);
    expect(ngo.textTheme.bodyMedium?.fontFamily, 'Inter');
    expect(
      pwcTheme(urdu: true).textTheme.bodyMedium?.fontFamily,
      PwcTokens.urduFont,
    );
    expect(
      ngo.filledButtonTheme.style?.backgroundColor?.resolve({
        WidgetState.disabled,
      }),
      PwcTokens.disabledBackground,
    );
    expect(
      ngo.filledButtonTheme.style?.backgroundColor?.resolve({
        WidgetState.pressed,
      }),
      PwcTokens.ngoPressed,
    );
  });
  for (final rtl in [false, true]) {
    testWidgets('320px, scaled text and direction=$rtl do not overflow', (
      tester,
    ) async {
      tester.view.physicalSize = const Size(320, 900);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      await tester.pumpWidget(
        MaterialApp(
          theme: pwcTheme(urdu: rtl),
          home: MediaQuery(
            data: const MediaQueryData(textScaler: TextScaler.linear(2)),
            child: Directionality(
              textDirection: rtl ? TextDirection.rtl : TextDirection.ltr,
              child: Scaffold(
                body: SingleChildScrollView(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        PwcStatePanel(
                          title: rtl ? 'دستیاب نہیں' : 'Not available',
                          message: 'No workflow or command has been activated.',
                        ),
                        const PwcBadge('Restricted'),
                        const SizedBox(height: 16),
                        FilledButton(
                          onPressed: () {},
                          child: const Text('Continue'),
                        ),
                        TextField(
                          decoration: const InputDecoration(
                            labelText: 'Display name',
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      expect(
        tester.getSize(find.byType(FilledButton)).height,
        greaterThanOrEqualTo(48),
      );
      expect(
        Directionality.of(tester.element(find.byType(PwcBadge))),
        rtl ? TextDirection.rtl : TextDirection.ltr,
      );
    });
  }
}
