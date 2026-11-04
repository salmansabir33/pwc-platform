import 'dart:convert';
import 'package:flutter/material.dart';
import '../core/membership_demonstrations.g.dart';
import '../design/controls.dart';

// Local fixture selection only; never a provider for rosters, credentials or IO.
class MembershipDemoState extends ChangeNotifier {
  int _selected = 0;
  int get selected => _selected;
  void select(int index) {
    if (index < 0 || index >= 5)
      throw RangeError.index(index, const [0, 1, 2, 3, 4]);
    _selected = index;
    notifyListeners();
  }

  void reset() => select(0);
}

class MembershipPreparationScreen extends StatefulWidget {
  final bool urdu;
  const MembershipPreparationScreen({super.key, this.urdu = false});
  @override
  State<MembershipPreparationScreen> createState() =>
      _MembershipPreparationState();
}

class _MembershipPreparationState extends State<MembershipPreparationScreen> {
  final model = MembershipDemoState();
  // Generated from the same backend fixed redacted examples as React. No network.
  final List<dynamic> scenarios =
      (jsonDecode(membershipDemonstrationsJson)
              as Map<String, dynamic>)['scenarios']
          as List<dynamic>;
  String t(String en, String ur) => widget.urdu ? ur : en;
  String word(String state) => switch (state) {
    'draft' => t('Draft', 'مسودہ'),
    'pending' => t('Pending', 'زیر التوا'),
    'accepted' => t('Proposed acceptance', 'قبولیت کی تجویز'),
    'active' => t('Active', 'فعال'),
    'suspended' => t('Suspended', 'معطل'),
    'ended' => t('Ended', 'ختم شدہ'),
    _ => state,
  };
  @override
  void dispose() {
    model.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final titles = [
      t('Admission requests', 'رکنیت کی درخواستیں'),
      t('Category assignment', 'زمرے کی تبدیلی'),
      t('Member status and history', 'رکن کی حالت اور تاریخ'),
      t('Source revision conflict', 'ماخذ کی ترمیم میں تضاد'),
      t('Import preparation', 'درآمد کی تیاری'),
    ];
    return ListenableBuilder(
      listenable: model,
      builder: (context, child) {
        final scenario = scenarios[model.selected] as Map<String, dynamic>;
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              t('Membership preparation', 'رکنیت کی تیاری'),
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            Notice(
              t(
                'Internal synthetic demonstration. No live membership authority.',
                'اندرونی فرضی نمونہ۔ حقیقی رکنیت کا اختیار نہیں۔',
              ),
            ),
            Text(
              t(
                'Nothing is sent, saved, admitted or linked.',
                'کچھ بھیجا، محفوظ، منظور یا منسلک نہیں ہوتا۔',
              ),
            ),
            DropdownButtonFormField<int>(
              value: model.selected,
              isExpanded: true,
              decoration: InputDecoration(
                labelText: t('Read-only example', 'صرف مطالعے کا نمونہ'),
              ),
              items: [
                for (var i = 0; i < titles.length; i++)
                  DropdownMenuItem(value: i, child: Text(titles[i])),
              ],
              onChanged: (value) {
                if (value != null) model.select(value);
              },
            ),
            Semantics(liveRegion: true, child: Text(titles[model.selected])),
            for (final raw in scenario['steps'] as List<dynamic>)
              ..._step(raw as Map<String, dynamic>),
            const SizedBox(height: 16),
            Text(
              t('Protected workflows — unavailable', 'محفوظ عمل — غیر دستیاب'),
            ),
            for (final label in [
              t('Save category', 'زمرہ محفوظ کریں'),
              t('Approve admission', 'داخلہ منظور کریں'),
              t('Change member status', 'رکن کی حالت بدلیں'),
              t('Upload or commit import', 'درآمد اپ لوڈ یا نافذ کریں'),
              t('Claim or link account', 'اکاؤنٹ کا دعویٰ یا ربط'),
            ])
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: FilledButton(onPressed: null, child: Text(label)),
              ),
            Notice(
              t(
                'Preview, staging, import approval, atomic creation and verified claiming are separate. No account linking by names or contacts.',
                'جائزہ، تیاری، درآمد کی منظوری، یکجا تخلیق اور تصدیق شدہ دعویٰ الگ ہیں۔ نام یا رابطے سے اکاؤنٹ منسلک نہیں ہوتا۔',
              ),
            ),
          ],
        );
      },
    );
  }

  List<Widget> _step(Map<String, dynamic> step) => [
    if (step.containsKey('revision'))
      Text(
        '${t('Fixture revision', 'فرضی ترمیم')}: ${step['revision']} · ${t('Fictional members', 'فرضی ارکان')}: ${step['member_count']}',
      ),
    if (step.containsKey('code'))
      Notice(
        '${t('Validation rejected stale source.', 'جانچ نے پرانا ماخذ مسترد کیا۔')} ${step['code']}',
      ),
    if (step.containsKey('history'))
      for (final raw in step['history'] as List<dynamic>)
        Text(
          '${raw['revision']}: ${word(raw['from_state'] as String)} → ${word(raw['to_state'] as String)}${raw['category_changed'] == true ? t(' · category changed', ' · زمرہ تبدیل') : ''}',
        ),
    if (step.containsKey('row_count'))
      Text(
        '${t('CSV records', 'سی ایس وی ریکارڈ')}: ${step['row_count']} · ${t('Admission candidates only', 'صرف داخلے کے امیدوار')}: ${step['candidate_count']}',
      ),
    if (step.containsKey('rows'))
      for (final row in step['rows'] as List<dynamic>)
        Text(
          '${t('Record', 'ریکارڈ')} ${row['record']}: ${(row['errors'] as List<dynamic>).isEmpty ? t('Candidate only; no import or admission', 'صرف امیدوار؛ درآمد یا داخلہ نہیں') : (row['errors'] as List<dynamic>).join(', ')}',
        ),
  ];
}
