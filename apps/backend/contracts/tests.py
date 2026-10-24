"""Contract guard regressions, including deliberately incompatible mutations."""
from copy import deepcopy
import inspect
import json
from django.test import SimpleTestCase, override_settings
from django.urls import resolve
from jsonschema import ValidationError
from openapi_spec_validator import validate
from .check import check_examples, check_legacy, check_metadata
from .generate import routes, source_lock, PACKAGE, compatibility, check_compatibility
from .schema import build
from .validation import validate_schema, validate_response


class ContractTests(SimpleTestCase):
    def test_valid_openapi_and_examples(self):
        doc = build()
        validate(deepcopy(doc))
        check_metadata(doc)
        check_legacy(doc)
        check_examples(doc)

    def test_exact_inventory_and_frozen_source(self):
        doc = build()
        self.assertEqual(routes(), set(doc['paths']))
        self.assertEqual(source_lock(), json.loads((PACKAGE/'source-lock.json').read_text()))
        before = json.loads((PACKAGE/'compatibility-v1.json').read_text())
        check_compatibility(before, compatibility(doc))

    def test_breaking_changes_fail_frozen_compatibility(self):
        before = compatibility(build())
        for section in ("operations", "schemas"):
            after = deepcopy(before)
            after[section].pop(next(iter(after[section])))
            with self.assertRaises(AssertionError): check_compatibility(before, after)
        after = deepcopy(before)
        after['security'] = 'different transport'
        with self.assertRaises(AssertionError): check_compatibility(before, after)

    def test_public_registration_fields_derive_from_actual_closure(self):
        doc = build()
        for path, methods in doc['paths'].items():
            if '/registration/' not in path and '/password-reset/' not in path:
                continue
            callback = inspect.unwrap(resolve(path).func)
            fields = inspect.getclosurevars(callback).nonlocals['fields']
            schema = methods['post']['requestBody']['content']['application/json']['schema']['$ref'].rsplit('/',1)[1]
            self.assertEqual(fields, set(doc['components']['schemas'][schema]['required']))

    def test_mixed_transport_and_synthetic_context_mutations_rejected(self):
        for mutate in ('transport', 'synthetic'):
            doc = deepcopy(build())
            if mutate == 'transport': doc['paths']['/api/v1/auth/me/']['get']['security'] = [{'browserCookie': [],'mobileBearer': []}]
            else: doc['paths']['/api/v1/ngo-contexts/{organization_uuid}/capabilities/']['get']['parameters'][0]['schema'] = {'type':'string'}
            with self.assertRaises((AssertionError, StopIteration)):
                check_metadata(doc)

    def test_invalid_examples_fail_closed(self):
        for name, body in [('ClearHold', {'intent_id':'not-uuid','password':'synthetic','totp_code':'000000'}),
                           ('SessionEnvelope', {'is_admin':True}),
                           ('IntentRequest', {'operation':'ngo.finance.approve','context':{'kind':'ngo','id':'00000000-0000-4000-8000-000000000001'},'command':{}})]:
            with self.assertRaises(ValidationError):
                validate_schema({'$ref':'#/components/schemas/'+name},body)

    @override_settings(PWC_AUTH_FLOWS_ENABLED=False, PWC_AUTH_SESSIONS_ENABLED=False,
                       PWC_AUTH_MFA_ENABLED=False, PWC_SYNTHETIC_CONTEXT_HTTP_ENABLED=False,
                       ALLOWED_HOSTS=['testserver'])
    def test_disabled_endpoints_do_not_masquerade_as_available(self):
        for path, methods in build()['paths'].items():
            method = next(iter(methods))
            op = methods[method]
            if not op['x-pwc']['gates']:continue
            actual = path.replace('{session_id}','00000000-0000-4000-8000-000000000001').replace('{organization_uuid}','00000000-0000-4000-8000-000000000001')
            examples = json.loads((PACKAGE/'examples-v1.json').read_text())['cases']
            body = next((x['body'] for x in examples if x['operationId']==op['operationId'] and x['kind']=='request'), {})
            response = getattr(self.client,method)(actual, data=json.dumps(body) if method!='get' else {},content_type='application/json',secure=True)
            self.assertEqual(response.status_code,op['x-pwc']['disabled']['status'], path)
            validate_response(path,method,response)
            code=response.json()['error']['code']
            self.assertEqual(code,op['x-pwc']['disabled']['code'])
