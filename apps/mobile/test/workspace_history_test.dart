import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pwc_mobile/core/contracts.g.dart';
import 'package:pwc_mobile/features/workspace_history.dart';

class FakeHistory implements WorkspaceHistoryGateway {
  Completer<WorkspacePage>? pending;
  bool fail = false;
  String? lastState;
  @override
  Future<WorkspacePage> load(
    String kind, {
    String state = '',
    String? cursor,
  }) async {
    lastState = state;
    if (fail) throw StateError('private server note');
    if (pending != null) return pending!.future;
    return WorkspacePage.fromJson({
      'results': [
        {
          'id': '00000000-0000-4000-8000-000000000001',
          'organization_id': '00000000-0000-4000-8000-000000000001',
          'kind': kind,
          'revision': 2,
          'state': 'withdrawn',
          'name': 'Synthetic historical draft',
          'city': 'City',
          'classification': 'unregistered',
          'can_withdraw': false,
          'verification': [
            {
              'id': '00000000-0000-4000-8000-000000000003',
              'purpose': 'organization_eligibility',
              'state': 'submitted',
              'revision': 1,
              'source_revision': 1,
              'stale': true,
            },
          ],
        },
      ],
      'next_cursor': null,
      'administration_available': false,
      'intake_available': false,
      'verification_available': true,
    });
  }
}

Widget history({WorkspaceHistoryGateway? gateway, String scope = 'fixture'}) =>
    MaterialApp(
      home: Scaffold(
        body: SingleChildScrollView(
          child: WorkspaceHistoryScreen(gateway: gateway, scope: scope),
        ),
      ),
    );
void main() {
  testWidgets(
    'unavailable by default; injected owner history has no admin controls',
    (tester) async {
      await tester.pumpWidget(history());
      expect(
        tester.widget<FilledButton>(find.byType(FilledButton)).onPressed,
        isNull,
      );
      await tester.pumpWidget(history(gateway: FakeHistory()));
      await tester.tap(find.text('Refresh history'));
      await tester.pumpAndSettle();
      expect(find.text('Synthetic historical draft'), findsOneWidget);
      expect(find.text('Withdrawn'), findsOneWidget);
      expect(find.textContaining('No membership'), findsOneWidget);
      expect(find.text('Approve'), findsNothing);
    },
  );
  testWidgets('safe failures and owner scope invalidation drop late data', (
    tester,
  ) async {
    final api = FakeHistory()..fail = true;
    await tester.pumpWidget(history(gateway: api));
    await tester.tap(find.text('Refresh history'));
    await tester.pumpAndSettle();
    expect(find.textContaining('private server note'), findsNothing);
    expect(find.textContaining('History unavailable'), findsOneWidget);
    api.fail = false;
    api.pending = Completer<WorkspacePage>();
    await tester.tap(find.text('Refresh history'));
    await tester.pump();
    await tester.pumpWidget(history(scope: 'signed-out'));
    api.pending!.complete(
      WorkspacePage.fromJson({
        'results': [],
        'next_cursor': null,
        'administration_available': false,
        'intake_available': false,
        'verification_available': true,
      }),
    );
    await tester.pumpAndSettle();
    expect(find.text('Synthetic historical draft'), findsNothing);
    expect(find.textContaining('transport unavailable'), findsOneWidget);
  });
  testWidgets(
    'state filter reaches read-only port and source revisions are explicit',
    (tester) async {
      final api = FakeHistory();
      await tester.pumpWidget(history(gateway: api));
      final filter = tester
          .widgetList<DropdownButtonFormField<String>>(
            find.byType(DropdownButtonFormField<String>),
          )
          .last;
      filter.onChanged!('withdrawn');
      await tester.pump();
      await tester.tap(find.text('Refresh history'));
      await tester.pumpAndSettle();
      expect(api.lastState, 'withdrawn');
      expect(
        find.textContaining('Verification revision: 1 · Source revision: 1'),
        findsOneWidget,
      );
      expect(find.textContaining('Stale source'), findsOneWidget);
    },
  );
}
