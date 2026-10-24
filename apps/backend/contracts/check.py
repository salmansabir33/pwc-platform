"""Offline validation, executable fixtures and historical wire-key compatibility."""
import json
from copy import deepcopy
from openapi_spec_validator import validate
from .generate import PACKAGE, main
from .validation import document, validate_schema


def check_metadata(doc):
    ids = set()
    for path, methods in doc["paths"].items():
        assert path.startswith('/api/v1/')
        for method, op in methods.items():
            assert op['operationId'] not in ids
            ids.add(op['operationId'])
            meta = op['x-pwc']
            assert meta['availability'] in ('public-implemented', 'default-disabled', 'synthetic-only')
            if 'ngo-contexts' in path:
                assert meta['availability'] == 'synthetic-only'
                assert method in ('get', 'head') and 'requestBody' not in op
                if '{' in path:
                    assert op['parameters'][0]['schema'].get('format') == 'uuid'
                    assert op['parameters'][0]['name'] == 'organization_uuid'
            if meta['gates']:
                disabled = meta['disabled']
                assert str(disabled['status']) in op['responses']
            if meta['transport'] == 'personal':
                assert {'mobileBearer': []} in op['security']
                cookie = next(x for x in op['security'] if 'browserCookie' in x)
                assert ('csrfHeader' in cookie) == (method not in ('get', 'head'))
            if meta['transport'].startswith('native-'):
                assert op['security'] == []  # Body proof only; no ambient cookie/bearer.
    assert doc['x-pwc-security']['web_network'] == 'disabled'


def check_legacy(doc):
    schemas = doc['components']['schemas']
    mappings = {
        'auth-sessions-v1.fixtures.json': {'web_success_keys':'SessionEnvelope', 'mobile_success_keys':'MobileSession', 'me_success_keys':'Me'},
        'auth-mfa-v1.fixtures.json': {'preauth_keys':'Preauth', 'enrollment_keys':'Enrollment', 'activation_keys':'Activation', 'intent_keys':'Intent', 'step_up_keys':'Assurance', 'factor_status_keys':'MfaStatus'},
        'ngo-contexts-v1.fixtures.json': {'discovery_keys':'Discovery','capability_keys':'Capabilities','context_keys':'Context','resource_keys':'SyntheticResource'},
    }
    for file, fields in mappings.items():
        legacy = json.loads((PACKAGE / file).read_text())
        for key, schema in fields.items():
            assert set(legacy[key]) == set(schemas[schema]['properties']), (file, key)
    auth = json.loads((PACKAGE/'auth-sessions-v1.fixtures.json').read_text())
    validate_schema({'$ref':'#/components/schemas/Login'}, auth['login_request'])
    validate_schema({'$ref':'#/components/schemas/Refresh'}, auth['refresh_request'])
    assert auth['cookie']['name'] == doc['components']['securitySchemes']['browserCookie']['name']
    mfa = json.loads((PACKAGE/'auth-mfa-v1.fixtures.json').read_text())
    assert mfa['hold_clear_requires_new_single_use_totp'] is True
    assert set(mfa['personal_operations']) == set(schemas['IntentRequest']['oneOf'][0]['properties']['operation']['enum']) | {'sessions.revoke'}


def check_examples(doc):
    examples = json.loads((PACKAGE / 'examples-v1.json').read_text())
    assert examples['contract_version'] == doc['info']['version']
    ops = {op['operationId']: op for methods in doc['paths'].values() for op in methods.values()}
    for case in examples['cases']:
        op = ops[case['operationId']]
        if case['kind'] == 'request':
            schema = op['requestBody']['content']['application/json']['schema']
        else:
            schema = op['responses'][str(case['status'])]['content']['application/json']['schema']
        validate_schema(schema, case['body'])
    covered = {(c['operationId'], str(c['status'])) for c in examples['cases']
               if c['kind'] == 'response' and 200 <= c['status'] < 300}
    expected = {(op['operationId'], code) for op in ops.values()
                for code, result in op['responses'].items()
                if code.startswith('2') and 'application/json' in result.get('content', {})}
    assert covered >= expected, expected - covered
    requests = {c['operationId'] for c in examples['cases'] if c['kind'] == 'request'}
    expected_requests = {op['operationId'] for op in ops.values() if 'requestBody' in op}
    assert requests >= expected_requests, expected_requests - requests


if __name__ == '__main__':
    main()
    doc = document()
    validate(deepcopy(doc))
    check_metadata(doc)
    check_legacy(doc)
    check_examples(doc)
    print('OpenAPI 3.1, security metadata, historical keys and checked examples passed')
