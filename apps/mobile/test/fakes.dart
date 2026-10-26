import 'dart:async';
import 'package:pwc_mobile/core/api.dart';
import 'package:pwc_mobile/core/contracts.g.dart';
import 'package:pwc_mobile/core/storage.dart';

const userId = '00000000-0000-4000-8000-000000000001';
const sessionId = '00000000-0000-4000-8000-000000000002';
const intentId = '00000000-0000-4000-8000-000000000003';
Json sessionData({
  String access = 'synthetic-access-1',
  String refresh = 'synthetic-refresh-1',
  String hold = 'clear',
  DateTime? clock,
}) {
  final now = clock ?? DateTime.utc(2026, 10, 26);
  return {
    'user': {'id': userId, 'preferred_language': 'en'},
    'session': {
      'id': sessionId,
      'absolute_expires_at': now
          .add(const Duration(days: 30))
          .toIso8601String(),
      'idle_expires_at': now.add(const Duration(days: 7)).toIso8601String(),
      'assurance': {'method': 'password', 'last_mfa_at': null},
    },
    'recovery_hold_state': hold,
    'access_token': access,
    'refresh_token': refresh,
    'token_type': 'Bearer',
    'expires_in': 300,
    'refresh_expires_at': now.add(const Duration(days: 7)).toIso8601String(),
  };
}

Json meData({String hold = 'clear'}) {
  final data = sessionData(hold: hold);
  return {
    'user': data['user'],
    'session': data['session'],
    'recovery_hold_state': hold,
    'email_verified': true,
  };
}

class MemoryStore implements CredentialStore {
  MobileSession? value;
  bool failRead = false, failWrite = false, failClear = false;
  int writes = 0;
  int generation = 0;
  Future<void>? writeGate;
  Completer<void>? writeStarted;
  @override
  Future<MobileSession?> read() async {
    if (failRead) throw StateError('unavailable');
    return value;
  }

  @override
  Future<String> lease() async => '$generation';
  @override
  Future<void> replace(MobileSession session, {required String lease}) async {
    writeStarted?.complete();
    if (writeGate != null) {
      await writeGate;
    }
    if (lease != '$generation') {
      throw StateError('Stale lease');
    }
    if (failWrite) throw StateError('unavailable');
    writes++;
    value = session;
  }

  @override
  Future<void> clear() async {
    if (failClear) throw StateError('unavailable');
    generation++;
    value = null;
  }
}

class FakeApi implements PersonalApi {
  final calls = <(String, Json, String?, String?)>[];
  int refreshes = 0;
  Future<ApiReply> Function(String, Json, String?, String?)? handler;
  @override
  void cancel() {}
  @override
  Future<ApiReply> call(
    String operation,
    Json body, {
    String? access,
    String? sessionId,
  }) async {
    calls.add((operation, body, access, sessionId));
    if (handler != null) return handler!(operation, body, access, sessionId);
    return switch (operation) {
      'mobileLogin' => ApiReply(200, sessionData()),
      'mobileRefresh' => ApiReply(
        200,
        sessionData(
          access: 'synthetic-access-${++refreshes + 1}',
          refresh: 'synthetic-refresh-${refreshes + 1}',
        ),
      ),
      'me' => ApiReply(200, meData()),
      'mfaStatus' => const ApiReply(200, {
        'enabled': false,
        'pending': false,
        'recovery_hold_state': 'clear',
      }),
      'sessions' => const ApiReply(200, {'results': []}),
      'logout' => const ApiReply(204, {}),
      _ => throw StateError('Unimplemented fixture operation'),
    };
  }
}
