"""Value-free, read-only preflight; cannot activate or issue an invitation."""

import json
from django.core.management.base import BaseCommand, CommandError
from accounts.enrollment_readiness import readiness


class Command(BaseCommand):
    help = (
        "Report exact personal-enrollment blockers; no credentials or issuer bootstrap."
    )

    def handle(self, *args, **options):
        self.stdout.write(json.dumps(readiness(), indent=2))
        raise CommandError("Real personal enrollment is not accepted or enabled.")
