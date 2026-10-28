import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../app/providers.dart';
import '../app/strings.dart';
import '../design/controls.dart';

class IdentityScreen extends ConsumerStatefulWidget {
  const IdentityScreen({super.key});
  @override
  ConsumerState<IdentityScreen> createState() => _IdentityState();
}

class _IdentityState extends ConsumerState<IdentityScreen> {
  final _form = GlobalKey<FormState>();
  final _email = TextEditingController();
  final _password = TextEditingController();
  final _proof = TextEditingController();
  final _code = TextEditingController();
  bool _register = false;
  bool _reset = false;
  bool _recovery = false;
  String? _notice;
  @override
  void dispose() {
    for (final value in [_email, _password, _proof, _code]) {
      value.clear();
      value.dispose();
    }
    super.dispose();
  }

  Future<void> _submit() async {
    if (!(_form.currentState?.validate() ?? false)) return;
    final session = ref.read(sessionProvider);
    final password = _password.text;
    final proof = _proof.text;
    final code = _code.text;
    _password.clear();
    _proof.clear();
    _code.clear();
    try {
      if (session.challenge != null) {
        await session.completeMfa(_recovery ? 'recovery_code' : 'totp', code);
      } else if (session.flow != null) {
        await session.confirmFlow(proof, password);
        if (mounted) {
          setState(() {
            _register = false;
            _reset = false;
            _notice = 'Done';
          });
        }
      } else if (_register || _reset) {
        await session.startFlow(_email.text.trim(), reset: _reset);
      } else {
        await session.login(_email.text.trim(), password);
      }
    } catch (_) {
      /* normalized controller error only */
    }
  }

  @override
  Widget build(BuildContext context) {
    final session = ref.watch(sessionProvider);
    final ur = ref.watch(urduProvider);
    String t(String v) => translated(v, ur);
    final mfa = session.challenge != null;
    final flow = session.flow != null;
    return Form(
      key: _form,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          TextButton(
            onPressed: () => context.push('/ngo-registry'),
            child: Text(
              ur ? 'عوامی تنظیموں کی فہرست' : 'NGO registry · public read-only',
            ),
          ),
          Text(
            t('ID-01 · Sign in'),
            style: Theme.of(context).textTheme.headlineSmall,
          ),
          if (apiOrigin.isEmpty)
            Notice(
              t(
                'Network disabled: configure an approved HTTPS API origin at build time.',
              ),
            ),
          if (session.storageBlocked)
            Notice(
              t(
                'Secure storage unavailable. Access is locked until deletion can be verified.',
              ),
              alert: true,
            ),
          if (session.error != null)
            Notice(t(safeMessage(session.error)), alert: true),
          if (_notice != null) Notice(t(_notice!)),
          if (mfa) ...[
            SecretField(
              label: _recovery ? 'Recovery code' : 'Authenticator code',
              controller: _code,
              ur: ur,
            ),
            SwitchListTile(
              title: Text(t('Use recovery code')),
              value: _recovery,
              onChanged: session.busy
                  ? null
                  : (v) => setState(() {
                      _recovery = v;
                      _code.clear();
                    }),
            ),
          ] else if (flow) ...[
            Notice(
              t(
                'Synthetic delivery only: an inbox message is not promised. Obtain test proof only from the authorized synthetic delivery harness.',
              ),
            ),
            SecretField(
              label: 'Verification proof',
              controller: _proof,
              ur: ur,
            ),
            SecretField(label: 'New password', controller: _password, ur: ur),
            TextButton(
              onPressed: session.busy
                  ? null
                  : () async {
                      try {
                        await session.resend();
                      } catch (_) {}
                    },
              child: Text(t('Resend')),
            ),
          ] else ...[
            SecretField(
              label: 'Email',
              controller: _email,
              ur: ur,
              secret: false,
            ),
            if (!_register && !_reset)
              SecretField(label: 'Password', controller: _password, ur: ur),
          ],
          const SizedBox(height: 12),
          FilledButton(
            onPressed: session.busy || session.storageBlocked ? null : _submit,
            child: Text(
              t(
                session.busy
                    ? 'Processing'
                    : mfa
                    ? 'Complete sign in'
                    : flow
                    ? 'Confirm verification'
                    : _register || _reset
                    ? 'Request verification'
                    : 'Sign in',
              ),
            ),
          ),
          if (!mfa && !flow)
            Wrap(
              spacing: 12,
              children: [
                TextButton(
                  onPressed: session.busy
                      ? null
                      : () => setState(() {
                          _register = true;
                          _reset = false;
                          _password.clear();
                        }),
                  child: Text(t('Register')),
                ),
                TextButton(
                  onPressed: session.busy
                      ? null
                      : () => setState(() {
                          _reset = true;
                          _register = false;
                          _password.clear();
                        }),
                  child: Text(t('Reset password')),
                ),
                TextButton(
                  onPressed: session.busy
                      ? null
                      : () async {
                          try {
                            await session.restore();
                          } catch (_) {}
                        },
                  child: Text(t('Resume session')),
                ),
              ],
            ),
          if (mfa || flow || _register || _reset)
            TextButton(
              onPressed: session.busy
                  ? null
                  : () {
                      session.cancelCeremonies();
                      _password.clear();
                      _proof.clear();
                      _code.clear();
                      setState(() {
                        _register = false;
                        _reset = false;
                      });
                    },
              child: Text(t('Cancel')),
            ),
          if (session.storageBlocked)
            TextButton(
              onPressed: session.busy
                  ? null
                  : () async {
                      try {
                        await session.logout();
                      } catch (_) {}
                    },
              child: Text(t('Sign out')),
            ),
        ],
      ),
    );
  }
}
