import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'api.dart';
import 'contracts.g.dart';

abstract interface class DirectoryGateway {
  Future<RegistrySearchPage> search(
    String query,
    String city, {
    String classification = '',
    String? cursor,
  });
  Future<PublicOrganization> detail(String id);
  void cancel();
}

// Public-only opt-in. No personal credentials, arbitrary paths, redirects or writes.
class NativeDirectoryGateway implements DirectoryGateway {
  final Uri origin;
  final http.Client Function() _factory;
  final _clients = <http.Client>{};
  int _generation = 0;
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
    _generation++;
    for (final client in _clients.toList()) {
      client.close();
    }
    _clients.clear();
  }

  void dispose() => cancel();

  @override
  Future<RegistrySearchPage> search(
    String query,
    String city, {
    String classification = '',
    String? cursor,
  }) async {
    if (query.length > 250 ||
        city.length > 250 ||
        !['', 'registered', 'unregistered'].contains(classification) ||
        (cursor?.length ?? 0) > 1024) {
      throw const ApiFailure('VALIDATION_ERROR');
    }
    final data = await _get('publicDirectory', '/api/v1/directory/', {
      'q': query,
      'city': city,
      if (classification.isNotEmpty) 'classification': classification,
      if (cursor != null) 'cursor': cursor,
    });
    try {
      final page = RegistrySearchPage.fromJson(data);
      final ids = page.results.map((row) => row.id).toSet();
      if (ids.length != page.results.length) {
        throw const ApiFailure('INVALID_RESPONSE');
      }
      return page;
    } catch (_) {
      throw const ApiFailure('INVALID_RESPONSE');
    }
  }

  @override
  Future<PublicOrganization> detail(String id) async {
    if (!RegExp(
      r'^[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$',
    ).hasMatch(id)) {
      throw const ApiFailure('VALIDATION_ERROR');
    }
    final canonical = id.toLowerCase();
    final data = await _get(
      'publicOrganization',
      '/api/v1/organizations/{pk}/',
      {},
      id: canonical,
    );
    try {
      final row = PublicOrganization.fromJson(data);
      if (row.id != canonical) throw const ApiFailure('INVALID_RESPONSE');
      return row;
    } catch (_) {
      throw const ApiFailure('INVALID_RESPONSE');
    }
  }

  Future<Json> _get(
    String operationId,
    String template,
    Map<String, String> query, {
    String? id,
  }) async {
    final operation = publicDirectoryOperations
        .cast<Map<String, dynamic>>()
        .singleWhere((op) => op['id'] == operationId);
    if (operation['method'] != 'GET' ||
        operation['path'] != template ||
        operation['authenticated'] != false) {
      throw const ApiFailure('CONFIGURATION');
    }
    final request = http.Request(
      'GET',
      origin
          .resolve(id == null ? template : template.replaceFirst('{pk}', id))
          .replace(queryParameters: query.isEmpty ? null : query),
    );
    request.followRedirects = false;
    request.headers['Accept'] = 'application/json';
    final client = _factory();
    final generation = _generation;
    _clients.add(client);
    Future<Json> read() async {
      final response = await client.send(request);
      final bytes = <int>[];
      await for (final chunk in response.stream) {
        if (bytes.length + chunk.length > 131072) {
          throw const ApiFailure('INVALID_RESPONSE');
        }
        bytes.addAll(chunk);
      }
      if (generation != _generation) {
        throw const ApiFailure('DIRECTORY_UNAVAILABLE');
      }
      if (response.statusCode != 200) {
        throw ApiFailure('DIRECTORY_UNAVAILABLE', response.statusCode);
      }
      if ((response.headers['content-type'] ?? '')
              .toLowerCase()
              .split(';')
              .first
              .trim() !=
          'application/json') {
        throw const ApiFailure('INVALID_RESPONSE');
      }
      try {
        return Map<String, Object?>.from(jsonDecode(utf8.decode(bytes)) as Map);
      } catch (_) {
        throw const ApiFailure('INVALID_RESPONSE');
      }
    }

    try {
      return await read().timeout(const Duration(seconds: 20));
    } on ApiFailure {
      rethrow;
    } catch (_) {
      throw const ApiFailure('NETWORK_UNAVAILABLE');
    } finally {
      // A canceled request's timeout must never close a newer request's client.
      _clients.remove(client);
      client.close();
    }
  }
}
