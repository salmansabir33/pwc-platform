import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'providers.dart';
import '../design/theme.dart';
import '../design/tokens.g.dart';
import 'strings.dart';
import '../features/identity.dart';
import '../features/home.dart';
import '../features/membership_preparation.dart';
import '../features/personal.dart';
import '../features/security.dart';
import '../features/registry.dart';
import '../features/directory.dart';
import '../features/favorites.dart';
import '../features/workspace_history.dart';
import '../features/administration_boundary.dart';
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
    var previouslyAuthenticated = session.authenticated;
    _router = GoRouter(
      initialLocation: '/',
      refreshListenable: session,
      redirect: (context, state) {
        final path = state.uri.path;
        final signedOut = previouslyAuthenticated && !session.authenticated;
        previouslyAuthenticated = session.authenticated;
        const publicPaths = {
          '/',
          '/identity',
          '/account',
          '/ngo-registry',
          '/favorites',
        };
        if (path == '/account')
          return session.authenticated ? '/personal' : '/identity';
        if (!session.authenticated && !publicPaths.contains(path)) {
          return signedOut ? '/' : '/identity';
        }
        if (session.authenticated && path == '/identity') return '/personal';
        return null;
      },
      routes: [
        GoRoute(
          path: '/',
          builder: (c, s) => _Frame(
            child: Consumer(
              builder: (context, ref, child) =>
                  PublicHomeScreen(urdu: ref.watch(urduProvider)),
            ),
          ),
        ),
        GoRoute(
          path: '/favorites',
          builder: (c, s) => _Frame(
            child: Consumer(
              builder: (context, ref, child) => FavoritesScreen(
                favorites: ref.watch(favoritesProvider),
                gateway: ref.watch(favoritesDirectoryProvider),
                urdu: ref.watch(urduProvider),
              ),
            ),
          ),
        ),
        GoRoute(
          path: '/ngo-registry',
          builder: (c, s) => _Frame(
            child: Consumer(
              builder: (context, ref, child) => DirectoryScreen(
                favorites: ref.watch(favoritesProvider),
                gateway: ref.watch(directoryProvider),
                urdu: ref.watch(urduProvider),
              ),
            ),
          ),
        ),
        GoRoute(
          path: '/membership-preparation',
          builder: (c, s) => _Frame(
            index: 2,
            child: Consumer(
              builder: (context, ref, child) =>
                  MembershipPreparationScreen(urdu: ref.watch(urduProvider)),
            ),
          ),
        ),
        GoRoute(
          path: '/administration',
          builder: (c, s) => _Frame(
            index: 2,
            child: Consumer(
              builder: (context, ref, child) =>
                  AdministrationBoundaryScreen(urdu: ref.watch(urduProvider)),
            ),
          ),
        ),
        GoRoute(
          path: '/application-history',
          builder: (c, s) => _Frame(
            index: 2,
            child: Consumer(
              builder: (context, ref, child) => WorkspaceHistoryScreen(
                scope:
                    '${ref.watch(sessionProvider).identity?.session.id}:${ref.watch(sessionProvider).hold}',
                urdu: ref.watch(urduProvider),
              ),
            ),
          ),
        ),
        GoRoute(
          path: '/verification',
          builder: (c, s) => _Frame(
            index: 2,
            child: Consumer(
              builder: (context, ref, child) =>
                  VerificationScreen(urdu: ref.watch(urduProvider)),
            ),
          ),
        ),
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
      theme: pwcTheme(urdu: ur),
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
    final labels = ['Home', 'Discover', 'Favorites', 'Account'];
    final path = GoRouterState.of(context).uri.path;
    final selected = path == '/'
        ? 0
        : path == '/ngo-registry'
        ? 1
        : path == '/favorites'
        ? 2
        : 3;
    const icons = [
      Icons.home_outlined,
      Icons.search,
      Icons.bookmark_outline,
      Icons.person_outline,
    ];
    void navigate(int v) {
      final target = [
        '/',
        '/ngo-registry',
        '/favorites',
        session.authenticated ? '/personal' : '/identity',
      ][v];
      if (target == path) return;
      session.cancelCeremonies();
      if (v == 0) {
        context.go('/');
      } else {
        context.push(target);
      }
    }

    final wide = MediaQuery.sizeOf(context).width >= PwcTokens.breakpoints[1];
    final content = SafeArea(
      child: Align(
        alignment: Alignment.topCenter,
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 640),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                if (session.authenticated && index != null)
                  Wrap(
                    spacing: 8,
                    children: [
                      for (final destination in {
                        'Personal': '/personal',
                        'Affiliations': '/affiliations',
                        'Workspaces': '/workspaces',
                        'Security': '/security',
                      }.entries)
                        TextButton(
                          onPressed: () {
                            if (destination.value == path) return;
                            session.cancelCeremonies();
                            context.push(destination.value);
                          },
                          child: Text(translated(destination.key, ur)),
                        ),
                    ],
                  ),
                child,
              ],
            ),
          ),
        ),
      ),
    );
    return Scaffold(
      appBar: AppBar(
        title: Text(translated('PWC citizen', ur)),
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
          if (wide)
            NavigationRail(
              selectedIndex: selected,
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
      bottomNavigationBar: !wide
          ? NavigationBar(
              selectedIndex: selected,
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
