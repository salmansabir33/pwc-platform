import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../app/strings.dart';
import '../design/controls.dart';

class PublicHomeScreen extends StatelessWidget {
  final bool urdu;
  const PublicHomeScreen({super.key, this.urdu = false});
  @override
  Widget build(BuildContext context) {
    String t(String value) => translated(value, urdu);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Semantics(
          header: true,
          child: Text(
            t('Welcome to PWC'),
            style: Theme.of(context).textTheme.headlineSmall,
          ),
        ),
        Notice(
          t(
            'Explore public NGOs and keep favorites on this device. No sign-in is needed.',
          ),
        ),
        FilledButton.icon(
          onPressed: () => context.push('/ngo-registry'),
          icon: const Icon(Icons.search),
          label: Text(t('Explore NGOs')),
        ),
        OutlinedButton.icon(
          onPressed: () => context.push('/favorites'),
          icon: const Icon(Icons.bookmark_outline),
          label: Text(t('Favorite NGOs')),
        ),
        TextButton.icon(
          onPressed: () => context.go('/account'),
          icon: const Icon(Icons.person_outline),
          label: Text(t('Open account')),
        ),
        Notice(
          t('Public discovery is not NGO membership or administrator access.'),
        ),
      ],
    );
  }
}
