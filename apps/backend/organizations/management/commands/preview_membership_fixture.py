"""Nonwriting 05A demonstration; accepts fixed fictional scenarios only."""

import json
from django.core.management.base import BaseCommand, CommandError
from organizations.membership_fixtures import (
    SCENARIOS,
    UnknownMembershipScenario,
    preview_membership_fixture,
)


class Command(BaseCommand):
    help = "Evaluate synthetic membership admission without writes or authority"

    def add_arguments(self, parser):
        parser.add_argument("--scenario", choices=SCENARIOS, default="open")

    def handle(self, *args, **options):
        try:
            previews = preview_membership_fixture(options["scenario"])
        except UnknownMembershipScenario:
            raise CommandError("Unknown synthetic membership scenario") from None
        self.stdout.write(
            json.dumps(
                {
                    "synthetic_only": True,
                    "commit_available": False,
                    "steps": [p.to_summary() for p in previews],
                },
                sort_keys=True,
            )
        )
        if any(not p.transition_valid for p in previews):
            raise CommandError("Synthetic membership preview contains conflicts")
