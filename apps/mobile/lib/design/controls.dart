import 'package:flutter/material.dart';
import '../app/strings.dart';
import 'tokens.g.dart';

class SecretField extends StatelessWidget {
  final String label;
  final TextEditingController controller;
  final bool secret;
  final bool ur;
  const SecretField({
    super.key,
    required this.label,
    required this.controller,
    required this.ur,
    this.secret = true,
  });
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 8),
    child: TextFormField(
      controller: controller,
      obscureText: secret,
      enableInteractiveSelection: !secret,
      autocorrect: false,
      enableSuggestions: false,
      enableIMEPersonalizedLearning: false,
      autofillHints: null,
      textInputAction: TextInputAction.next,
      decoration: InputDecoration(labelText: translated(label, ur)),
      validator: (value) =>
          value == null || value.isEmpty ? translated('Required', ur) : null,
    ),
  );
}

class Notice extends StatelessWidget {
  final String text;
  final bool alert;
  const Notice(this.text, {super.key, this.alert = false});
  @override
  Widget build(BuildContext context) => Semantics(
    liveRegion: alert,
    child: Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Text(
        text,
        style: TextStyle(
          color: alert ? Theme.of(context).colorScheme.error : null,
        ),
      ),
    ),
  );
}

/// Textual status only; "verified" is never inferred by this widget.
class PwcBadge extends StatelessWidget {
  final String label;
  final bool warning;
  const PwcBadge(this.label, {super.key, this.warning = false});
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
    decoration: BoxDecoration(
      color: warning ? PwcTokens.warningBackground : PwcTokens.infoBackground,
      borderRadius: BorderRadius.circular(6),
    ),
    child: Text(
      label,
      style: Theme.of(context).textTheme.labelSmall?.copyWith(
        color: warning ? PwcTokens.warning : PwcTokens.info,
      ),
    ),
  );
}

class PwcStatePanel extends StatelessWidget {
  final String title;
  final String message;
  final bool error;
  const PwcStatePanel({
    super.key,
    required this.title,
    required this.message,
    this.error = false,
  });
  @override
  Widget build(BuildContext context) => Semantics(
    liveRegion: error,
    child: Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            Text(
              message,
              style: TextStyle(
                color: error ? PwcTokens.danger : PwcTokens.textSecondary,
              ),
            ),
          ],
        ),
      ),
    ),
  );
}

/// Caller retains authorization/proof/unknown-outcome handling. No command here.
Future<bool> pwcConfirm(
  BuildContext context, {
  required String title,
  required String message,
  required String confirm,
  required String cancel,
}) async =>
    await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: SingleChildScrollView(child: Text(message)),
        actions: [
          TextButton(
            autofocus: true,
            onPressed: () => Navigator.pop(context, false),
            child: Text(cancel),
          ),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: PwcTokens.danger),
            onPressed: () => Navigator.pop(context, true),
            child: Text(confirm),
          ),
        ],
      ),
    ) ??
    false;
