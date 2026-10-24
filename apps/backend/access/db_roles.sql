-- psql -v runtime_role=... -v fixture_role=... -f access/db_roles.sql
-- Run as migration owner in a disposable synthetic DB AFTER migrations.
-- Roles must already exist, be non-owner/non-superuser, with no inherited owner,
-- fixture, CREATEROLE, TRUNCATE, BYPASSRLS or schema CREATE powers. No passwords here.
-- Existing accounts/organizations auth privileges are provisioned separately.
REVOKE ALL ON access_ngogrant, access_ngokernelstate, access_syntheticprincipal,
    access_authorizationevent FROM :"runtime_role";
GRANT SELECT ON access_ngogrant, access_ngokernelstate, access_syntheticprincipal,
    access_authorizationevent TO :"runtime_role";
GRANT INSERT ON access_authorizationevent TO :"runtime_role";
GRANT EXECUTE ON FUNCTION pwc_kernel_lock(uuid) TO :"runtime_role";
GRANT SELECT, INSERT, UPDATE ON access_ngogrant, access_ngokernelstate TO :"fixture_role";
GRANT SELECT, INSERT ON access_syntheticprincipal, access_authorizationevent TO :"fixture_role";
-- Never deploy fixture credentials/membership to an ordinary application process.
-- NO ALTER DEFAULT PRIVILEGES granting broad rights on future access tables.
