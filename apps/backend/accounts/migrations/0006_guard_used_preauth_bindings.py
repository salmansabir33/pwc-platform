"""Preserve used 0005 bindings before any backward column removal."""

from django.db import migrations
from django.db.models import Q
from django.db.migrations.exceptions import IrreversibleError


def require_unused_preauth_bindings(apps, schema_editor):
    Challenge = apps.get_model("accounts", "AuthChallenge")
    if (
        Challenge.objects.using(schema_editor.connection.alias)
        .filter(
            Q(purpose="preauth_mfa")
            | Q(client_digest__isnull=False)
            | Q(factor_revision__isnull=False)
            | ~Q(device_label="")
        )
        .exists()
    ):
        raise IrreversibleError(
            "MFA preauthentication bindings have been used; preserve evidence "
            "and use a reviewed forward fix or backup/restore, not column removal."
        )


class Migration(migrations.Migration):
    dependencies = [("accounts", "0005_mfa_preauth_binding")]
    operations = [
        migrations.RunPython(
            migrations.RunPython.noop, require_unused_preauth_bindings
        ),
    ]
