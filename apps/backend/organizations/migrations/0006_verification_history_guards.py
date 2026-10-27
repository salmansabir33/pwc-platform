from django.db import migrations
from django.db.migrations.exceptions import IrreversibleError


def reverse_unused(apps, schema_editor):
    for name in (
        "VerificationCase",
        "EvidencePreparation",
        "VerificationEvent",
        "VerificationReceipt",
    ):
        if apps.get_model("organizations", name).objects.exists():
            raise IrreversibleError(
                "Used verification preparation requires a forward fix; history cannot be dropped."
            )


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0005_verificationcase_evidencepreparation_and_more")
    ]
    operations = [
        migrations.RunPython(migrations.RunPython.noop, reverse_unused),
        migrations.RunSQL(
            """
CREATE TRIGGER verification_history_immutable BEFORE UPDATE OR DELETE ON organizations_verificationevent
FOR EACH ROW EXECUTE FUNCTION pwc_registry_history_immutable();
CREATE TRIGGER verification_receipt_immutable BEFORE UPDATE OR DELETE ON organizations_verificationreceipt
FOR EACH ROW EXECUTE FUNCTION pwc_registry_history_immutable();
""",
            """
DROP TRIGGER verification_receipt_immutable ON organizations_verificationreceipt;
DROP TRIGGER verification_history_immutable ON organizations_verificationevent;
""",
        ),
    ]
