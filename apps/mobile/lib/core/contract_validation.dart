import 'dart:collection';
import 'dart:convert';

// Deliberately never include a response/body/value in an exception.
class ContractFailure implements Exception {
  const ContractFailure();
  @override
  String toString() => 'Incompatible API response';
}

Map<String, Object?> checkedObject(
  Map<String, Object?> data,
  Map<String, dynamic> schema,
  Map<String, dynamic> schemas,
) {
  validateContract(data, schema, schemas);
  return UnmodifiableMapView(
    Map<String, Object?>.from(jsonDecode(jsonEncode(data)) as Map),
  );
}

void validateContract(
  Object? data,
  Map<String, dynamic> schema,
  Map<String, dynamic> schemas,
) {
  if (schema.containsKey(r'$ref')) {
    validateContract(
      data,
      schemas[(schema[r'$ref'] as String).split('/').last]
          as Map<String, dynamic>,
      schemas,
    );
    return;
  }
  for (final union in ['oneOf', 'anyOf']) {
    if (schema.containsKey(union)) {
      var matches = 0;
      for (final item in schema[union] as List) {
        try {
          validateContract(data, item as Map<String, dynamic>, schemas);
          matches++;
        } on ContractFailure {
          /* try the other explicit alternative */
        }
      }
      if (matches == 0 || (union == 'oneOf' && matches != 1)) {
        throw const ContractFailure();
      }
      return;
    }
  }
  final valid = switch (schema['type']) {
    'object' => data is Map<String, Object?>,
    'array' => data is List,
    'string' => data is String,
    'integer' => data is int,
    'number' => data is num,
    'boolean' => data is bool,
    'null' => data == null,
    _ => true,
  };
  if (!valid) throw const ContractFailure();
  if (schema['enum'] is List && !(schema['enum'] as List).contains(data)) {
    throw const ContractFailure();
  }
  if (data is String) {
    if (data.length < (schema['minLength'] as int? ?? 0) ||
        data.length > (schema['maxLength'] as int? ?? 65536)) {
      throw const ContractFailure();
    }
    if (schema['pattern'] is String &&
        !RegExp(schema['pattern'] as String).hasMatch(data)) {
      throw const ContractFailure();
    }
    if (schema['format'] == 'uuid' &&
        !RegExp(
          r'^[a-fA-F0-9]{8}(-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12}$',
        ).hasMatch(data)) {
      throw const ContractFailure();
    }
    if (schema['format'] == 'date-time' &&
        (DateTime.tryParse(data) == null ||
            !RegExp(r'(Z|[+-]\d\d:\d\d)$').hasMatch(data))) {
      throw const ContractFailure();
    }
  }
  if (data is num &&
      schema['minimum'] is num &&
      data < (schema['minimum'] as num)) {
    throw const ContractFailure();
  }
  if (data is List && schema['items'] is Map<String, dynamic>) {
    for (final value in data) {
      validateContract(value, schema['items'] as Map<String, dynamic>, schemas);
    }
  }
  if (data is Map<String, Object?>) {
    final properties = schema['properties'] as Map<String, dynamic>? ?? {};
    for (final key in schema['required'] as List? ?? []) {
      if (!data.containsKey(key)) throw const ContractFailure();
    }
    for (final entry in data.entries) {
      final child = properties[entry.key];
      if (child != null) {
        validateContract(entry.value, child as Map<String, dynamic>, schemas);
      } else if (schema['additionalProperties'] == false) {
        throw const ContractFailure();
      }
    }
  }
}
