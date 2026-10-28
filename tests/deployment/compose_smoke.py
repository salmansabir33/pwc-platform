"""Hosted-only real Compose/TLS/PostgreSQL smoke; A evidence, never B/C/D.

Run as root on an isolated disposable CI runner, never on a real host. Generates
only ephemeral synthetic secrets outside Git and never prints response bodies.
"""

import http.client
import json
import os
from pathlib import Path
import socket
import ssl
import subprocess
import sys
import tempfile
import time
import traceback

from staging_fixtures import certificates, config, deploy, resign_app, ROOT

BASES = {
    "python": "python:3.12-slim-bookworm",
    "node": "node:22.22.3-bookworm-slim",
    "nginx": "nginx:stable-bookworm",
    "postgres": "postgres:16-bookworm",
    "haproxy": "haproxy:3.2-bookworm",
}


def run(*args, data=None):
    result = subprocess.run(
        args, input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if result.returncode:
        # Docker/build/SQL output can contain sensitive data: never echo it.
        raise RuntimeError(
            "Synthetic stack command failed (output redacted): " + args[0]
        )
    return result.stdout


def main():
    if os.getuid() != 0 or os.environ.get("PWC_DISPOSABLE_CI") != "YES":
        raise RuntimeError("Only disposable root CI is permitted")
    checks = []
    with tempfile.TemporaryDirectory(prefix="pwc-staging-synthetic-") as directory:
        root = Path(directory)
        value = config(root)
        certificates(value)
        for name, tag in BASES.items():
            run("docker", "pull", tag)
            value["images"][name] = json.loads(run("docker", "image", "inspect", tag))[
                0
            ]["RepoDigests"][0]
        config_path = root / "config.json"
        config_path.write_text(json.dumps(value))
        config_path.chmod(0o600)
        manifest = deploy.render(config_path, root / "rendered", synthetic=True)
        command = ["docker", "compose", "--env-file", "/dev/null", "-f", str(manifest)]
        stack = str(ROOT / "infra/staging/stack.sh")
        built = [
            value["project"] + "-" + name + ":" + value["release"]
            for name in ("app", "ngo", "ops")
        ]
        try:
            print("Building three separate staging images", flush=True)
            run(stack, str(manifest), "build")
            print(
                "Starting private PostgreSQL, migrations, mTLS application and portals",
                flush=True,
            )
            run(stack, str(manifest), "up")
            checks.append("deterministic-migration-before-ready")
            # A second migration is safe, and an ordinary restart does not migrate.
            run(
                *command,
                "--profile",
                "maintenance",
                "run",
                "--rm",
                "--no-deps",
                "migrate",
            )
            run(*command, "up", "-d", "--wait", "--wait-timeout", "180")
            checks.append("idempotent-migrations")
            context = ssl.create_default_context(cafile=value["files"]["public_ca"])

            def request(host, path, headers=None, method="GET", body=None):
                # Trusted ephemeral CA, genuine host SNI, local socket only.
                connection = http.client.HTTPSConnection(
                    host, 443, context=context, timeout=10
                )
                connection._create_connection = lambda *args, **kwargs: (
                    socket.create_connection(("127.0.0.1", 443), timeout=10)
                )
                try:
                    connection.request(method, path, body=body, headers=headers or {})
                    response = connection.getresponse()
                    return (
                        response.status,
                        dict(response.getheaders()),
                        response.read(1024 * 1024),
                    )
                finally:
                    connection.close()

            for name in ("ngo", "ops"):
                host = value[name + "_host"]
                status, headers, body = request(host, "/")
                assert status == 200 and b"<html" in body
                for header in (
                    "Strict-Transport-Security",
                    "Content-Security-Policy",
                    "X-Frame-Options",
                    "X-Content-Type-Options",
                    "Referrer-Policy",
                    "Cache-Control",
                ):
                    assert header in headers
                status, headers, body = request(
                    host,
                    "/api/v1/health/",
                    {
                        "Forwarded": "host=evil.test;proto=http",
                        "X-Forwarded-Host": "evil.test",
                        "X-Forwarded-Proto": "http",
                        "X-Forwarded-Port": "80",
                        "X-Forwarded-For": "203.0.113.1",
                    },
                )
                assert (
                    status == 200
                    and json.loads(body)["service"] == "pwc-api"
                    and "Location" not in headers
                )
                assert not any(
                    key.lower().startswith("access-control-allow") for key in headers
                )
                assert request(host, "/api/v1/directory/")[0] == 200
                # Disabled auth is asserted, not bypassed for infrastructure tests.
                assert request(host, "/api/v1/auth/me/")[0] in (401, 403, 404, 503)
                assert request(host, "/api/v1/not-a-route/")[0] == 404
                checks.append(name + "-exact-tls-static-api-no-spoofing-no-cors")
                # Canonical authority only; never route a sibling Host using this SNI.
                for authority in (
                    value["ops_host"] if name == "ngo" else value["ngo_host"],
                    "unknown.pwc.test",
                    host + ":443",
                    host + ":444",
                ):
                    try:
                        status, _, _ = request(
                            host, "/api/v1/health/", {"Host": authority}
                        )
                        assert status >= 400
                    except (http.client.RemoteDisconnected, ConnectionResetError):
                        pass
                # Nginx must reject duplicate authority and ambiguous framing.
                for raw in (
                    f"GET /api/v1/health/ HTTP/1.1\r\nHost: {host}\r\nHost: {host}\r\nConnection: close\r\n\r\n",
                    f"POST /api/v1/health/ HTTP/1.1\r\nHost: {host}\r\nContent-Length: 1\r\nTransfer-Encoding: chunked\r\nConnection: close\r\n\r\n0\r\n\r\n",
                ):
                    with context.wrap_socket(
                        socket.create_connection(("127.0.0.1", 443), timeout=10),
                        server_hostname=host,
                    ) as client:
                        client.sendall(raw.encode())
                        response = client.recv(1024)
                        assert b" 400 " in response
                checks.append(name + "-authority-framing-rejection")
            # HTTP is not published and cannot redirect submitted secrets.
            for port in (80, 5432, 8000, 8443):
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=2):
                        raise AssertionError("Unexpected published ingress")
                except (ConnectionRefusedError, TimeoutError):
                    pass
            checks.append("no-plaintext-app-or-public-database")
            # Server requires authenticated clients and refuses plaintext at WSGI.
            probe = """import http.client, ssl, socket
c = ssl.create_default_context(cafile='/run/secrets/app_ca')
try:
 x=http.client.HTTPSConnection('app.pwc.internal',8443,context=c,timeout=3)
 x.request('GET','/api/v1/health/',headers={'Host':'ngo.pwc.test'})
 x.getresponse()
 raise SystemExit(1)
except (ssl.SSLError, ConnectionError, http.client.HTTPException): pass
s=socket.create_connection(('app.pwc.internal',8443),timeout=3)
s.sendall(b'GET /api/v1/health/ HTTP/1.1\\r\\nHost: ngo.pwc.test\\r\\n\\r\\n')
try:
 assert b'200 OK' not in s.recv(1024)
except ConnectionError: pass
s.close()
"""
            run(*command, "exec", "-T", "app", "python", "-c", probe)
            checks.append("mtls-peer-and-plaintext-refusal")
            # Inspect effective settings without secrets; reject authority writes.
            settings_probe = """import sys
sys.path.insert(0,'/app/infra/staging')
import runtime
runtime.environment()
import django
django.setup()
from django.conf import settings as s
from config.environment import FLAGS
assert not any(getattr(s,"DEBUG" if k=="DJANGO_DEBUG" else k) for k in FLAGS)
assert s.SECURE_PROXY_SSL_HEADER is None
assert not s.USE_X_FORWARDED_HOST and not s.USE_X_FORWARDED_PORT
assert s.SESSION_COOKIE_SECURE and s.SESSION_COOKIE_HTTPONLY and s.SESSION_COOKIE_SAMESITE=='Lax'
assert s.SESSION_COOKIE_DOMAIN is None and s.SESSION_COOKIE_PATH=='/'
assert s.CSRF_COOKIE_SECURE and s.CSRF_COOKIE_DOMAIN is None and s.CSRF_TRUSTED_ORIGINS==[]
from django.db import connection
with connection.cursor() as c:
 c.execute("SELECT has_table_privilege(current_user,'accounts_user','INSERT'), has_table_privilege(current_user,'organizations_organizationaccess','UPDATE'), has_table_privilege(current_user,'accounts_authsession','INSERT')")
 assert c.fetchone() == (False,False,False)
 c.execute('SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()')
 assert c.fetchone() == (True,)
"""
            run(*command, "exec", "-T", "app", "python", "-c", settings_probe)
            checks.append("effective-security-cookies-gates-bounded-role-db-tls")
            # Prove shared aggregate budget and audit INSERT works at threshold.
            for name in ("ngo", "ops"):
                for _ in range(29):
                    assert (
                        request(value[name + "_host"], "/api/v1/directory/")[0] == 200
                    )
                assert request(value[name + "_host"], "/api/v1/directory/")[0] == 429
            checks.append("aggregate-proxy-budgets-no-relaxation-audit-at-threshold")
            # Bad upstream cert names must fail at Nginx, not silently fall back.
            app_cert = Path(value["files"]["app_cert"])
            app_key = Path(value["files"]["app_key"])
            original_cert, original_key = app_cert.read_bytes(), app_key.read_bytes()
            app_cert.write_bytes(Path(value["files"]["db_cert"]).read_bytes())
            app_key.write_bytes(Path(value["files"]["db_key"]).read_bytes())
            run(*command, "restart", "app")
            time.sleep(4)
            assert request(value["ngo_host"], "/api/v1/health/")[0] == 502
            app_cert.write_bytes(original_cert)
            app_key.write_bytes(original_key)
            # Correct issuing CA, but wrong SAN: exercise hostname verification.
            resign_app(value, hostname="wrong.pwc.internal")
            try:
                deploy.files(value)
                raise AssertionError("Wrong-name leaf accepted")
            except ValueError:
                pass
            run(*command, "restart", "app")
            time.sleep(4)
            assert request(value["ngo_host"], "/api/v1/health/")[0] == 502
            # Correct CA/name but expired: validity must fail, not just trust.
            resign_app(value, days=0)
            try:
                deploy.files(value)
                raise AssertionError("Expired leaf accepted")
            except subprocess.CalledProcessError:
                pass
            run(*command, "restart", "app")
            time.sleep(4)
            assert request(value["ops_host"], "/api/v1/health/")[0] == 502
            app_cert.write_bytes(original_cert)
            run(*command, "restart", "app")
            run(*command, "up", "-d", "--wait", "--wait-timeout", "180")
            checks.append("untrusted-wrong-name-upstream-fails-closed-and-recovers")
            # Snapshot/fresh restore round-trip including retained grants via migrate.
            backup = run(stack, str(manifest), "backup")
            assert backup.startswith(b"PGDMP")
            run(*command, "stop", "gateway", "ngo", "ops", "app")
            # Prove fresh restore without destroying volume or existing records.
            run(
                *command,
                "exec",
                "-T",
                "db",
                "psql",
                "-U",
                "pwc_owner",
                "-d",
                "pwc_staging",
                "-c",
                "DROP SCHEMA public CASCADE; CREATE SCHEMA public AUTHORIZATION pwc_owner;",
            )
            os.environ["PWC_CONFIRM_FRESH_RESTORE"] = "YES"
            run(stack, str(manifest), "restore", data=backup)
            run(stack, str(manifest), "up")
            assert request(value["ngo_host"], "/api/v1/health/")[0] == 200
            checks.append("backup-fresh-restore-regrant-and-ready")
            # Ingest secret-like canaries but never include request/response logs.
            canary = "synthetic-sensitive-log-canary-" + os.urandom(16).hex()
            request(
                value["ngo_host"],
                "/api/v1/not-found/?proof=" + canary,
                {
                    "Cookie": "__Host-pwc_session=" + canary,
                    "Authorization": "Bearer " + canary,
                },
                "POST",
                canary,
            )
            logs = run(*command, "logs", "--no-color")
            assert canary.encode() not in logs
            for name in deploy.PASSWORDS:
                assert Path(value["files"][name]).read_bytes().strip() not in logs
            checks.append("secret-free-request-and-container-logs")
            # Renderer rejects unsafe file perms, mismatched keys, expiry, bad CA.
            key = Path(value["files"]["ngo_key"])
            key.chmod(0o644)
            try:
                deploy.files(value)
                raise AssertionError("World-readable key accepted")
            except ValueError:
                pass
            key.chmod(0o640)
            invalid = json.loads(json.dumps(value))
            invalid["files"]["ngo_key"] = value["files"]["ops_key"]
            try:
                deploy.files(invalid)
                raise AssertionError("Mismatched key accepted")
            except ValueError:
                pass
            invalid = json.loads(json.dumps(value))
            invalid["files"]["public_ca"] = value["files"]["db_ca"]
            try:
                deploy.files(invalid)
                raise AssertionError("Untrusted certificate accepted")
            except (ValueError, subprocess.CalledProcessError):
                pass
            checks.append("render-rejects-unsafe-permissions-keys-untrusted-chain")
            report = {
                "category": "A_SYNTHETIC_COMPOSE_ONLY",
                "B_deployed": False,
                "C_independently_accepted": False,
                "D_credential_transport_authorized": False,
                "release": value["release"],
                "base_images": value["images"],
                "checks": checks,
            }
            cache = ROOT / ".cache"
            cache.mkdir(exist_ok=True)
            (cache / "staging-smoke.json").write_text(json.dumps(report, indent=2))
            # Scanner consumes only image names; no deployment configuration/artifact.
            (cache / "staging-images.txt").write_text(
                "\n".join(
                    built + [value["images"][name] for name in ("postgres", "haproxy")]
                )
                + "\n"
            )
            print(
                "Synthetic Compose passed: "
                + str(len(checks))
                + " checks; B/C/D not accepted",
                flush=True,
            )
        except Exception:
            status = subprocess.run(
                [*command, "ps", "-a", "--format", "json"],
                capture_output=True,
                text=True,
            )
            for line in status.stdout.splitlines():
                try:
                    item = json.loads(line)
                    print(
                        "::notice title=Redacted container state::"
                        + json.dumps(
                            {
                                key: item.get(key)
                                for key in ("Service", "State", "Health", "ExitCode")
                            }
                        )
                    )
                except (ValueError, TypeError):
                    pass
            raise
        finally:
            run(*command, "down", "--volumes", "--remove-orphans")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        frames = [
            f"{Path(frame.filename).name}:{frame.lineno}"
            for frame in traceback.extract_tb(error.__traceback__)
            if Path(frame.filename).name == "compose_smoke.py"
        ]
        print(
            "::error title=Synthetic staging failure::"
            + type(error).__name__
            + " at "
            + ",".join(frames),
            file=sys.stderr,
        )
        print(
            "Synthetic Compose test failed; output redacted; no host acceptance",
            file=sys.stderr,
        )
        raise SystemExit(1) from None
