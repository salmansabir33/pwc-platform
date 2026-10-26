import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../app/providers.dart';
import '../app/strings.dart';
import '../design/controls.dart';
class PersonalScreen extends ConsumerWidget {
  const PersonalScreen({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final session=ref.watch(sessionProvider); final ur=ref.watch(urduProvider);
    String t(String v)=>translated(v,ur);
    final me=session.identity;
    if (me==null) return const SizedBox.shrink();
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children:[
      Text(t('ID-02 · Personal profile'),style:Theme.of(context).textTheme.headlineSmall),
      Notice(t('Personal context only')),
      Text('${t('Account')}: ${me.user.id}',textDirection:TextDirection.ltr),
      Text('${t('Session')}: ${me.session.id}',textDirection:TextDirection.ltr),
      Text('${t('Session expires')}: ${me.session.absoluteExpiresAt}',textDirection:TextDirection.ltr),
      if(me.emailVerified) Notice(t('Email verified')),
      if(session.hold!='clear') Notice(t(session.hold=='restricted'?'Recovery restricted':'Manual recovery review required'),alert:true),
      const SizedBox(height:16),
      FilledButton(onPressed: session.busy?null:()async {try{await session.logout();}catch(_){}},child:Text(t('Sign out'))),
    ]);
  }
}
class UnavailableScreen extends ConsumerWidget {
  final bool workspace;
  const UnavailableScreen({super.key,required this.workspace});
  @override
  Widget build(BuildContext context,WidgetRef ref){
    final ur=ref.watch(urduProvider);
    return Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
      Text(translated(workspace?'ID-04 · Workspaces':'ID-03 · Affiliations',ur),style:Theme.of(context).textTheme.headlineSmall),
      Notice(translated(workspace?'No real NGO workspace API is available. Personal MFA and platform roles do not grant NGO access.':'Affiliation discovery is not available. No membership or role is inferred.',ur)),
    ]);
  }
}
