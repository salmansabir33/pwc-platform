from django.db import migrations
from django.db.migrations.exceptions import IrreversibleError


def reverse_unused(apps, schema_editor):
    for name in (
        "ControlledOnboardingRecord",
        "ControlledOnboardingRevision",
        "OfflineVerificationAttestation",
        "ControlledOnboardingEvent",
    ):
        if apps.get_model("organizations", name).objects.exists():
            raise IrreversibleError(
                "Used controlled onboarding requires a reviewed forward correction."
            )


class Migration(migrations.Migration):
    dependencies = [("organizations", "0007_controlledonboardingrecord_and_more")]
    operations = [
        migrations.RunPython(migrations.RunPython.noop, reverse_unused),
        migrations.RunSQL(
            """
CREATE TRIGGER controlled_snapshot_immutable BEFORE UPDATE OR DELETE ON organizations_controlledonboardingrevision FOR EACH ROW EXECUTE FUNCTION pwc_registry_history_immutable();
CREATE TRIGGER offline_attestation_immutable BEFORE UPDATE OR DELETE ON organizations_offlineverificationattestation FOR EACH ROW EXECUTE FUNCTION pwc_registry_history_immutable();
CREATE TRIGGER controlled_event_immutable BEFORE UPDATE OR DELETE ON organizations_controlledonboardingevent FOR EACH ROW EXECUTE FUNCTION pwc_registry_history_immutable();
CREATE FUNCTION pwc_controlled_initiator_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW.initiator_id IS DISTINCT FROM OLD.initiator_id THEN
  RAISE EXCEPTION 'Controlled initiator is immutable';
 END IF;
 RETURN NEW;
END;
$$;
CREATE TRIGGER controlled_initiator_immutable BEFORE UPDATE ON organizations_controlledonboardingrecord FOR EACH ROW EXECUTE FUNCTION pwc_controlled_initiator_immutable();
""",
            """
DROP TRIGGER controlled_initiator_immutable ON organizations_controlledonboardingrecord;
DROP FUNCTION pwc_controlled_initiator_immutable();
DROP TRIGGER controlled_event_immutable ON organizations_controlledonboardingevent;
DROP TRIGGER offline_attestation_immutable ON organizations_offlineverificationattestation;
DROP TRIGGER controlled_snapshot_immutable ON organizations_controlledonboardingrevision;
""",
        ),
    ]
