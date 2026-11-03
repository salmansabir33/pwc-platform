"""Run only built-in fictional CSV scenarios; no file/network/intake option."""

import json
from uuid import UUID
from django.core.management.base import BaseCommand, CommandError
from organizations.member_import_preview import PreviewCatalog, preview_csv


class Command(BaseCommand):
    help = "Exercise nonwriting member CSV preview with synthetic fixtures only"

    def add_arguments(self, parser):
        parser.add_argument(
            "--scenario", choices=("valid", "duplicate", "invalid"), default="valid"
        )

    def handle(self, *args, **options):
        organization = UUID("00000000-0000-4000-8000-000000000001")
        header = "record_reference,display_name,category_reference\n"
        cases = {
            "valid": "MEMBER_A,Synthetic Person A,ORDINARY\nMEMBER_B,Synthetic Person B,ORDINARY\n",
            "duplicate": "MEMBER_A,Synthetic Person A,ORDINARY\nMEMBER_A,Synthetic Person B,ORDINARY\n",
            "invalid": "MEMBER_A,=FORMULA,UNKNOWN\n",
        }
        report = preview_csv(
            (header + cases[options["scenario"]]).encode(),
            organization_id=organization,
            catalog=PreviewCatalog(organization, frozenset({"ORDINARY"})),
        )
        # Counts/codes only, never names/raw cells, source authority or a receipt.
        self.stdout.write(
            json.dumps(
                {
                    "synthetic_only": True,
                    "commit_available": report.commit_available,
                    "rows": [
                        {
                            "record": row.number,
                            "errors": row.errors,
                            "warnings": row.warnings,
                        }
                        for row in report.rows
                    ],
                }
            )
        )
        if any(row.errors for row in report.rows):
            raise CommandError("Synthetic preview contains invalid rows")
