#!/bin/sh
set -eu
# Only initial database setup runs as root, then official entrypoint drops UID.
mkdir -p /run/postgres-tls
for name in db_cert db_key db_owner_password db_app_password; do
    cp "/run/secrets/$name" "/run/postgres-tls/$name"
    chown postgres:postgres "/run/postgres-tls/$name"
    chmod 600 "/run/postgres-tls/$name"
done
export POSTGRES_PASSWORD_FILE=/run/postgres-tls/db_owner_password
exec /usr/local/bin/docker-entrypoint.sh postgres \
    -c ssl=on -c ssl_cert_file=/run/postgres-tls/db_cert -c ssl_key_file=/run/postgres-tls/db_key \
    -c hba_file=/etc/pwc/pg_hba.conf -c password_encryption=scram-sha-256 \
    -c log_statement=none -c log_min_messages=panic -c log_min_error_statement=panic \
    -c log_error_verbosity=terse -c log_connections=off -c log_disconnections=off
