"""Shared offline schema/example and Django-response validators. Never log payloads."""
import json
from functools import lru_cache
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker

PACKAGE = Path(__file__).resolve().parents[3] / "packages/api-contracts"


@lru_cache
def document():
    return json.loads((PACKAGE / "openapi-v1.json").read_text())


def validate_schema(schema, value):
    # A wrapper root makes nested local references resolve into the OpenAPI document.
    root = dict(document())
    root.update(schema)
    Draft202012Validator(root, format_checker=FormatChecker()).validate(value)


def validate_response(path, method, response):
    methods = document()["paths"][path]
    operation = methods.get(method) or next(iter(methods.values()))
    status = str(response.status_code)
    if method not in methods and status != "405":
        # Plain Django mixed-credential checks precede method checks.
        assert status in ("400", "403", "404"), "Unexpected unsupported-method behavior"
    if response.status_code < 400:
        assert status in operation["responses"], "Undocumented successful status"
    if status == "204" or method == "head":
        assert not response.content, "Body on HEAD/204"
        if status in operation["responses"]:
            for name, header in operation["responses"][status].get("headers", {}).items():
                if "const" in header["schema"]:
                    assert response.get(name) == header["schema"]["const"], "Security header drift: " + name
            validate_vary(operation, response)
        return
    if response.get("Content-Type", "").partition(";")[0].strip().lower() != "application/json":
        assert response.status_code >= 400, "Non-JSON success drift"
        return  # Documented framework/proxy errors; never a successful API result.
    assert status in operation["responses"], f"Undocumented status: {method} {path} {status}"
    item = operation["responses"][status]
    validate_schema(item["content"]["application/json"]["schema"], json.loads(response.content))
    for name, header in item.get("headers", {}).items():
        if "const" in header["schema"]:
            assert response.get(name) == header["schema"]["const"], "Security header drift: " + name

    validate_vary(operation, response)


def validate_vary(operation, response):
    if operation["x-pwc"]["availability"] == "synthetic-only":
        tokens = {value.strip().lower() for value in response.get("Vary", "").split(",")}
        assert {"cookie", "authorization"} <= tokens, "Synthetic credential Vary drift"
