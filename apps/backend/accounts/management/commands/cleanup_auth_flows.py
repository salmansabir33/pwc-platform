from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from accounts.flow_cleanup import cleanup_flows


class Command(BaseCommand):
    help = "Prune expired synthetic registration/reset flows and abuse windows."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args, **options):
        if settings.PWC_AUTH_DELIVERY_MODE != "synthetic":
            raise CommandError("Live retention/disposal requires operational approval.")
        if not 1 <= options["limit"] <= 1000:
            raise CommandError("limit must be between 1 and 1000")
        # Deliberately works with endpoints disabled and/or encryption keys lost.
        result = cleanup_flows(options["limit"])
        self.stdout.write(
            "Disposed synthetic expired state: "
            + ", ".join(f"{key}={value}" for key, value in result.items())
        )
