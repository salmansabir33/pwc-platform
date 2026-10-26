import 'package:flutter/material.dart';
import '../app/strings.dart';

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
      autofillHints: const [],
      textInputAction: TextInputAction.next,
      decoration: InputDecoration(
        labelText: translated(label, ur),
        border: const OutlineInputBorder(),
      ),
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
