#!/bin/sh
set -eu
export PGHOST=db.pwc.internal PGDATABASE=pwc_staging PGUSER=pwc_owner PGSSLMODE=verify-full PGSSLROOTCERT=/run/secrets/db_ca
export PGPASSWORD="$(cat /run/secrets/db_owner_password)"
case "$1" in
    backup) exec pg_dump --format=custom --no-owner --no-acl 2>/dev/null ;;
    restore) exec pg_restore --exit-on-error --single-transaction --no-owner --no-acl --dbname=pwc_staging 2>/dev/null ;;
    *) exit 2 ;;
esac
