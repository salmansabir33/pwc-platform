import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../app/providers.dart';
import '../app/strings.dart';
import '../core/contracts.g.dart';
import '../design/controls.dart';

class SecurityScreen extends ConsumerStatefulWidget {
  const SecurityScreen({super.key});
  @override
  ConsumerState<SecurityScreen> createState() => _SecurityState();
}

class _SecurityState extends ConsumerState<SecurityScreen> {
  Sessions? _sessions;
  MfaStatus? _status;
  int? _generation;
  bool _loading = false;
  final _code = TextEditingController();
  @override
  void dispose() {
    _code.clear();
    _code.dispose();
    super.dispose();
  }

  Future<void> _refresh() async {
    setState(() => _loading = true);
    final session = ref.read(sessionProvider);
    final captured = session.context.generation;
    try {
      final status = MfaStatus.fromJson(
        (await session.readSecurity('mfaStatus')).body,
      );
      final sessions = Sessions.fromJson(
        (await session.readSecurity('sessions')).body,
      );
      if (mounted &&
          session.authenticated &&
          session.context.accept(captured)) {
        setState(() {
          _status = status;
          _sessions = sessions;
          _generation = captured;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _status = null;
          _sessions = null;
        });
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<(String, String)?> _proofPrompt() async {
    final password = TextEditingController();
    final totp = TextEditingController();
    final form = GlobalKey<FormState>();
    final ur = ref.read(urduProvider);
    try {
      return await showDialog<(String, String)>(
        context: context,
        barrierDismissible: false,
        builder: (ctx) => AlertDialog(
          title: Text(translated('Security', ur)),
          content: SingleChildScrollView(
            child: Form(
              key: form,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Notice(
                    translated(
                      'Sensitive operations are bound to this personal account and exact command.',
                      ur,
                    ),
                  ),
                  SecretField(label: 'Password', controller: password, ur: ur),
                  // May be omitted for enrollment before a factor exists. The backend
                  // intent determines whether TOTP is required; there is no local bypass.
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 8),
                    child: TextField(
                      controller: totp,
                      obscureText: true,
                      enableInteractiveSelection: false,
                      autocorrect: false,
                      enableSuggestions: false,
                      decoration: InputDecoration(
                        labelText: translated('Authenticator code', ur),
                        border: const OutlineInputBorder(),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: Text(translated('Cancel', ur)),
            ),
            FilledButton(
              onPressed: () {
                if (form.currentState!.validate()) {
                  Navigator.pop(ctx, (password.text, totp.text));
                }
              },
              child: Text(translated('Continue', ur)),
            ),
          ],
        ),
      );
    } finally {
      password.clear();
      totp.clear();
      password.dispose();
      totp.dispose();
    }
  }

  Future<void> _codes(List<String> codes) async {
    if (!mounted) return;
    final ur = ref.read(urduProvider);
    await showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        title: Text(translated('One-time recovery codes', ur)),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Notice(
                translated(
                  'Record these privately now. They will not be stored or shown again. Clipboard copying is disabled.',
                  ur,
                ),
              ),
              for (final code in codes)
                Text(code, textDirection: TextDirection.ltr),
            ],
          ),
        ),
        actions: [
          FilledButton(
            onPressed: () => Navigator.pop(ctx),
            child: Text(translated('Done', ur)),
          ),
        ],
      ),
    );
  }

  Future<void> _command(String operation, {String? target}) async {
    final proof = await _proofPrompt();
    if (proof == null || !mounted) return;
    final session = ref.read(sessionProvider);
    if (!session.authenticated) return;
    try {
      final reply = await session.securityCommand(
        operation,
        proof.$1,
        proof.$2,
        targetSession: target,
      );
      if (operation == 'mfa.recovery_codes.rotate') {
        await _codes(RecoveryCodes.fromJson(reply.body).recoveryCodes);
      }
      if (mounted && session.authenticated) await _refresh();
    } catch (_) {
      /* controller safe error */
    }
  }

  Future<void> _confirm() async {
    final code = _code.text;
    _code.clear();
    try {
      final result = await ref.read(sessionProvider).confirmEnrollment(code);
      await _codes(result.recoveryCodes);
      if (mounted) await _refresh();
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    final session = ref.watch(sessionProvider);
    final ur = ref.watch(urduProvider);
    String t(String v) => translated(v, ur);
    final locked = session.busy || _loading;
    final current = _generation == session.context.generation;
    final enrollment = session.enrollment;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          t('ID-05 · Privacy and security'),
          style: Theme.of(context).textTheme.headlineSmall,
        ),
        if (session.error != null)
          Notice(t(safeMessage(session.error)), alert: true),
        if (session.hold != 'clear')
          Notice(
            t(
              session.hold == 'restricted'
                  ? 'Recovery restricted'
                  : 'Manual recovery review required',
            ),
            alert: true,
          ),
        if (session.hold == 'review_required')
          Notice(
            t(
              'Review required: factor codes cannot clear this state. Use the approved recovery review process.',
            ),
          ),
        if (current && _status != null)
          Notice(
            t(
              _status!.enabled
                  ? 'MFA enabled'
                  : _status!.pending
                  ? 'MFA pending'
                  : 'MFA disabled',
            ),
          ),
        OutlinedButton(
          onPressed: locked ? null : _refresh,
          child: Text(t('Refresh security status')),
        ),
        if (enrollment != null) ...[
          Notice(
            t(
              'Enter this secret manually in your authenticator. Confirm a fresh code before expiry.',
            ),
          ),
          Text(enrollment.secret, textDirection: TextDirection.ltr),
          SecretField(label: 'Authenticator code', controller: _code, ur: ur),
          FilledButton(
            onPressed: locked ? null : _confirm,
            child: Text(t('Confirm authenticator')),
          ),
        ],
        if (session.hold == 'clear')
          Wrap(
            spacing: 12,
            runSpacing: 12,
            children: [
              OutlinedButton(
                onPressed: locked ? null : () => _command('mfa.enroll'),
                child: Text(t('Enable authenticator')),
              ),
              OutlinedButton(
                onPressed: locked ? null : () => _command('mfa.remove'),
                child: Text(t('Remove authenticator')),
              ),
              OutlinedButton(
                onPressed: locked
                    ? null
                    : () => _command('mfa.recovery_codes.rotate'),
                child: Text(t('Rotate recovery codes')),
              ),
            ],
          ),
        if (session.hold == 'restricted')
          OutlinedButton(
            onPressed: locked ? null : () => _command('recovery_hold.clear'),
            child: Text(t('Clear restricted hold')),
          ),
        OutlinedButton(
          onPressed: locked ? null : () => _command('sessions.logout_all'),
          child: Text(t('Sign out all sessions')),
        ),
        const SizedBox(height: 16),
        Text(
          t('Active sessions'),
          style: Theme.of(context).textTheme.titleLarge,
        ),
        if (current && _sessions != null)
          for (final row in _sessions!.results)
            Card(
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(row.id, textDirection: TextDirection.ltr),
                    // User-controlled device labels are not echoed into the UI.
                    if (row.isCurrent) Text(t('Current session')),
                    Text(row.createdAt, textDirection: TextDirection.ltr),
                    TextButton(
                      onPressed: locked
                          ? null
                          : () => _command('sessions.revoke', target: row.id),
                      child: Text(t('Revoke')),
                    ),
                  ],
                ),
              ),
            ),
      ],
    );
  }
}
