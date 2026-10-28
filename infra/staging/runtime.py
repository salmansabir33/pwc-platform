"""Container entry/health commands. Errors are deliberately value-free."""

import http.client
import json
import os
from pathlib import Path
import ssl
import sys


def environment():
    for key in ("DJANGO_SECRET_KEY", "DB_PASSWORD", "PWC_AUTH_ABUSE_KEY"):
        value = Path(os.environ[key + "_FILE"]).read_text().strip()
        if not value or "\n" in value or "\x00" in value:
            raise ValueError("Invalid mounted secret")
        os.environ[key] = value


def health():
    import psycopg

    environment()
    with psycopg.connect(
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        sslmode="verify-full",
        sslrootcert=os.environ["DB_SSLROOTCERT"],
        connect_timeout=3,
    ) as connection:
        connection.execute("SELECT 1")
    context = ssl.create_default_context(cafile="/run/secrets/app_ca")
    context.load_cert_chain("/run/secrets/health_cert", "/run/secrets/health_key")
    client = http.client.HTTPSConnection(
        "app.pwc.internal", 8443, context=context, timeout=3
    )
    try:
        client.request(
            "GET", "/api/v1/health/", headers={"Host": os.environ["PWC_HEALTH_HOST"]}
        )
        response = client.getresponse()
        if (
            response.status != 200
            or json.loads(response.read(4096)).get("service") != "pwc-api"
        ):
            raise ValueError("Unhealthy")
    finally:
        client.close()


def main():
    operation = sys.argv[1]
    if operation == "health":
        health()
        return
    environment()
    import django

    django.setup()
    from django.core.management import call_command

    if operation == "migrate":
        call_command("migrate", interactive=False, verbosity=0)
        from django.db import connection

        # Disabled services need no domain writer. No blanket future-table DML
        # grant: current public readers + shared abuse budget only.
        with connection.cursor() as cursor:
            cursor.execute("GRANT CONNECT ON DATABASE pwc_staging TO pwc_app")
            cursor.execute("GRANT USAGE ON SCHEMA public TO pwc_app")
            cursor.execute(
                "GRANT SELECT ON organizations_organization, organizations_organizationworkspace, django_migrations TO pwc_app"
            )
            cursor.execute(
                "GRANT SELECT, INSERT, UPDATE ON accounts_authabusebucket TO pwc_app"
            )
            cursor.execute("GRANT INSERT ON accounts_securityevent TO pwc_app")
            cursor.execute("GRANT SELECT (id) ON accounts_securityevent TO pwc_app")
        print("Staging migrations and bounded public-reader privileges complete")
    elif operation == "serve":
        call_command("migrate", check=True, verbosity=0)
        print(
            "Staging TLS application starting; gated services remain disabled",
            flush=True,
        )
        os.execvp(
            "gunicorn",
            [
                "gunicorn",
                "--config",
                "/app/infra/staging/gunicorn.conf.py",
                "config.wsgi:application",
            ],
        )
    else:
        raise ValueError("Unknown operation")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print(
            "Staging command failed; inspect readiness/configuration (details redacted)",
            file=sys.stderr,
        )
        raise SystemExit(1) from None
