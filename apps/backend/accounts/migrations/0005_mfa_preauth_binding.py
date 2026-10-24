from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):
    dependencies = [("accounts", "0004_flow_cooldown_and_transition_evidence")]
    operations = [
        migrations.AddField(
            model_name="authchallenge",
            name="client_digest",
            field=models.CharField(
                max_length=64,
                null=True,
                blank=True,
                validators=[
                    django.core.validators.RegexValidator(
                        r"\A[0-9a-f]{64}\Z", "Supply a digest, never a raw secret."
                    )
                ],
            ),
        ),
        migrations.AddField(
            model_name="authchallenge",
            name="factor_revision",
            field=models.PositiveBigIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name="authchallenge",
            name="device_label",
            field=models.CharField(max_length=100, blank=True),
        ),
    ]
