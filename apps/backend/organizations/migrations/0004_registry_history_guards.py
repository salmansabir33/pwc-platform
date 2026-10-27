"""Backfill public-only lookup keys; guard immutable lifecycle history in PostgreSQL."""

import unicodedata
from django.db import migrations
from django.db.migrations.exceptions import IrreversibleError


def backfill(apps, schema_editor):
    Organization = apps.get_model("organizations", "Organization")
    for org in Organization.objects.iterator(chunk_size=500):

        def key(value):
            return " ".join(unicodedata.normalize("NFKC", value).split()).casefold()

        Organization.objects.filter(pk=org.pk).update(
            lookup_name=key(org.name), lookup_city=key(org.city)
        )


def reverse_unused(apps, schema_editor):
    for name in (
        "OrganizationDraft",
        "OrganizationClaim",
        "RegistryEvent",
        "RegistryReceipt",
    ):
        if apps.get_model("organizations", name).objects.exists():
            raise IrreversibleError(
                "Used registry records require a forward migration; history cannot be dropped."
            )


SQL = """
CREATE FUNCTION pwc_registry_history_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'registry history is immutable' USING ERRCODE = '23514';
END;
$$;
CREATE TRIGGER registry_history_immutable BEFORE UPDATE OR DELETE ON organizations_registryevent
FOR EACH ROW EXECUTE FUNCTION pwc_registry_history_immutable();
CREATE TRIGGER registry_receipt_immutable BEFORE UPDATE OR DELETE ON organizations_registryreceipt
FOR EACH ROW EXECUTE FUNCTION pwc_registry_history_immutable();
"""
REVERSE = """
DROP TRIGGER registry_receipt_immutable ON organizations_registryreceipt;
DROP TRIGGER registry_history_immutable ON organizations_registryevent;
DROP FUNCTION pwc_registry_history_immutable();
"""


class Migration(migrations.Migration):
    dependencies = [
        (
            "organizations",
            "0003_organization_lookup_city_organization_lookup_name_and_more",
        )
    ]
    operations = [
        migrations.RunPython(backfill, reverse_unused),
        migrations.RunSQL(SQL, REVERSE),
    ]
