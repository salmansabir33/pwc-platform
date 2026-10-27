import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'providers.dart';
import 'strings.dart';
import '../features/identity.dart';
import '../features/personal.dart';
import '../features/security.dart';
import '../features/registry.dart';
import '../features/verification.dart';

class PwcApp extends ConsumerStatefulWidget {
  const PwcApp({super.key});
  @override
  ConsumerState<PwcApp> createState() => _PwcAppState();
}

class _PwcAppState extends ConsumerState<PwcApp> with WidgetsBindingObserver {
  late final GoRouter _router;
  bool _hidden = false;
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    final session = ref.read(sessionProvider);
    _router = GoRouter(
      initialLocation: '/identity',
      refreshListenable: session,
      redirect: (context, state) {
        if (!session.authenticated && state.uri.path != '/identity') {
          return '/identity';
        }
        if (session.authenticated && state.uri.path == '/identity') {
          return '/personal';
        }
        return null;
      },
      routes: [
        GoRoute(path: '/verification', builder: (c, s) => _Frame(index: 2, child: Consumer(builder: (context, ref, child) => VerificationScreen(urdu: ref.watch(urduProvider))))),
        GoRoute(
          path: '/registry',
          builder: (c, s) => _Frame(
            index: 2,
            child: Consumer(
              builder: (context, ref, child) =>
                  RegistryScreen(urdu: ref.watch(urduProvider)),
            ),
          ),
        ),
        GoRoute(
          path: '/identity',
          builder: (c, s) => const _Frame(child: IdentityScreen()),
        ),
        GoRoute(
          path: '/personal',
          builder: (c, s) => const _Frame(index: 0, child: PersonalScreen()),
        ),
        GoRoute(
          path: '/affiliations',
          builder: (c, s) => const _Frame(
            index: 1,
            child: UnavailableScreen(workspace: false),
          ),
        ),
        GoRoute(
          path: '/workspaces',
          builder: (c, s) =>
              const _Frame(index: 2, child: UnavailableScreen(workspace: true)),
        ),
        GoRoute(
          path: '/security',
          builder: (c, s) => const _Frame(index: 3, child: SecurityScreen()),
        ),
      ],
    );
    Future.microtask(() async {
      try {
        await session.restore();
      } catch (_) {}
    });
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state != AppLifecycleState.resumed) {
      ref.read(sessionProvider).suspend();
      if (mounted) setState(() => _hidden = true);
    } else if (mounted) {
      setState(() => _hidden = false);
    }
    // No background heartbeat, automatic proof replay or auto-unlock on resume.
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _router.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final ur = ref.watch(urduProvider);
    return MaterialApp.router(
      title: 'PWC',
      debugShowCheckedModeBanner: false,
      locale: Locale(ur ? 'ur' : 'en'),
      supportedLocales: const [Locale('en'), Locale('ur')],
      localizationsDelegates: GlobalMaterialLocalizations.delegates,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xff175c47)),
        inputDecorationTheme: const InputDecorationTheme(filled: true),
      ),
      routerConfig: _router,
      builder: (context, child) => _hidden
          ? Scaffold(
              body: Center(
                child: Text(translated('Protected view hidden', ur)),
              ),
            )
          : child!,
    );
  }
}

class _Frame extends ConsumerWidget {
  final Widget child;
  final int? index;
  const _Frame({required this.child, this.index});
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final ur = ref.watch(urduProvider);
    final session = ref.watch(sessionProvider);
    final labels = ['Personal', 'Affiliations', 'Workspaces', 'Security'];
    const icons = [
      Icons.person_outline,
      Icons.people_outline,
      Icons.domain_outlined,
      Icons.shield_outlined,
    ];
    void navigate(int v) {
      session.cancelCeremonies();
      context.go(['/personal', '/affiliations', '/workspaces', '/security'][v]);
    }

    final wide = MediaQuery.sizeOf(context).width >= 840;
    final content = SafeArea(
      child: Align(
        alignment: Alignment.topCenter,
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 640),
            child: child,
          ),
        ),
      ),
    );
    return Scaffold(
      appBar: AppBar(
        title: Text(translated('PWC personal identity', ur)),
        actions: [
          Semantics(
            label: ur ? 'English' : 'اردو',
            button: true,
            child: TextButton(
              onPressed: () => ref.read(urduProvider.notifier).state = !ur,
              child: Text(ur ? 'English' : 'اردو'),
            ),
          ),
        ],
      ),
      body: Row(
        children: [
          if (index != null && wide)
            NavigationRail(
              selectedIndex: index,
              onDestinationSelected: navigate,
              labelType: NavigationRailLabelType.all,
              destinations: [
                for (var i = 0; i < labels.length; i++)
                  NavigationRailDestination(
                    icon: Icon(icons[i]),
                    label: Text(translated(labels[i], ur)),
                  ),
              ],
            ),
          Expanded(child: content),
        ],
      ),
      bottomNavigationBar: index != null && !wide
          ? NavigationBar(
              selectedIndex: index!,
              onDestinationSelected: navigate,
              destinations: [
                for (var i = 0; i < labels.length; i++)
                  NavigationDestination(
                    icon: Icon(icons[i]),
                    label: translated(labels[i], ur),
                  ),
              ],
            )
          : null,
    );
  }
}
