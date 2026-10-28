"""Offline, fail-closed staging renderer/operator CLI. Never activates auth.

Generated configuration and deployment-managed PKI/secrets belong outside Git.
"""

import argparse
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "infra/staging"
PASSWORDS = ("django_secret", "db_owner_password", "db_app_password", "abuse_key")
PAIRS = ("ngo", "ops", "app", "db", "ngo_client", "ops_client", "health")
FILES = (
    *PASSWORDS,
    *(name + suffix for name in PAIRS for suffix in ("_cert", "_key")),
    "public_ca",
    "app_ca",
    "db_ca",
    "client_ca",
)
IMAGES = ("python", "node", "nginx", "postgres", "haproxy")


def fail():
    raise ValueError("Unsafe/incomplete staging configuration (values redacted)")


def unique(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            fail()
        value[key] = item
    return value


def metadata(value, synthetic=False):
    if not isinstance(value, dict) or set(value) != {
        "project",
        "release",
        "ngo_host",
        "ops_host",
        "images",
        "files",
    }:
        fail()
    if not isinstance(value["project"], str) or not isinstance(value["release"], str):
        fail()
    if not re.fullmatch(
        r"pwc-staging(?:-[a-z0-9-]{1,24})?", value["project"]
    ) or not re.fullmatch(r"[0-9a-f]{40}", value["release"]):
        fail()
    for key in ("ngo_host", "ops_host"):
        host = value[key]
        if (
            not isinstance(host, str)
            or len(host) > 253
            or host != host.lower()
            or not re.fullmatch(
                r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+",
                host,
            )
        ):
            fail()
        try:
            ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            fail()
        if host.endswith((".invalid", ".localhost")) or (
            not synthetic
            and host.endswith(
                (".test", ".example", ".example.org", ".example.com", ".example.net")
            )
        ):
            fail()
    if value["ngo_host"] == value["ops_host"]:
        fail()
    if not isinstance(value["images"], dict) or set(value["images"]) != set(IMAGES):
        fail()
    for image in value["images"].values():
        if not isinstance(image, str) or not re.fullmatch(
            r"[a-zA-Z0-9./_:-]+@sha256:[a-f0-9]{64}", image
        ):
            fail()
    if not isinstance(value["files"], dict) or set(value["files"]) != set(FILES):
        fail()
    for path in value["files"].values():
        if (
            not isinstance(path, str)
            or any(c in path for c in ("$", "\n", "\r", ":"))
            or not Path(path).is_absolute()
            or Path(path).resolve().is_relative_to(ROOT)
        ):
            fail()
    return value


def checked(command):
    result = subprocess.run(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    return result.stdout


def files(value):
    paths = value["files"]
    secrets = []
    for name, path in paths.items():
        file = Path(path)
        if file.is_symlink() or not file.is_file():
            fail()
        if name.endswith("_cert") or name.endswith("_ca"):
            if b"PRIVATE KEY" in file.read_bytes():
                fail()
        if name in PASSWORDS or name.endswith("_key"):
            stat = file.stat()
            if (stat.st_mode & 0o777) not in {0o600, 0o640} or not (
                (stat.st_uid == 10001 and stat.st_mode & 0o400)
                or (
                    stat.st_uid in {0, 10001}
                    and stat.st_gid == 10001
                    and stat.st_mode & 0o040
                )
            ):
                fail()
        if name in PASSWORDS:
            text = file.read_text().strip()
            if (
                len(text) < (50 if name == "django_secret" else 32)
                or len(set(text)) < 12
                or any(
                    x in text.lower()
                    for x in ("test-only", "replace-", "example", "password")
                )
                or any(ord(x) < 33 or ord(x) > 126 for x in text)
            ):
                fail()
            secrets.append(text)
    if len(set(secrets)) != len(secrets):
        fail()
    if (
        len(
            {
                Path(paths[name]).read_bytes()
                for name in ("public_ca", "app_ca", "db_ca", "client_ca")
            }
        )
        != 4
    ):
        fail()
    public_keys = set()
    for name in PAIRS:
        cert, key = paths[name + "_cert"], paths[name + "_key"]
        checked(["openssl", "x509", "-in", cert, "-checkend", "604800", "-noout"])
        if checked(["openssl", "x509", "-in", cert, "-pubkey", "-noout"]) != checked(
            ["openssl", "pkey", "-in", key, "-pubout"]
        ):
            fail()
        public_key = checked(["openssl", "x509", "-in", cert, "-pubkey", "-noout"])
        if public_key in public_keys:
            fail()
        public_keys.add(public_key)
        client = name.endswith("client") or name == "health"
        ca = (
            "client_ca"
            if client
            else "public_ca"
            if name in ("ngo", "ops")
            else name + "_ca"
        )
        command = [
            "openssl",
            "verify",
            "-CAfile",
            paths[ca],
            "-untrusted",
            cert,
            "-purpose",
            "sslclient" if client else "sslserver",
        ]
        if not client:
            host = (
                value[name + "_host"]
                if name in ("ngo", "ops")
                else name + ".pwc.internal"
            )
            san = checked(
                ["openssl", "x509", "-in", cert, "-noout", "-ext", "subjectAltName"]
            ).decode()
            if re.findall(r"DNS:([^,\s]+)", san) != [host] or "IP Address:" in san:
                fail()
            command += ["-verify_hostname", host]
        checked([*command, cert])


def portal(host):
    return f'''pid /tmp/nginx.pid;
error_log /dev/null;
events {{ worker_connections 256; }}
http {{
  include /etc/nginx/mime.types;
  default_type application/octet-stream;
  access_log off;
  server_tokens off;
  ssl_protocols TLSv1.2 TLSv1.3;
  client_body_temp_path /tmp/body;
  proxy_temp_path /tmp/proxy;
  fastcgi_temp_path /tmp/fastcgi;
  uwsgi_temp_path /tmp/uwsgi;
  scgi_temp_path /tmp/scgi;
  client_max_body_size 16k;
  server {{
    listen 8443 ssl default_server;
    ssl_reject_handshake on;
  }}
  server {{
    listen 8443 ssl;
    server_name {host};
    if ($http_host != "{host}") {{ return 444; }}
    if ($ssl_server_name != "{host}") {{ return 444; }}
    ssl_certificate /run/secrets/portal_cert;
    ssl_certificate_key /run/secrets/portal_key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_session_tickets off;
    add_header Strict-Transport-Security "max-age=300" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header Referrer-Policy no-referrer always;
    add_header Cache-Control no-store always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'" always;
    location /api/ {{
      proxy_pass https://app.pwc.internal:8443;
      proxy_ssl_verify on;
      proxy_ssl_verify_depth 3;
      proxy_ssl_trusted_certificate /run/secrets/app_ca;
      proxy_ssl_server_name on;
      proxy_ssl_name app.pwc.internal;
      proxy_ssl_certificate /run/secrets/client_cert;
      proxy_ssl_certificate_key /run/secrets/client_key;
      proxy_http_version 1.1;
      proxy_pass_request_headers off;
      proxy_set_header Host {host};
      proxy_set_header Cookie $http_cookie;
      proxy_set_header Authorization $http_authorization;
      proxy_set_header X-CSRFToken $http_x_csrftoken;
      proxy_set_header Origin $http_origin;
      proxy_set_header Referer $http_referer;
      proxy_set_header Sec-Fetch-Site $http_sec_fetch_site;
      proxy_set_header Content-Type $http_content_type;
      proxy_set_header Accept $http_accept;
      proxy_set_header Connection close;
      proxy_connect_timeout 5s;
      proxy_read_timeout 35s;
      proxy_intercept_errors off;
      proxy_redirect off;
      proxy_cache off;
    }}
    location / {{ root /srv/portal; try_files $uri $uri/ /index.html; }}
  }}
}}
'''


def compose(value, destination):
    image, secret = value["images"], value["files"]
    config = str(destination)
    project = value["project"]
    release = value["release"]
    common = {
        "restart": "unless-stopped",
        "read_only": True,
        "cap_drop": ["ALL"],
        "security_opt": ["no-new-privileges:true"],
        "pids_limit": 128,
        "logging": {
            "driver": "json-file",
            "options": {"max-size": "10m", "max-file": "3"},
        },
    }
    environment = {
        "PWC_ENVIRONMENT": "staging",
        "DJANGO_ALLOWED_HOSTS": value["ngo_host"] + "," + value["ops_host"],
        "DJANGO_SECRET_KEY_FILE": "/run/secrets/django_secret",
        "PWC_AUTH_ABUSE_KEY_FILE": "/run/secrets/abuse_key",
        "DB_NAME": "pwc_staging",
        "DB_USER": "pwc_app",
        "DB_PASSWORD_FILE": "/run/secrets/db_app_password",
        "DB_HOST": "db.pwc.internal",
        "DB_PORT": "5432",
        "DB_SSLMODE": "verify-full",
        "DB_SSLROOTCERT": "/run/secrets/db_ca",
        "PWC_HEALTH_HOST": value["ngo_host"],
        "PWC_AUTH_PORTALS": json.dumps(
            {
                "https://" + value["ngo_host"]: "ngo_web",
                "https://" + value["ops_host"]: "pwc_ops",
            }
        ),
    }
    # Explicitly pinned off; caller configuration cannot supply service flags.
    sys.path.insert(0, str(ROOT / "apps/backend"))
    from config.environment import FLAGS

    environment.update({key: "0" for key in FLAGS})
    app_build = {
        "context": str(ROOT),
        "dockerfile": "infra/staging/app.Dockerfile",
        "args": {"PYTHON_IMAGE": image["python"]},
    }
    app_secrets = [
        "django_secret",
        "abuse_key",
        "db_app_password",
        "db_ca",
        "app_cert",
        "app_key",
        "app_ca",
        "client_ca",
        "health_cert",
        "health_key",
    ]
    services = {
        "db": {
            **common,
            "image": image["postgres"],
            "entrypoint": ["/bin/sh", "/etc/pwc/postgres-entrypoint.sh"],
            "environment": {
                "POSTGRES_DB": "pwc_staging",
                "POSTGRES_USER": "pwc_owner",
                "POSTGRES_INITDB_ARGS": "--auth-host=scram-sha-256",
            },
            "cap_add": ["CHOWN", "DAC_OVERRIDE", "FOWNER", "SETUID", "SETGID"],
            "networks": {"database": {"aliases": ["db.pwc.internal"]}},
            "volumes": [
                "pgdata:/var/lib/postgresql/data",
                f"{HERE}/postgres-entrypoint.sh:/etc/pwc/postgres-entrypoint.sh:ro",
                f"{HERE}/init-role.sh:/docker-entrypoint-initdb.d/10-role.sh:ro",
                f"{HERE}/pg_hba.conf:/etc/pwc/pg_hba.conf:ro",
            ],
            "tmpfs": ["/tmp", "/var/run/postgresql", "/run/postgres-tls"],
            "secrets": ["db_cert", "db_key", "db_owner_password", "db_app_password"],
            "healthcheck": {
                "test": [
                    "CMD",
                    "pg_isready",
                    "-h",
                    "127.0.0.1",
                    "-U",
                    "pwc_owner",
                    "-d",
                    "pwc_staging",
                ],
                "interval": "5s",
                "timeout": "3s",
                "retries": 20,
            },
            "mem_limit": "768m",
        },
        "app": {
            **common,
            "image": f"{project}-app:{release}",
            "build": app_build,
            "environment": environment,
            "networks": {
                "application": {"aliases": ["app.pwc.internal"]},
                "database": {},
            },
            "secrets": app_secrets,
            "depends_on": {"db": {"condition": "service_healthy"}},
            "tmpfs": ["/tmp"],
            "healthcheck": {
                "test": ["CMD", "python", "/app/infra/staging/runtime.py", "health"],
                "interval": "10s",
                "timeout": "8s",
                "retries": 12,
                "start_period": "20s",
            },
            "mem_limit": "768m",
        },
        "migrate": {
            **common,
            "image": f"{project}-app:{release}",
            "build": app_build,
            "restart": "no",
            "command": ["migrate"],
            "profiles": ["maintenance"],
            "environment": {
                **environment,
                "DB_USER": "pwc_owner",
                "DB_PASSWORD_FILE": "/run/secrets/db_owner_password",
            },
            "networks": ["database"],
            "secrets": ["django_secret", "abuse_key", "db_owner_password", "db_ca"],
            "tmpfs": ["/tmp"],
        },
        "dbtool": {
            **common,
            "image": image["postgres"],
            "restart": "no",
            "profiles": ["maintenance"],
            "user": "10001:10001",
            "entrypoint": ["/bin/sh", "/etc/pwc/dbtool.sh"],
            "networks": ["database"],
            "volumes": [f"{HERE}/dbtool.sh:/etc/pwc/dbtool.sh:ro"],
            "secrets": ["db_owner_password", "db_ca"],
            "tmpfs": ["/tmp"],
        },
        "gateway": {
            **common,
            "image": image["haproxy"],
            "user": "10001:10001",
            "command": ["haproxy", "-W", "-db", "-f", "/etc/pwc/haproxy.cfg"],
            "ports": ["443:8443"],
            "networks": ["public", "routing"],
            "volumes": [f"{config}/haproxy.cfg:/etc/pwc/haproxy.cfg:ro"],
            "tmpfs": ["/tmp"],
            "depends_on": {
                name: {"condition": "service_healthy"} for name in ("ngo", "ops")
            },
            "healthcheck": {
                "test": ["CMD", "haproxy", "-c", "-f", "/etc/pwc/haproxy.cfg"],
                "interval": "10s",
                "timeout": "5s",
                "retries": 3,
            },
            "mem_limit": "128m",
        },
    }
    for name, portal_name in (("ngo", "ngo-web"), ("ops", "pwc-ops")):
        services[name] = {
            **common,
            "image": f"{project}-{name}:{release}",
            "build": {
                "context": str(ROOT),
                "dockerfile": "infra/staging/portal.Dockerfile",
                "args": {
                    "NODE_IMAGE": image["node"],
                    "NGINX_IMAGE": image["nginx"],
                    "PORTAL": portal_name,
                },
            },
            "user": "10001:10001",
            "networks": ["routing", "application"],
            "volumes": [f"{config}/{name}.conf:/etc/pwc/nginx.conf:ro"],
            "secrets": [
                {"source": name + "_cert", "target": "portal_cert"},
                {"source": name + "_key", "target": "portal_key"},
                {"source": name + "_client_cert", "target": "client_cert"},
                {"source": name + "_client_key", "target": "client_key"},
                "app_ca",
            ],
            "tmpfs": ["/tmp"],
            "depends_on": {"app": {"condition": "service_healthy"}},
            "healthcheck": {
                "test": [
                    "CMD-SHELL",
                    "kill -0 $(cat /tmp/nginx.pid) && nginx -t -q -c /etc/pwc/nginx.conf",
                ],
                "interval": "10s",
                "timeout": "5s",
                "retries": 6,
            },
            "mem_limit": "128m",
        }
    return {
        "name": project,
        "services": services,
        "volumes": {"pgdata": {}},
        "networks": {
            "public": {},
            **{
                name: {"internal": True}
                for name in ("routing", "application", "database")
            },
        },
        "secrets": {name: {"file": path} for name, path in secret.items()},
    }


def render(config, output, synthetic=False):
    value = metadata(
        json.loads(Path(config).read_text(), object_pairs_hook=unique), synthetic
    )
    if (
        value["release"]
        != checked(["git", "-C", str(ROOT), "rev-parse", "HEAD"]).decode().strip()
    ):
        fail()
    files(value)
    output = Path(output).resolve()
    if any(c in str(output) for c in ("$", "\n", "\r", ":")):
        fail()
    if output.is_relative_to(ROOT):
        fail()
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    output.chmod(0o700)
    for name in ("ngo", "ops"):
        (output / (name + ".conf")).write_text(portal(value[name + "_host"]))
        (output / (name + ".conf")).chmod(0o644)
    gateway = f"""global
  maxconn 512
defaults
  mode tcp
  timeout connect 5s
  timeout client 40s
  timeout server 40s
frontend tls
  bind :8443
  tcp-request inspect-delay 5s
  tcp-request content accept if {{ req.ssl_hello_type 1 }}
  use_backend ngo if {{ req.ssl_sni -i {value["ngo_host"]} }}
  use_backend ops if {{ req.ssl_sni -i {value["ops_host"]} }}
  default_backend denied
backend ngo
  server ngo ngo:8443 check
backend ops
  server ops ops:8443 check
backend denied
  tcp-request content reject
"""
    (output / "haproxy.cfg").write_text(gateway)
    (output / "haproxy.cfg").chmod(0o644)
    document = compose(value, output)
    path = output / "compose.json"
    path.write_text(json.dumps(document, indent=2) + "\n")
    path.chmod(0o600)
    (output / "evidence.json").write_text(
        json.dumps(
            {
                "release": value["release"],
                "images": value["images"],
                "configuration_sha256": hashlib.sha256(
                    Path(config).read_bytes()
                ).hexdigest(),
                "synthetic": synthetic,
                "acceptance": "A_PENDING_STACK_TEST_B_C_D_NOT_ACCEPTED",
            },
            indent=2,
        )
    )
    print("Staging configuration rendered; no deployment or acceptance performed")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--synthetic",
        action="store_true",
        help="Reserved .test fixtures only; never host acceptance",
    )
    args = parser.parse_args()
    try:
        render(args.config, args.output, args.synthetic)
    except (ValueError, TypeError, KeyError, OSError, subprocess.CalledProcessError):
        print("Staging validation failed (values redacted)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
