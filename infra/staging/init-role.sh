#!/bin/sh
set -eu
export PWC_APP_PASSWORD="$(cat /run/postgres-tls/db_app_password)"
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --no-psqlrc --set ON_ERROR_STOP=1 2>/dev/null <<'SQL'
\getenv app_password PWC_APP_PASSWORD
CREATE ROLE pwc_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD :'app_password';
REVOKE ALL ON DATABASE pwc_staging FROM PUBLIC;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
SQL
unset PWC_APP_PASSWORD
