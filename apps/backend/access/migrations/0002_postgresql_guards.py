"""PostgreSQL-only immutable history. Provision roles separately; never grant PUBLIC."""
from django.db import migrations

SQL = r"""
REVOKE ALL ON access_ngogrant, access_ngokernelstate, access_syntheticprincipal,
    access_authorizationevent FROM PUBLIC;

-- SELECT FOR UPDATE normally needs UPDATE privilege. Runtime gets only this
-- fixed, read/lock-only function, never table UPDATE on the authority root.
CREATE FUNCTION pwc_kernel_lock(tenant uuid) RETURNS SETOF access_ngokernelstate
LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog AS $$
    SELECT * FROM public.access_ngokernelstate WHERE organization_id = tenant FOR UPDATE;
$$;
REVOKE ALL ON FUNCTION pwc_kernel_lock(uuid) FROM PUBLIC;

CREATE FUNCTION pwc_kernel_guard() RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public, pg_temp AS $$
DECLARE tenant_batch uuid; principal_batch uuid; parent_org uuid; parent_actor uuid; parent_version integer;
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'kernel history cannot be deleted' USING ERRCODE = '23514';
    END IF;
    IF TG_TABLE_NAME = 'access_syntheticprincipal' THEN
        IF TG_OP = 'UPDATE' THEN
            RAISE EXCEPTION 'synthetic attestation immutable' USING ERRCODE = '23514';
        END IF;
    ELSIF TG_TABLE_NAME = 'access_ngokernelstate' AND TG_OP = 'UPDATE' THEN
        IF (to_jsonb(NEW) - ARRAY['revision','mode']) IS DISTINCT FROM
           (to_jsonb(OLD) - ARRAY['revision','mode']) OR
           NEW.revision <> OLD.revision + 1 OR
           (NEW.mode <> OLD.mode AND NOT (OLD.mode = 'synthetic' AND NEW.mode = 'disabled')) THEN
            RAISE EXCEPTION 'invalid kernel state transition' USING ERRCODE = '23514';
        END IF;
    ELSIF TG_TABLE_NAME = 'access_ngogrant' THEN
        IF TG_OP = 'UPDATE' THEN
            IF OLD.revoked_at IS NOT NULL OR NEW.revoked_at IS NULL OR
               NEW.revision <> OLD.revision + 1 OR
               (to_jsonb(NEW) - ARRAY['revision','revoked_at','revoked_by_id','revoked_by_process','revocation_reason']) IS DISTINCT FROM
               (to_jsonb(OLD) - ARRAY['revision','revoked_at','revoked_by_id','revoked_by_process','revocation_reason']) THEN
                RAISE EXCEPTION 'grant immutable except terminal revocation' USING ERRCODE = '23514';
            END IF;
        END IF;
        SELECT fixture_batch INTO tenant_batch FROM access_ngokernelstate
            WHERE organization_id = NEW.organization_id AND mode = 'synthetic';
        SELECT fixture_batch INTO principal_batch FROM access_syntheticprincipal WHERE user_id = NEW.subject_id;
        IF tenant_batch IS NULL OR principal_batch IS NULL OR
           tenant_batch <> NEW.fixture_batch OR principal_batch <> NEW.fixture_batch THEN
            RAISE EXCEPTION 'grant synthetic ownership mismatch' USING ERRCODE = '23514';
        END IF;
        IF TG_OP = 'INSERT' AND (NEW.revision <> 1 OR NEW.revoked_at IS NOT NULL) THEN
            RAISE EXCEPTION 'new grant must start unrevoked at revision 1' USING ERRCODE = '23514';
        END IF;
        IF NEW.issuing_actor_id IS NOT NULL AND NOT EXISTS (
            SELECT 1 FROM access_syntheticprincipal WHERE user_id = NEW.issuing_actor_id AND fixture_batch = NEW.fixture_batch
        ) THEN
            RAISE EXCEPTION 'issuer outside fixture' USING ERRCODE = '23514';
        END IF;
        IF NEW.revoked_by_id IS NOT NULL AND NOT EXISTS (
            SELECT 1 FROM access_syntheticprincipal WHERE user_id = NEW.revoked_by_id AND fixture_batch = NEW.fixture_batch
        ) THEN
            RAISE EXCEPTION 'revoker outside fixture' USING ERRCODE = '23514';
        END IF;
    ELSIF TG_TABLE_NAME = 'access_authorizationevent' THEN
        IF TG_OP = 'UPDATE' THEN
            RAISE EXCEPTION 'audit append only' USING ERRCODE = '23514';
        END IF;
        -- Audit cannot attach another tenant's grant or another human's session.
        IF NEW.grant_id IS NOT NULL THEN
            SELECT organization_id, fixture_batch, role_version INTO parent_org, tenant_batch, parent_version FROM access_ngogrant WHERE id = NEW.grant_id;
            IF parent_org IS DISTINCT FROM NEW.organization_id OR tenant_batch IS DISTINCT FROM NEW.fixture_batch OR parent_version IS DISTINCT FROM NEW.role_version THEN
                RAISE EXCEPTION 'audit grant ownership mismatch' USING ERRCODE = '23514';
            END IF;
        END IF;
        IF NEW.session_id IS NOT NULL THEN
            SELECT user_id INTO parent_actor FROM accounts_authsession WHERE id = NEW.session_id;
            IF parent_actor IS DISTINCT FROM NEW.actor_id THEN
                RAISE EXCEPTION 'audit session ownership mismatch' USING ERRCODE = '23514';
            END IF;
        END IF;
        IF NEW.result = 'allow' AND (NEW.actor_id IS NULL OR NEW.session_id IS NULL OR NOT EXISTS (
            SELECT 1 FROM access_ngokernelstate s WHERE s.organization_id = NEW.organization_id
                AND s.fixture_batch = NEW.fixture_batch AND s.revision = NEW.new_context_revision
        )) THEN
            RAISE EXCEPTION 'allow audit must identify live context and principal' USING ERRCODE = '23514';
        END IF;
        NEW.created_at := clock_timestamp();
    END IF;
    RETURN NEW;
END $$;

CREATE TRIGGER pwc_principal_guard BEFORE INSERT OR UPDATE OR DELETE ON access_syntheticprincipal
    FOR EACH ROW EXECUTE FUNCTION pwc_kernel_guard();
CREATE TRIGGER pwc_state_guard BEFORE UPDATE OR DELETE ON access_ngokernelstate
    FOR EACH ROW EXECUTE FUNCTION pwc_kernel_guard();
CREATE TRIGGER pwc_grant_guard BEFORE INSERT OR UPDATE OR DELETE ON access_ngogrant
    FOR EACH ROW EXECUTE FUNCTION pwc_kernel_guard();
CREATE TRIGGER pwc_event_guard BEFORE INSERT OR UPDATE OR DELETE ON access_authorizationevent
    FOR EACH ROW EXECUTE FUNCTION pwc_kernel_guard();

-- No untracked legacy workspace lifecycle writer on a kernel tenant. Future
-- lifecycle commands need a separately reviewed atomic revision/audit contract.
CREATE FUNCTION pwc_kernel_workspace_guard() RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public, pg_temp AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM access_ngokernelstate WHERE organization_id = OLD.organization_id) THEN
        RAISE EXCEPTION 'kernel workspace lifecycle is frozen; disable kernel state instead' USING ERRCODE = '23514';
    END IF;
    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END $$;
CREATE TRIGGER pwc_kernel_workspace_guard BEFORE UPDATE OR DELETE ON organizations_organizationworkspace
    FOR EACH ROW EXECUTE FUNCTION pwc_kernel_workspace_guard();
"""
REVERSE = """
DROP TRIGGER pwc_kernel_workspace_guard ON organizations_organizationworkspace;
DROP FUNCTION pwc_kernel_workspace_guard();
DROP TRIGGER pwc_principal_guard ON access_syntheticprincipal;
DROP TRIGGER pwc_state_guard ON access_ngokernelstate;
DROP TRIGGER pwc_grant_guard ON access_ngogrant;
DROP TRIGGER pwc_event_guard ON access_authorizationevent;
DROP FUNCTION pwc_kernel_guard();
DROP FUNCTION IF EXISTS pwc_kernel_lock(uuid);
"""


def protect_used_history(apps, schema_editor):
    for model in ("NGOGrant", "AuthorizationEvent", "NGOKernelState", "SyntheticPrincipal"):
        if apps.get_model("access", model).objects.using(schema_editor.connection.alias).exists():
            raise RuntimeError("Used kernel history cannot be reversed; disable and forward-fix")


class Migration(migrations.Migration):
    dependencies = [("access", "0001_initial")]
    operations = [migrations.RunSQL(SQL, REVERSE), migrations.RunPython(migrations.RunPython.noop, protect_used_history)]
