import 'package:flutter_test/flutter_test.dart';
import 'package:pwc_mobile/core/api.dart';
import 'package:pwc_mobile/core/contracts.g.dart';
import 'package:pwc_mobile/core/session_controller.dart';
import 'fakes.dart';

void main() {
  test(
    'two ordinary enrollments remain isolated and MFA never enters storage',
    () async {
      final clock = DateTime.utc(2026, 10, 26);
      final controllers = <SessionController>[];
      final stores = <MemoryStore>[];
      for (var index = 0; index < 2; index++) {
        final api = FakeApi();
        final store = MemoryStore();
        final owner = '00000000-0000-4000-8000-00000000000${index + 4}';
        final ownedSession = '00000000-0000-4000-8000-00000000000${index + 6}';
        Json identity(bool tokens) {
          final data = tokens
              ? sessionData(
                  clock: clock,
                  access: 'synthetic-access-$index',
                  refresh: 'synthetic-refresh-$index',
                )
              : meData();
          data['user'] = {'id': owner, 'preferred_language': 'en'};
          final session = Map<String, Object?>.from(data['session']! as Map);
          session['id'] = ownedSession;
          data['session'] = session;
          return data;
        }

        final expires = clock.add(const Duration(minutes: 5)).toIso8601String();
        api.handler = (operation, body, access, target) async {
          switch (operation) {
            case 'registrationRequest':
              expect(access, null);
              return ApiReply(202, {
                'status': 'accepted',
                'flow_id': intentId,
                'flow_control': 'synthetic-control-$index',
                'expires_in': 1800,
              });
            case 'registrationConfirm':
              expect(body.keys.toSet(), {'flow_id', 'proof', 'password'});
              expect(body['password'], 'synthetic-password-$index');
              expect(access, null);
              return const ApiReply(201, {'status': 'verified'});
            case 'mobileLogin':
              return ApiReply(200, identity(true));
            case 'me':
              return ApiReply(200, identity(false));
            case 'createIntent':
              expect(body['operation'], 'mfa.enroll');
              expect(body['context'], {'kind': 'personal', 'id': owner});
              return ApiReply(201, {
                'intent_id': intentId,
                'expires_at': expires,
                'required_methods': ['password'],
              });
            case 'stepUp':
              expect(body['password'], 'synthetic-password-$index');
              return ApiReply(200, {
                'assurance_proof': 'synthetic-assurance-$index',
                'expires_at': expires,
              });
            case 'enrollMfa':
              return ApiReply(201, {
                'enrollment_id': intentId,
                'secret': 'SYNTHETIC-$index',
                'otpauth_uri': 'otpauth://totp/synthetic-$index',
                'expires_at': expires,
              });
            case 'confirmMfa':
              return ApiReply(200, {
                'status': 'active',
                'recovery_codes': List.generate(
                  10,
                  (n) => 'synthetic-recovery-$index-$n',
                ),
              });
            case 'logout':
              return const ApiReply(204, {});
            default:
              throw StateError('Unexpected operation');
          }
        };
        final controller = SessionController(api, store, clock: () => clock);
        controllers.add(controller);
        stores.add(store);
        await controller.startFlow(
          'fixture-$index@example.invalid',
          reset: false,
        );
        expect(store.value, null);
        await controller.confirmFlow(
          'synthetic-proof-$index',
          'synthetic-password-$index',
        );
        expect(controller.authenticated, false);
        expect(store.value, null);
        await controller.login(
          'fixture-$index@example.invalid',
          'synthetic-password-$index',
        );
        expect(controller.identity!.user.id, owner);
        await controller.securityCommand(
          'mfa.enroll',
          'synthetic-password-$index',
          '',
        );
        final activation = await controller.confirmEnrollment('123456');
        expect(activation.recoveryCodes.length, 10);
        expect(controller.enrollment, null);
        final stored = store.value!.toJson().toString();
        expect(stored.contains('synthetic-password'), false);
        expect(stored.contains('synthetic-proof'), false);
        expect(stored.contains('synthetic-recovery'), false);
        expect(stored.contains('SYNTHETIC-'), false);
        expect(stored.contains('role'), false);
      }
      expect(
        controllers[0].identity!.user.id,
        isNot(controllers[1].identity!.user.id),
      );
      await controllers[0].logout();
      expect(stores[0].value, null);
      expect(controllers[1].authenticated, true);
      expect(stores[1].value, isNotNull);
      for (final controller in controllers) {
        controller.dispose();
      }
    },
  );
}
