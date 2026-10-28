"""Read-only, credential-free observations at operator-supplied real portal hosts.

No rollout toggle or acceptance authority. Never send credentials, unsafe verbs,
follow redirects, persist cookie values, or disable certificate verification.
"""

import argparse
import http.client
from http.cookies import SimpleCookie, CookieError
import ipaddress
import json
from pathlib import Path
import re
import socket
import ssl
import sys
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps/backend"))
from config.environment import origin  # noqa: E402


def portal_pair(ngo, ops):
    result = {}
    for name, value in (("ngo_web", ngo), ("pwc_ops", ops)):
        origin(value, "portal origin")
        parsed = urlsplit(value)
        host = parsed.hostname
        if host.lower() in ("localhost", "backend") or host.lower().endswith(
            (".invalid", ".localhost", ".example", ".test")
        ):
            raise ValueError("Real publicly reviewed portal origins required")
        try:
            ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            raise ValueError("Named portal origins required, not IP literals")
        result[name] = value
    if urlsplit(ngo).hostname.lower() == urlsplit(ops).hostname.lower():
        raise ValueError("Separate portal hosts required")
    return result


def cookie_observations(headers):
    """Emit properties only. Cookie names/values and server strings never escape."""
    cookies = SimpleCookie()
    try:
        for header in headers:
            cookies.load(header)
    except CookieError:
        return {"parseable": False}
    csrf = cookies.get("csrftoken")
    return {
        "parseable": True,
        "session_issued_to_anonymous": "__Host-pwc_session" in cookies,
        "csrf_present": csrf is not None,
        "csrf_secure": bool(csrf and csrf["secure"]),
        "csrf_host_only": bool(csrf and not csrf["domain"]),
        "csrf_root_path": bool(csrf and csrf["path"] == "/"),
        "csrf_safe_same_site": bool(
            csrf and csrf["samesite"].lower() in ("lax", "strict")
        ),
    }


def request_observation(target, path):
    parsed = urlsplit(target)
    context = ssl.create_default_context()  # System CAs, hostname verification ON.
    connection = http.client.HTTPSConnection(
        parsed.hostname, parsed.port or 443, timeout=10, context=context
    )
    try:
        connection.request("GET", path, headers={"Accept": "application/json"})
        response = connection.getresponse()  # No redirect handler, no cookie jar.
        body = response.read(65537)
        observation = {
            "status": response.status,
            "redirect": 300 <= response.status < 400,
            "json_content_type": response.getheader("Content-Type", "")
            .split(";")[0]
            .strip()
            == "application/json",
            "no_store": "no-store" in response.getheader("Cache-Control", "").lower(),
            "no_referrer": response.getheader("Referrer-Policy", "").lower()
            == "no-referrer",
            "credentialed_cors_absent": response.getheader(
                "Access-Control-Allow-Origin"
            )
            is None
            and response.getheader("Access-Control-Allow-Credentials") is None,
            "bounded": len(body) <= 65536,
        }
        if path.endswith("/csrf/"):
            observation["cookies"] = cookie_observations(
                response.headers.get_all("Set-Cookie", [])
            )
            try:
                data = json.loads(body)
                observation["csrf_shape"] = (
                    isinstance(data, dict)
                    and set(data) == {"csrf_token"}
                    and isinstance(data["csrf_token"], str)
                    and bool(re.fullmatch(r"[A-Za-z0-9]{64}", data["csrf_token"]))
                )
            except (ValueError, TypeError):
                observation["csrf_shape"] = False
        return observation
    finally:
        connection.close()


def observe(target):
    parsed = urlsplit(target)
    try:
        addresses = sorted(
            {
                entry[4][0]
                for entry in socket.getaddrinfo(
                    parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM
                )
            }
        )
        if not addresses or any(
            not ipaddress.ip_address(address).is_global for address in addresses
        ):
            return {"observed": False, "failure": "DNS_NOT_PUBLIC"}
        routes = {
            path: request_observation(target, path)
            for path in ("/api/v1/health/", "/api/v1/auth/csrf/", "/api/v1/auth/me/")
        }
        return {
            "observed": True,
            "dns_addresses": addresses,
            "system_ca_tls_verified": True,
            "routes": routes,
        }
    except ssl.SSLCertVerificationError:
        return {"observed": False, "failure": "TLS_CERTIFICATE_REJECTED"}
    except (OSError, ssl.SSLError, http.client.HTTPException, ValueError):
        return {"observed": False, "failure": "NETWORK_OR_PROTOCOL_UNAVAILABLE"}


def main(args=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ngo-origin", required=True)
    parser.add_argument("--ops-origin", required=True)
    parsed = parser.parse_args(args)
    try:
        targets = portal_pair(parsed.ngo_origin, parsed.ops_origin)
    except ValueError:
        parser.error(
            "Invalid, non-real or non-separated exact HTTPS portal origins (values redacted)"
        )
    result = {
        "production_enablement": "BLOCKED_PENDING_INDEPENDENT_ACCEPTANCE",
        "scope": "read_only_external_observations_not_acceptance",
        "portals": {
            name: {"origin": target, **observe(target)}
            for name, target in targets.items()
        },
        "unverified": [
            "login_mfa_recovery_and_revocation",
            "upstream_tls_and_peer_restriction",
            "host_and_header_spoofing",
            "proxy_ip_nat_abuse_budgets",
            "certificate_rotation",
            "logging_retention_and_secret_redaction",
            "deployment_config_and_independent_signoff",
        ],
    }
    print(json.dumps(result, indent=2))
    return 0 if all(value["observed"] for value in result["portals"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
