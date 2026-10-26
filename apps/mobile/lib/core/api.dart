import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'contracts.g.dart';
import 'contract_validation.dart';

class ApiFailure implements Exception {
  final String code;
  final int? status;
  const ApiFailure(this.code, [this.status]);
  @override
  String toString() => 'Request unavailable ($code)';
}

class ApiReply {
  final int status;
  final Json body;
  const ApiReply(this.status, this.body);
}

abstract interface class PersonalApi {
  Future<ApiReply> call(
    String operation,
    Json body, {
    String? access,
    String? sessionId,
  });
  void cancel();
}

// Native-only, HTTPS, no cookies, redirects, retries, interceptor logging or
// browser provenance. No caller-defined endpoint, context or extra headers.
class NativeApi implements PersonalApi {
  final Uri origin;
  http.Client _client;
  final http.Client Function() _factory;
  NativeApi(String base, {http.Client Function()? factory})
    : origin = Uri.parse(base),
      _factory = factory ?? http.Client.new,
      _client = (factory ?? http.Client.new)() {
    if (origin.scheme != 'https' ||
        origin.host.isEmpty ||
        origin.userInfo.isNotEmpty ||
        origin.hasQuery ||
        origin.hasFragment ||
        !['', '/'].contains(origin.path)) {
      _client.close();
      throw const ApiFailure('CONFIGURATION');
    }
  }
  @override
  void cancel() {
    _client.close();
    _client = _factory();
  }

  @override
  Future<ApiReply> call(String operation, Json body, {String? access, String? sessionId}) async {
    try {
      return await _send(operation, body, access: access, sessionId: sessionId)
          .timeout(const Duration(seconds: 20));
    } on TimeoutException {
      cancel();
      throw const ApiFailure('NETWORK_UNCERTAIN');
    }
  }

  Future<ApiReply> _send(
    String operation,
    Json body, {
    String? access,
    String? sessionId,
  }) async {
    final op = personalOperations.cast<Map<String, dynamic>>().singleWhere(
      (entry) => entry['id'] == operation,
      orElse: () => throw const ApiFailure('UNAVAILABLE'),
    );
    if (access != null && (access.length > 4096 || access.codeUnits.any((c) => c < 33 || c > 126))) {
      throw const ApiFailure('TRANSPORT');
    }
    final authenticated = op['authenticated'] as bool;
    if (authenticated != (access != null)) throw const ApiFailure('TRANSPORT');
    final requestSchema = op['request'] as String;
    if (requestSchema.isNotEmpty) {
      validateContract(
        body,
        canonicalSchemas[requestSchema] as Map<String, dynamic>,
        canonicalSchemas,
      );
    } else if (body.isNotEmpty) {
      throw const ContractFailure();
    }
    var path = op['path'] as String;
    if (path.contains('{session_id}')) {
      if (sessionId == null ||
          !RegExp(r'^[a-fA-F0-9-]{36}$').hasMatch(sessionId)) {
        throw const ContractFailure();
      }
      path = path.replaceFirst('{session_id}', sessionId);
    }
    final request = http.Request(op['method'] as String, origin.resolve(path))
      ..followRedirects = false
      ..headers.addAll({
        'Accept': 'application/json',
        'Cache-Control': 'no-store',
        if (access != null) 'Authorization': 'Bearer $access',
      });
    if (request.method != 'GET') {
      request.headers['Content-Type'] = 'application/json';
      request.body = jsonEncode(body);
    }
    try {
      final response = await _client
          .send(request)
          .timeout(const Duration(seconds: 20));
      final bytes = <int>[];
      await for (final chunk in response.stream.timeout(
        const Duration(seconds: 20),
      )) {
        if (bytes.length + chunk.length > 262144) {
          throw const ApiFailure('RESPONSE_LIMIT');
        }
        bytes.addAll(chunk);
      }
      final success =
          (op['responses'] as Map<String, dynamic>)['${response.statusCode}'];
      if (success == null) {
        // Never display server message/field echoes, HTML, credentials or URLs.
        String code = 'REQUEST_FAILED';
        try {
          final value = jsonDecode(utf8.decode(bytes)) as Map<String, dynamic>;
          final error = value['error'] as Map<String, dynamic>;
          final candidate = error['code'];
          if (candidate is String &&
              RegExp(r'^[A-Z_]{1,64}$').hasMatch(candidate)) {
            code = candidate;
          }
        } catch (_) {
          /* keep safe fallback */
        }
        throw ApiFailure(code, response.statusCode);
      }
      if (success == '') {
        if (bytes.isNotEmpty) throw const ContractFailure();
        return ApiReply(response.statusCode, {});
      }
      if (!(response.headers['content-type'] ?? '').toLowerCase().startsWith(
        'application/json',
      )) {
        throw const ContractFailure();
      }
      final data = Map<String, Object?>.from(
        jsonDecode(utf8.decode(bytes)) as Map,
      );
      validateContract(
        data,
        canonicalSchemas[success] as Map<String, dynamic>,
        canonicalSchemas,
      );
      return ApiReply(response.statusCode, data);
    } on ApiFailure {
      rethrow;
    } on ContractFailure {
      rethrow;
    } on TimeoutException {
      throw const ApiFailure('NETWORK_UNCERTAIN');
    } on SocketException {
      throw const ApiFailure('NETWORK_UNCERTAIN');
    } on http.ClientException {
      throw const ApiFailure('NETWORK_UNCERTAIN');
    } catch (_) {
      throw const ApiFailure('INVALID_RESPONSE');
    }
  }
}
