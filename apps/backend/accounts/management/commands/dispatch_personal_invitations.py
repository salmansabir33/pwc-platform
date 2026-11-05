"""Bounded test-profile outbox/expiry worker. Never selects SMTP from settings."""

from django.core.management.base import BaseCommand, CommandError
from accounts.flow_security import FlowProblem
from accounts.personal_invitations import gate, expire_one
from accounts.invitation_delivery import dispatch_one


class Command(BaseCommand):
    help = "Process bounded synthetic personal invitation delivery and expiry."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=20)

    def handle(self, *args, **options):
        try:
            gate()
            limit = options["limit"]
            if not 1 <= limit <= 100:
                raise CommandError("Limit must be between 1 and 100.")
            for _ in range(limit):
                if not expire_one():
                    break
            for _ in range(limit):
                if not dispatch_one():
                    break
            self.stdout.write(
                "Bounded synthetic worker finished; not delivery approval."
            )
        except FlowProblem:
            raise CommandError("Personal invitation worker unavailable.") from None
