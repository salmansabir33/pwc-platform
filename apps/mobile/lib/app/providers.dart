import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api.dart';
import '../core/directory_api.dart';
import '../core/contracts.g.dart';
import '../core/session_controller.dart';
import '../core/storage.dart';

const apiOrigin = String.fromEnvironment('PWC_API_ORIGIN');

class DisabledApi implements PersonalApi {
  @override
  Future<ApiReply> call(
    String operation,
    Json body, {
    String? access,
    String? sessionId,
  }) async => throw const ApiFailure('AUTH_UNAVAILABLE');
  @override
  void cancel() {}
}

final sessionProvider = ChangeNotifierProvider<SessionController>((ref) {
  return SessionController(
    apiOrigin.isEmpty ? DisabledApi() : NativeApi(apiOrigin),
    NativeCredentialStore(),
  );
});
final urduProvider = StateProvider<bool>((ref) => false);

// Independent public-only opt-in; never widens personal/native domain operations.
const directoryOrigin = String.fromEnvironment('PWC_PUBLIC_DIRECTORY_ORIGIN');
final directoryProvider = Provider<DirectoryGateway?>((ref) {
  if (directoryOrigin.isEmpty) return null;
  final gateway = NativeDirectoryGateway(directoryOrigin);
  ref.onDispose(gateway.dispose);
  return gateway;
});
