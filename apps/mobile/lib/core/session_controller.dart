import 'dart:async';
import 'package:flutter/foundation.dart';
import 'api.dart';
import 'contracts.g.dart';
import 'storage.dart';

class StaleOperation implements Exception { const StaleOperation(); }

// All private caches are generation-scoped, not role-scoped. No production NGO
// discovery API exists: callers cannot activate a synthetic organization.
class ContextFence {
  int generation = 0;
  final Map<String, Object> _cache = {};
  void clear() { generation++; _cache.clear(); }
  void personal() => clear();
  Never organization(String ignored) { clear(); throw const ApiFailure('UNAVAILABLE'); }
  bool accept(int captured) => captured == generation;
  void put(String key, Object value, int captured) {
    if (accept(captured)) _cache[key] = value;
  }
  Object? get(String key) => _cache[key];
}

class SessionController extends ChangeNotifier {
  final PersonalApi api;
  final CredentialStore store;
  final DateTime Function() now;
  final ContextFence context = ContextFence();
  Future<void> _tail = Future<void>.value();
  MobileSession? _credentials;
  DateTime? _accessUntil;
  Me? identity;
  Preauth? challenge;
  DateTime? _challengeUntil;
  FlowAccepted? flow;
  DateTime? _flowUntil;
  bool resetFlow = false;
  Enrollment? enrollment;
  bool busy = false;
  bool storageBlocked = false;
  bool suspended = false;
  bool _disposed = false;
  String? error;
  int _epoch = 0;
  Timer? _timer;
  SessionController(this.api, this.store, {DateTime Function()? clock}) : now = clock ?? DateTime.now;
  bool get authenticated => identity != null && !suspended && !storageBlocked;
  String get hold => identity?.recoveryHoldState ?? 'clear';
  void _notify() { if (!_disposed) notifyListeners(); }
  void _fence(int captured) { if (captured != _epoch || _disposed) throw const StaleOperation(); }
  void _transients() { challenge = null; flow = null; enrollment = null; }
  void _privateClear() {
    _timer?.cancel(); identity = null; _credentials = null; _accessUntil = null;
    _transients(); context.clear();
  }
  Future<T> _serial<T>(Future<T> Function(int captured) action) {
    final captured = _epoch;
    final result = _tail.then((_) async {
      _fence(captured); busy = true; error = null; _notify();
      try { return await action(captured); }
      catch (failure) {
        if (captured == _epoch) {
          error = failure is ApiFailure ? _safeCode(failure.code) : 'FAILED';
          _notify();
        }
        rethrow;
      } finally { busy = false; _notify(); }
    });
    _tail = result.then<void>((_) {}, onError: (Object _, StackTrace __) {});
    return result;
  }
  String _safeCode(String code) => const {
    'AUTH_UNAVAILABLE','SESSION_INVALID','MFA_REQUIRED','CHALLENGE_INVALID',
    'RECOVERY_RESTRICTED','RECOVERY_REVIEW_REQUIRED','VALIDATION_ERROR',
    'STEP_UP_REQUIRED','RATE_LIMITED','NETWORK_UNCERTAIN','UNAVAILABLE',
  }.contains(code) ? code : 'FAILED';

  Future<void> _erase() async {
    _privateClear();
    try {
      await store.clear();
      if (await store.read() != null) throw StateError('Deletion not confirmed');
      storageBlocked = false;
    } catch (_) { storageBlocked = true; rethrow; }
  }
  Future<void> _accept(MobileSession session, int captured) async {
    _fence(captured);
    _validateLifetime(session);
    final me = Me.fromJson((await api.call('me', {}, access: session.accessToken)).body);
    _fence(captured);
    if (me.user.id != session.user.id || me.session.id != session.session.id) {
      throw const ApiFailure('SESSION_INVALID');
    }
    await store.replace(session);
    _fence(captured);
    _credentials = session; identity = me; suspended = false;
    _accessUntil = now().add(Duration(seconds: session.expiresIn));
    context.clear(); _transients();
    _timer?.cancel();
    _timer = Timer(Duration(seconds: session.expiresIn), suspend);
    _notify();
  }
  void _validateLifetime(MobileSession s) {
    final deadlines = [s.refreshExpiresAt, s.session.idleExpiresAt, s.session.absoluteExpiresAt];
    if (s.expiresIn <= 0 || s.expiresIn > 300 || deadlines.any((v) => !DateTime.parse(v).isAfter(now()))) {
      throw const ApiFailure('SESSION_INVALID');
    }
  }
  Future<void> _rotate(int captured) async {
    final old = _credentials;
    if (old == null) throw const ApiFailure('SESSION_INVALID');
    _validateLifetime(old);
    // Crash/timeout safe: the old single-use proof cannot survive to be replayed.
    // Delete and verify BEFORE sending refresh. Failure/uncertainty => re-login.
    await store.clear();
    if (await store.read() != null) throw StateError('Rotation preparation failed');
    _fence(captured);
    final rotated = MobileSession.fromJson((await api.call('mobileRefresh',
        Refresh.fromJson({'refresh_token': old.refreshToken}).toJson())).body);
    _fence(captured);
    if (rotated.user.id != old.user.id || rotated.session.id != old.session.id ||
        rotated.refreshToken == old.refreshToken || rotated.accessToken == old.accessToken) {
      throw const ApiFailure('SESSION_INVALID');
    }
    await _accept(rotated, captured);
  }
  Future<void> restore() => _serial((captured) async {
    _privateClear();
    try {
      _credentials = await store.read(); _fence(captured);
      if (_credentials != null) await _rotate(captured);
      else suspended = false;
    } catch (_) { await _erase(); rethrow; }
    _notify();
  });
  Future<void> login(String email, String password) => _serial((captured) async {
    if (storageBlocked) throw const ApiFailure('UNAVAILABLE');
    await _erase(); _fence(captured);
    try {
      final reply = await api.call('mobileLogin', Login.fromJson({'email': email, 'password': password}).toJson());
      _fence(captured);
      if (reply.status == 202) {
        challenge = Preauth.fromJson(reply.body);
        _challengeUntil = now().add(Duration(seconds: challenge!.expiresIn));
      } else { await _accept(MobileSession.fromJson(reply.body), captured); }
    } catch (_) { await _erase(); rethrow; }
    _notify();
  });
  Future<void> completeMfa(String method, String code) => _serial((captured) async {
    final pending = challenge;
    challenge = null;
    if (pending == null || !(_challengeUntil?.isAfter(now()) ?? false)) {
      throw const ApiFailure('CHALLENGE_INVALID');
    }
    try {
      final result = await api.call('mobileMfaConfirm', MfaLogin.fromJson({
        'challenge_id': pending.challengeId, 'preauth_control': pending.preauthControl,
        'method': method, 'code': code}).toJson());
      _fence(captured); await _accept(MobileSession.fromJson(result.body), captured);
    } catch (_) { await _erase(); rethrow; }
  });
  Future<ApiReply> _protected(String operation, Json body, int captured, {String? sessionId}) async {
    try {
      _fence(captured);
      if (_credentials == null || suspended || storageBlocked) throw const ApiFailure('SESSION_INVALID');
      _validateLifetime(_credentials!);
      if (!(_accessUntil?.isAfter(now()) ?? false)) await _rotate(captured);
      _fence(captured);
      final reply = await api.call(operation, body, access: _credentials!.accessToken, sessionId: sessionId);
      _fence(captured);
      return reply;
    } catch (failure) {
      if (failure is! ApiFailure || failure.status == 401 ||
          failure.code == 'NETWORK_UNCERTAIN' || failure.code == 'SESSION_INVALID') {
        await _erase();
      } else if (failure.code.startsWith('RECOVERY_')) {
        // Do not retain a previously clear/privileged screen after a hold denial.
        suspend();
      }
      rethrow;
    }
  }
  Future<ApiReply> readSecurity(String operation) => _serial((captured) async {
    if (!['sessions', 'mfaStatus', 'me'].contains(operation)) throw const ApiFailure('UNAVAILABLE');
    return _protected(operation, {}, captured);
  });
  Future<void> startFlow(String email, {required bool reset}) => _serial((captured) async {
    _transients();
    final reply = await api.call(reset ? 'resetRequest' : 'registrationRequest', FlowRequest.fromJson({'email': email}).toJson());
    _fence(captured); resetFlow = reset; flow = FlowAccepted.fromJson(reply.body);
    _flowUntil = now().add(Duration(seconds: flow!.expiresIn)); _notify();
  });
  Future<void> resend() => _serial((captured) async {
    final pending = _validFlow();
    await api.call(resetFlow ? 'resetResend' : 'registrationResend', FlowResend.fromJson({
      'flow_id': pending.flowId, 'flow_control': pending.flowControl}).toJson());
    _fence(captured);
  });
  FlowAccepted _validFlow() {
    if (flow == null || !(_flowUntil?.isAfter(now()) ?? false)) throw const ApiFailure('CHALLENGE_INVALID');
    return flow!;
  }
  Future<void> confirmFlow(String proof, String password) => _serial((captured) async {
    final pending = _validFlow(); final reset = resetFlow;
    flow = null;
    if (reset) { await _erase(); _fence(captured); }
    await api.call(reset ? 'resetConfirm' : 'registrationConfirm', {
      'flow_id': pending.flowId, 'proof': proof, reset ? 'new_password' : 'password': password});
    _fence(captured);
    if (reset) await _erase();
    _notify();
  });

  // Ceremony is scoped to exact personal operation/object/command; proofs never
  // enter widget state or persistent storage and are never reused on failure.
  Future<ApiReply> securityCommand(String operation, String password, String totp,
      {String? targetSession}) => _serial((captured) async {
    const commands = {
      'mfa.enroll': 'enrollMfa', 'mfa.remove': 'removeMfa',
      'mfa.recovery_codes.rotate': 'rotateRecovery', 'sessions.logout_all': 'logoutAll',
      'sessions.revoke': 'revokeSession', 'recovery_hold.clear': 'clearHold',
    };
    final endpoint = commands[operation];
    if (endpoint == null || identity == null) throw const ApiFailure('UNAVAILABLE');
    final intent = Intent.fromJson((await _protected('createIntent', {
      'operation': operation, 'context': {'kind': 'personal', 'id': identity!.user.id},
      'command': {if (targetSession != null) 'session_id': targetSession},
      if (targetSession != null) 'object_id': targetSession,
    }, captured)).body);
    if (!DateTime.parse(intent.expiresAt).isAfter(now())) throw const ApiFailure('CHALLENGE_INVALID');
    ApiReply result;
    if (operation == 'recovery_hold.clear') {
      result = await _protected(endpoint, ClearHold.fromJson({
        'intent_id': intent.intentId, 'password': password, 'totp_code': totp}).toJson(), captured);
    } else {
      final assurance = Assurance.fromJson((await _protected('stepUp', StepUp.fromJson({
        'intent_id': intent.intentId, 'password': password,
        if (intent.requiredMethods.contains('totp')) 'totp_code': totp}).toJson(), captured)).body);
      if (!DateTime.parse(assurance.expiresAt).isAfter(now())) throw const ApiFailure('CHALLENGE_INVALID');
      result = await _protected(endpoint, ProofCommand.fromJson({'assurance_proof': assurance.assuranceProof}).toJson(), captured, sessionId: targetSession);
    }
    if (operation == 'mfa.enroll') { enrollment = Enrollment.fromJson(result.body); }
    if (operation == 'mfa.remove' || operation == 'sessions.logout_all' ||
        (operation == 'sessions.revoke' && targetSession == identity?.session.id)) {
      await _erase();
    } else {
      final refreshed = await _protected('me', {}, captured);
      identity = Me.fromJson(refreshed.body);
    }
    _notify(); return result;
  });
  Future<Activation> confirmEnrollment(String code) => _serial((captured) async {
    final pending = enrollment; enrollment = null;
    if (pending == null || !DateTime.parse(pending.expiresAt).isAfter(now())) throw const ApiFailure('CHALLENGE_INVALID');
    final result = Activation.fromJson((await _protected('confirmMfa', EnrollmentConfirm.fromJson({
      'enrollment_id': pending.enrollmentId, 'code': code}).toJson(), captured)).body);
    _notify(); return result;
  });
  Future<void> logout() {
    final old = _credentials;
    _epoch++; api.cancel(); _privateClear(); suspended = false; _notify();
    return _serial((captured) async {
      await _erase();
      if (old == null) return;
      try { await api.call('logout', {}, access: old.accessToken); }
      catch (_) { error = 'LOGOUT_UNCONFIRMED'; _notify(); }
    });
  }
  void cancelCeremonies() { _epoch++; api.cancel(); _transients(); context.clear(); _notify(); }
  void suspend() {
    _epoch++; api.cancel(); suspended = true;
    _privateClear(); _notify();
  }
  @override
  void dispose() { _disposed = true; _epoch++; _timer?.cancel(); api.cancel(); super.dispose(); }
}
