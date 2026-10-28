import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'api.dart';
import 'contracts.g.dart';

abstract interface class DirectoryGateway {
  Future<RegistrySearchPage> search(
    String query,
    String city, {
    String? cursor,
  });
  void cancel();
}

// Separate opt-in public-only reader. Never accepts access credentials, tenant IDs,
// arbitrary paths, cookies, redirects or writes. PersonalApi allowlist unchanged.
class NativeDirectoryGateway implements DirectoryGateway {
  final Uri origin;
  final http.Client Function() _factory;
  http.Client? _client;
  NativeDirectoryGateway(String base, {http.Client Function()? factory})
    : origin = Uri.tryParse(base) ?? (throw const ApiFailure('CONFIGURATION')),
      _factory = factory ?? http.Client.new {
    if (origin.scheme != 'https' ||
        origin.host.isEmpty ||
        origin.userInfo.isNotEmpty ||
        origin.hasQuery ||
        origin.hasFragment ||
        !['', '/'].contains(origin.path)) {
      throw const ApiFailure('CONFIGURATION');
    }
  }
  @override
  void cancel() {
    _client?.close();
    _client = null;
  }

  void dispose() {
    _client?.close();
    _client = null;
  }

  @override
  Future<RegistrySearchPage> search(
    String query,
    String city, {
    String? cursor,
  }) async {
    if (query.length > 250 ||
        city.length > 250 ||
        (cursor?.length ?? 0) > 1024) {
      throw const ApiFailure('VALIDATION_ERROR');
    }
    try {
      return await _search(
        query,
        city,
        cursor,
      ).timeout(const Duration(seconds: 20));
    } on TimeoutException {
      cancel();
      throw const ApiFailure('NETWORK_UNAVAILABLE');
    } on ApiFailure {
      rethrow;
    } catch (_) {
      throw const ApiFailure('NETWORK_UNAVAILABLE');
    }
  }

  Future<RegistrySearchPage> _search(
    String query,
    String city,
    String? cursor,
  ) async {
    final operation = publicDirectoryOperations
        .cast<Map<String, dynamic>>()
        .single;
    if (operation['id'] != 'publicDirectory' ||
        operation['method'] != 'GET' ||
        operation['path'] != '/api/v1/directory/' ||
        operation['authenticated'] != false) {
      throw const ApiFailure('CONFIGURATION');
    }
    final request = http.Request(
      'GET',
      origin
          .resolve('/api/v1/directory/')
          .replace(
            queryParameters: {
              'q': query,
              'city': city,
              if (cursor != null) 'cursor': cursor,
            },
          ),
    );
    request.followRedirects = false;
    request.headers['Accept'] = 'application/json';
    final response = await (_client ??= _factory()).send(request);
    final bytes = <int>[];
    await for (final chunk in response.stream) {
      if (bytes.length + chunk.length > 131072) {
        throw const ApiFailure('INVALID_RESPONSE');
      }
      bytes.addAll(chunk);
    }
    if (response.statusCode != 200) {
      throw ApiFailure('DIRECTORY_UNAVAILABLE', response.statusCode);
    }
    if (!(response.headers['content-type'] ?? '').toLowerCase().startsWith(
      'application/json',
    )) {
      throw const ApiFailure('INVALID_RESPONSE');
    }
    try {
      return RegistrySearchPage.fromJson(
        Map<String, Object?>.from(jsonDecode(utf8.decode(bytes)) as Map),
      );
    } catch (_) {
      throw const ApiFailure('INVALID_RESPONSE');
    }
  }
}
