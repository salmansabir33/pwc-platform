#!/bin/sh
# Run only on the explicitly approved staging host. Does not authorize B/C/D.
set -eu
[ "$#" -ge 2 ] || { echo 'Usage: stack.sh /absolute/rendered/compose.json build|up|status|stop|logs|backup|restore|restart' >&2; exit 2; }
manifest=$1
operation=$2
case "$manifest" in /*/compose.json) ;; *) exit 2 ;; esac
[ -f "$manifest" ] || exit 2
# Never inherit another project's Compose scope/profiles or a remote Docker target.
unset COMPOSE_PROJECT_NAME COMPOSE_PROFILES COMPOSE_FILE COMPOSE_ENV_FILES COMPOSE_PATH_SEPARATOR
compose() { docker --context default compose --env-file /dev/null -f "$manifest" "$@"; }
case "$operation" in
    build) compose config --quiet; compose build --pull app ngo ops db gateway ;;
    up)
        # An explicit migration error stops startup. Never automatically migrate on
        # an application restart; maintenance is a controlled separate operation.
        compose config --quiet
        compose up -d --wait --wait-timeout 180 db
        compose --profile maintenance run --rm --no-deps migrate
        compose up -d --wait --wait-timeout 180 app ngo ops gateway
        ;;
    status) compose ps ;;
    stop) compose stop ;;
    logs) compose logs --tail=100 ;;
    restart) compose restart app ngo ops gateway ;;
    backup) compose --profile maintenance run --rm --no-deps -T dbtool backup ;;
    restore)
        # Stop every request producer. Restore only into a freshly initialized DB.
        [ "${PWC_CONFIRM_FRESH_RESTORE:-}" = YES ] || { echo 'Fresh restore confirmation required' >&2; exit 2; }
        compose stop gateway ngo ops app
        compose --profile maintenance run --rm --no-deps -T dbtool restore
        ;;
    *) exit 2 ;;
esac
