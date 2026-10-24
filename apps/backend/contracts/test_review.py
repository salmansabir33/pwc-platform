"""Confirmed integration-review regressions; synthetic responses only."""
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.http import HttpResponse, JsonResponse
from django.test import SimpleTestCase

from .check import check_examples
from .generate import compatibility, check_compatibility, main, encoded
from .schema import build
from .validation import validate_response


class ReviewRegressions(SimpleTestCase):
    def test_undocumented_empty_success_does_not_bypass_schema(self):
        response = HttpResponse(status=204)
        response['Cache-Control'] = 'no-store'
        response['Referrer-Policy'] = 'no-referrer'
        with self.assertRaises(AssertionError):
            validate_response('/api/v1/auth/me/', 'get', response)

    def test_json_prefix_is_not_a_json_media_type(self):
        response = JsonResponse({'status': 'ok', 'service': 'pwc-api'})
        response['Content-Type'] = 'application/jsonp'
        with self.assertRaises(AssertionError):
            validate_response('/api/v1/health/', 'get', response)

    def test_synthetic_vary_must_partition_both_credentials(self):
        response = JsonResponse({'results': [], 'next_cursor': None})
        response['Cache-Control'] = 'no-store'
        response['Referrer-Policy'] = 'no-referrer'
        response['Vary'] = 'Cookie'
        with self.assertRaises(AssertionError):
            validate_response('/api/v1/me/ngo-contexts/', 'get', response)

    def test_valid_json_charset_and_vary_case_order(self):
        response = JsonResponse({'results': [], 'next_cursor': None})
        response['Cache-Control'] = 'no-store'
        response['Referrer-Policy'] = 'no-referrer'
        response['Vary'] = 'authorization, COOKIE, Accept-Encoding'
        response['Content-Type'] = 'application/json; charset=utf-8'
        validate_response('/api/v1/me/ngo-contexts/', 'get', response)

    def test_only_error_examples_cannot_cover_a_success(self):
        from .generate import PACKAGE
        examples = json.loads((PACKAGE / 'examples-v1.json').read_text())
        examples['cases'] = [case for case in examples['cases'] if not (
            case['operationId'] == 'webLogin' and case['kind'] == 'response' and case['status'] < 300)]
        with TemporaryDirectory() as directory:
            package = Path(directory)
            (package / 'examples-v1.json').write_text(encoded(examples))
            with patch('contracts.check.PACKAGE', package):
                with self.assertRaises(AssertionError):
                    check_examples(build())

    def test_missing_request_examples_are_detected(self):
        from .generate import PACKAGE
        examples = json.loads((PACKAGE / 'examples-v1.json').read_text())
        examples['cases'] = [case for case in examples['cases'] if not (
            case['operationId'] == 'clearHold' and case['kind'] == 'request')]
        with TemporaryDirectory() as directory:
            package = Path(directory)
            (package / 'examples-v1.json').write_text(encoded(examples))
            with patch('contracts.check.PACKAGE', package):
                with self.assertRaises(AssertionError):
                    check_examples(build())

    def test_global_security_and_protocol_changes_cannot_evade_freeze(self):
        before = build()
        for key in ('servers', 'openapi', 'x-pwc-security'):
            after = deepcopy(before)
            after[key] = [] if key == 'servers' else 'changed'
            with self.assertRaises(AssertionError):
                check_compatibility(compatibility(before), compatibility(after))

    def test_compatibility_failure_never_overwrites_checked_files(self):
        original = build()
        changed = deepcopy(original)
        changed['paths']['/api/v1/auth/me/']['get']['security'] = []
        with TemporaryDirectory() as directory:
            package = Path(directory)
            (package / 'generated').mkdir()
            (package / 'compatibility-v1.json').write_text(encoded(compatibility(original)))
            for path in ('openapi-v1.json', 'source-lock.json', 'generated/browser-operations.ts'):
                (package / path).write_text('preserved\n')
            with patch('contracts.generate.PACKAGE', package), patch('contracts.generate.build', return_value=changed), patch('sys.argv', ['contracts.generate']):
                with self.assertRaises(AssertionError):
                    main()
            for path in ('openapi-v1.json', 'source-lock.json', 'generated/browser-operations.ts'):
                self.assertEqual((package / path).read_text(), 'preserved\n')
