import 'dart:async';
import 'package:flutter_test/flutter_test.dart';
import 'package:pwc_mobile/core/session_controller.dart';
import 'package:pwc_mobile/core/contracts.g.dart';
import 'package:pwc_mobile/core/api.dart';
import 'fakes.dart';
void main(){
  late FakeApi api;late MemoryStore store;late SessionController session;
  late DateTime clock;
  setUp((){api=FakeApi();store=MemoryStore();clock=DateTime.utc(2026,10,26);session=SessionController(api,store,clock:()=>clock);});
  tearDown(()=>session.dispose());
  Future<void> login()=>session.login('person@example.invalid','synthetic-password');
  test('login requires me and stores one coherent pair',()async{
    await login();expect(session.authenticated,true);expect(store.writes,1);
    expect(api.calls.map((c)=>c.$1),['mobileLogin','me']);
    expect(api.calls.first.$3,null);expect(api.calls.last.$3,'synthetic-access-1');
  });
  test('preauth is memory-only and not authority',()async{
    api.handler=(op,b,a,id)async=>const ApiReply(202,{'status':'mfa_required','challenge_id':intentId,'preauth_control':'synthetic-control','expires_in':60});
    await login();expect(session.authenticated,false);expect(session.challenge,isNotNull);expect(store.value,null);
    session.suspend();expect(session.challenge,null);
  });
  test('expired preauth cannot be replayed',()async{
    api.handler=(op,b,a,id)async=>const ApiReply(202,{'status':'mfa_required','challenge_id':intentId,'preauth_control':'synthetic-control','expires_in':60});
    await login();clock=clock.add(const Duration(seconds:61));
    await expectLater(session.completeMfa('totp','123456'),throwsA(isA<ApiFailure>()));expect(api.calls.length,1);expect(session.challenge,null);
  });
  test('cold restore rotates before obtaining identity',()async{
    store.value=MobileSession.fromJson(sessionData());await session.restore();
    expect(api.calls.map((c)=>c.$1),['mobileRefresh','me']);expect(api.refreshes,1);expect(session.authenticated,true);
  });
  test('refresh old proof is absent from disk before dispatch',()async{
    await login();clock=clock.add(const Duration(seconds:301));
    api.handler=(op,b,a,id)async{
      if(op=='mobileRefresh'){expect(store.value,null);return ApiReply(200,sessionData(access:'new-access',refresh:'new-refresh',clock:clock));}
      if(op=='me')return ApiReply(200,meData());
      return const ApiReply(200,{'results':[]});
    };
    await session.readSecurity('sessions');expect(store.value!.refreshToken,'new-refresh');
  });
  test('parallel protected callers perform one rotation',()async{
    await login();clock=clock.add(const Duration(seconds:301));
    await Future.wait([session.readSecurity('sessions'),session.readSecurity('mfaStatus')]);expect(api.refreshes,1);
  });
  test('ambiguous refresh clears all local authority with no retry',()async{
    await login();clock=clock.add(const Duration(seconds:301));
    api.handler=(op,b,a,id)async=>throw const ApiFailure('NETWORK_UNCERTAIN');
    await expectLater(session.readSecurity('sessions'),throwsA(isA<ApiFailure>()));
    expect(store.value,null);expect(session.identity,null);
    expect(api.calls.where((c)=>c.$1=='mobileRefresh').length,1);
  });
  test('logout fences a late refresh and cannot resurrect tokens',()async{
    await login();clock=clock.add(const Duration(seconds:301));
    final completer=Completer<ApiReply>();final dispatched=Completer<void>();
    api.handler=(op,b,a,id)async{
      if(op=='mobileRefresh'){dispatched.complete();return completer.future;}
      return const ApiReply(204,{});
    };
    final pending=session.readSecurity('sessions');
    final checked=expectLater(pending,throwsA(isA<StaleOperation>()));
    await dispatched.future;final out=session.logout();
    completer.complete(ApiReply(200,sessionData(access:'late-access',refresh:'late-refresh')));
    await checked;await out;expect(store.value,null);expect(session.authenticated,false);
  });
  test('logout clears locally even if server is unavailable',()async{
    await login();api.handler=(o,b,a,id)async=>throw const ApiFailure('NETWORK_UNCERTAIN');
    await session.logout();expect(store.value,null);expect(session.authenticated,false);expect(session.error,'LOGOUT_UNCONFIRMED');
  });
  test('revoked access fails closed without refresh retry',()async{
    await login();api.handler=(o,b,a,id)async=>throw const ApiFailure('SESSION_INVALID',401);
    await expectLater(session.readSecurity('sessions'),throwsA(isA<ApiFailure>()));expect(store.value,null);expect(api.refreshes,0);
  });
  test('expired idle lifetime is not extended locally',()async{
    store.value=MobileSession.fromJson(sessionData());clock=clock.add(const Duration(days:8));
    await expectLater(session.restore(),throwsA(isA<ApiFailure>()));expect(api.calls,isEmpty);expect(store.value,null);
  });
  test('unavailable secure read never restores authority',()async{
    store.failRead=true;await expectLater(session.restore(),throwsStateError);expect(session.authenticated,false);expect(session.storageBlocked,true);
  });
  test('failed secure replacement clears issued credentials',()async{
    store.failWrite=true;await expectLater(login(),throwsStateError);expect(store.value,null);expect(session.authenticated,false);
  });
  test('failed deletion blocks a fresh login',()async{
    await login();store.failClear=true;await expectLater(session.logout(),throwsStateError);expect(session.storageBlocked,true);
    await expectLater(login(),throwsA(isA<ApiFailure>()));expect(session.authenticated,false);
  });
  test('mismatched me identity cannot authorize or persist',()async{
    api.handler=(op,b,a,id)async=>op=='mobileLogin'?ApiReply(200,sessionData()):ApiReply(200,{...meData(),'user':{'id':intentId,'preferred_language':'en'}});
    await expectLater(login(),throwsA(isA<ApiFailure>()));expect(store.value,null);expect(session.identity,null);
  });
  test('hold/review state is taken from backend me',()async{
    api.handler=(op,b,a,id)async=>op=='mobileLogin'?ApiReply(200,sessionData(hold:'restricted')):ApiReply(200,meData(hold:'review_required'));
    await login();expect(session.hold,'review_required');
  });
  test('contexts reject synthetic activation and late cache results',(){
    final context=session.context;final old=context.generation;context.put('private','synthetic-record',old);
    expect(()=>context.organization(intentId),throwsA(isA<ApiFailure>()));expect(context.get('private'),null);
    context.put('private','late',old);expect(context.get('private'),null);
  });
}
