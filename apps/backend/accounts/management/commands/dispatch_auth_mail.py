from django.core.management.base import BaseCommand, CommandError

from accounts.delivery import dispatch_one
from accounts.flow_security import FlowProblem


class Command(BaseCommand):
    help = "Dispatch a bounded batch of synthetic encrypted authentication mail."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args, **options):
        limit = options["limit"]
        if not 1 <= limit <= 1000:
            raise CommandError("limit must be between 1 and 1000")
        count = 0
        try:
            while count < limit and dispatch_one():
                count += 1
        except FlowProblem:
            raise CommandError(
                "Authentication mail configuration is unavailable."
            ) from None
        self.stdout.write(f"Processed {count} authentication delivery intents.")
