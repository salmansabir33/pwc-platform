"""Opt-in full regression runner: validates actual HTTP results, not mocks.

Never imports fixtures/writes a schema from test results or prints credentials.
"""
import re
from unittest.mock import patch
from django.test.client import Client
from django.test.runner import DiscoverRunner
from .validation import document, validate_response


class ContractRunner(DiscoverRunner):
    def run_tests(self, *args, **kwargs):
        original = Client.request
        paths = [(re.compile("^" + re.sub(r"\{[^}]+\}", "[^/]+", path) + "$"), path)
                 for path in document()["paths"]]
        checked = set()

        def request(client, **parameters):
            response = original(client, **parameters)
            actual = response.wsgi_request.path
            for pattern, path in paths:
                if pattern.fullmatch(actual):
                    method = response.wsgi_request.method.lower()
                    try:
                        validate_response(path, method, response)
                    except Exception as error:
                        # Do not include potentially sensitive validation instances.
                        raise AssertionError(f"Wire contract mismatch: {method} {path} status={response.status_code}; {type(error).__name__}") from None
                    checked.add((path, method, response.status_code))
                    break
            return response

        with patch.object(Client, "request", request):
            result = super().run_tests(*args, **kwargs)
        print(f"Contract runner checked {len(checked)} distinct route/method/status combinations")
        return result
