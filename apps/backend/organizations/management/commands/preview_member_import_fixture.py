"""Run only built-in fictional CSV scenarios; no file/network/intake option."""

import json
from django.core.management.base import BaseCommand, CommandError
from organizations.member_import_fixtures import (
    SCENARIOS,
    UnknownFixtureScenario,
    preview_fixture,
)


class Command(BaseCommand):
    help = "Exercise nonwriting member CSV preview with synthetic fixtures only"

    def add_arguments(self, parser):
        parser.add_argument("--scenario", choices=SCENARIOS, default="valid")

    def handle(self, *args, **options):
        try:
            report = preview_fixture(options["scenario"])
        except UnknownFixtureScenario:
            raise CommandError("Unknown synthetic preview scenario") from None
        # Reuse the single redacted projection. No raw values, names or contacts.
        self.stdout.write(
            json.dumps(dict(report.to_summary(), synthetic_only=True), sort_keys=True)
        )
        if any(row.errors for row in report.rows):
            raise CommandError("Synthetic preview contains invalid rows")
