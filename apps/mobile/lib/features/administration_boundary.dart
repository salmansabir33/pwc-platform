import 'package:flutter/material.dart';
import '../design/controls.dart';

enum AdministrationBoundaryState { unavailable, noContext, restricted, expired }

// Presentation only: no private provider, invitation token, permission writer
// or extension to NativeApi's personal-operation allowlist.
class AdministrationBoundaryScreen extends StatelessWidget {
  final bool urdu;
  final AdministrationBoundaryState state;
  const AdministrationBoundaryScreen({
    super.key,
    this.urdu = false,
    this.state = AdministrationBoundaryState.unavailable,
  });
  String t(String en, String ur) => urdu ? ur : en;
  @override
  Widget build(BuildContext context) {
    final reason = switch (state) {
      AdministrationBoundaryState.unavailable => t(
        'Administration integration unavailable.',
        'انتظامی رابطہ دستیاب نہیں۔',
      ),
      AdministrationBoundaryState.noContext => t(
        'No authorized NGO context. Personal identity is not an NGO role.',
        'تنظیم کا مجاز سیاق موجود نہیں۔ ذاتی شناخت تنظیم کا کردار نہیں۔',
      ),
      AdministrationBoundaryState.restricted => t(
        'Access restricted. No private information loaded.',
        'رسائی محدود ہے۔ نجی معلومات لوڈ نہیں کی گئیں۔',
      ),
      AdministrationBoundaryState.expired => t(
        'Session or invitation expired. Reauthentication is not grant activation.',
        'نشست یا دعوت ختم ہو چکی ہے۔ دوبارہ شناخت اختیار کی فعالیت نہیں۔',
      ),
    };
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          t('NGO administration boundary', 'تنظیم کی انتظامی حد'),
          style: Theme.of(context).textTheme.headlineSmall,
        ),
        Notice(
          t(
            'UI-state preparation only. No active authority.',
            'صرف حالتوں کی تیاری۔ فعال اختیار موجود نہیں۔',
          ),
        ),
        Notice(reason),
        Text(
          t(
            'Overview: approved public registry information is separate; no private NGO profile here.',
            'جائزہ: منظور شدہ عوامی معلومات الگ ہیں؛ یہاں نجی تنظیم پروفائل نہیں۔',
          ),
        ),
        Text(
          t(
            'Administrators and representatives: no private roster or appointment writer. Primary and ordinary administrators are distinct.',
            'منتظمین اور نمائندے: نجی فہرست یا تقرری دستیاب نہیں۔ بنیادی اور عام منتظم الگ ہیں۔',
          ),
        ),
        Text(
          t(
            'Nonfinance permissions: no grant editor or activation. Finance, signatory, alliance and support authority remain separate.',
            'غیر مالی اختیارات: تبدیلی یا فعالیت دستیاب نہیں۔ مالی، دستخطی، اتحاد اور معاونت کے اختیارات الگ ہیں۔',
          ),
        ),
        Text(
          t(
            'Invitations and appointment requests: unavailable. Recipient-bound invitations last at most 72 hours. Acceptance is distinct from activation; no success is claimed.',
            'دعوتیں اور تقرری کی درخواستیں: غیر دستیاب۔ دعوت وصول کنندہ سے منسلک اور زیادہ سے زیادہ ۷۲ گھنٹے کی ہے۔ قبولیت فعالیت سے الگ ہے؛ کامیابی کا دعویٰ نہیں۔',
          ),
        ),
      ],
    );
  }
}
