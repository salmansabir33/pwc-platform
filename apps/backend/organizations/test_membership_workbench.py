"""P4 projections are fictional; revision checks never substitute for DB locks."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError, replace
import json
from pathlib import Path
import subprocess
import sys
from uuid import uuid4
from django.contrib.auth import get_user_model
from django.db import close_old_connections, transaction
from django.test import SimpleTestCase, TransactionTestCase
from .member_import_preview import TEMPLATE, ImportPreviewError
from .membership_fixtures import APPLICATION, CATEGORY
from .membership_preview import MembershipSnapshotFixture
from .membership_workbench import (
    MemberFixture,
    MembershipFixture,
    SourceRevision,
    HistoryFixture,
    ImportPreparation,
    MembershipWorkbenchError,
    preview_admission,
    preview_member_change,
    prepare_import,
)
from .membership_demonstrations import demonstrations
from .models import Organization, OrganizationAccess

ROOT = Path(__file__).resolve().parents[3]


def empty():
    return MembershipFixture(
        MembershipSnapshotFixture(
            CATEGORY.organization_id,
            "approval",
            (
                CATEGORY,
                replace(CATEGORY, reference="ASSOCIATE", label="Synthetic Associate"),
                replace(
                    CATEGORY,
                    reference="RETIRED",
                    label="Synthetic Retired",
                    active=False,
                ),
            ),
        )
    )


def admitted():
    initial = empty()
    pending = preview_admission(
        initial, initial.source_revision(), APPLICATION, "apply"
    ).projected
    return preview_admission(
        pending, pending.source_revision(), pending.policy.requests[0], "approve"
    ).projected


class MembershipWorkbenchTests(SimpleTestCase):
    def setUp(self):
        self.source = admitted()

    def failure(self, code, function, *args, **kwargs):
        with self.assertRaises(MembershipWorkbenchError) as error:
            function(*args, **kwargs)
        self.assertEqual(error.exception.to_diagnostic(), {"code": code})
        self.assertEqual(str(error.exception), "Invalid membership preparation")

    def test_complete_hypothetical_admission_category_status_history_journey(self):
        self.assertEqual(self.source.revision, 2)
        self.assertEqual(len(self.source.members), 1)
        assigned = preview_member_change(
            self.source, self.source.source_revision(), "MEMBER_A", category="ASSOCIATE"
        ).projected
        suspended = preview_member_change(
            assigned, assigned.source_revision(), "MEMBER_A", state="suspended"
        ).projected
        resumed = preview_member_change(
            suspended, suspended.source_revision(), "MEMBER_A", state="active"
        ).projected
        ended = preview_member_change(
            resumed, resumed.source_revision(), "MEMBER_A", state="ended"
        ).projected
        self.assertEqual(ended.revision, 6)
        self.assertEqual(ended.members[0].revision, 5)
        self.assertEqual(ended.members[0].state, "ended")
        self.assertEqual(ended.members[0].category_reference, "ASSOCIATE")
        self.assertEqual(ended.history[:2], self.source.history)
        self.assertEqual(len(ended.history_for("MEMBER_A")), 6)
        self.assertEqual(ended.history_for("UNKNOWN"), ())
        self.assertEqual(ended.policy.requests[0].category_reference, "ORDINARY")
        self.assertEqual(
            ended.to_summary()["states"], {"active": 0, "suspended": 0, "ended": 1}
        )
        self.assertEqual(self.source.members[0].state, "active")
        self.assertEqual(self.source.members[0].category_reference, "ORDINARY")

    def test_all_member_status_edges_with_category_and_end_guards(self):
        valid = {
            ("active", "suspended"),
            ("suspended", "active"),
            ("active", "ended"),
            ("suspended", "ended"),
        }
        for before in ("active", "suspended", "ended"):
            member = replace(self.source.members[0], state=before)
            source = replace(self.source, members=(member,))
            for after in ("active", "suspended", "ended", "paid", "admin", None, []):
                if (before, str(after)) in valid:
                    plan = preview_member_change(
                        source, source.source_revision(), member.reference, state=after
                    )
                    self.assertEqual(plan.projected.members[0].state, after)
                else:
                    with self.assertRaises(MembershipWorkbenchError):
                        preview_member_change(
                            source,
                            source.source_revision(),
                            member.reference,
                            state=after,
                        )
            if before == "ended":
                self.failure(
                    "INVALID_MEMBER_TRANSITION",
                    preview_member_change,
                    source,
                    source.source_revision(),
                    member.reference,
                    category="ASSOCIATE",
                )

    def test_category_conflicts_and_noop_fail_without_partial_history(self):
        for category, code in (
            ("UNKNOWN", "UNKNOWN_CATEGORY"),
            ("RETIRED", "INACTIVE_CATEGORY"),
            ("ORDINARY", "UNCHANGED_CATEGORY"),
        ):
            self.failure(
                code,
                preview_member_change,
                self.source,
                self.source.source_revision(),
                "MEMBER_A",
                category=category,
            )
        self.assertEqual(self.source.revision, 2)
        self.failure(
            "INVALID_INPUT",
            preview_member_change,
            self.source,
            self.source.source_revision(),
            "MEMBER_A",
            category="ASSOCIATE",
            state="ended",
        )
        self.failure(
            "UNKNOWN_MEMBER",
            preview_member_change,
            self.source,
            self.source.source_revision(),
            "UNKNOWN",
            state="ended",
        )

    def test_revision_binds_policy_content_tenant_members_requests_and_history(self):
        token = self.source.source_revision()
        variants = [
            replace(self.source, policy=replace(self.source.policy, mode="open")),
            replace(self.source, policy=replace(self.source.policy, active=False)),
            replace(
                self.source,
                members=(
                    replace(self.source.members[0], category_reference="ASSOCIATE"),
                ),
            ),
            replace(
                self.source,
                policy=replace(
                    self.source.policy,
                    categories=tuple(
                        replace(c, label=c.label + " changed")
                        for c in self.source.policy.categories
                    ),
                ),
            ),
        ]
        other = empty()
        other_org = uuid4()
        foreign_policy = MembershipSnapshotFixture(
            other_org,
            "approval",
            tuple(
                replace(c, organization_id=other_org) for c in other.policy.categories
            ),
        )
        variants.append(MembershipFixture(foreign_policy))
        for source in variants:
            self.failure(
                "SOURCE_REVISION_CONFLICT",
                preview_member_change,
                source,
                token,
                "MEMBER_A",
                state="ended",
            )
        newer = preview_member_change(
            self.source, token, "MEMBER_A", state="suspended"
        ).projected
        self.failure(
            "SOURCE_REVISION_CONFLICT",
            preview_member_change,
            newer,
            token,
            "MEMBER_A",
            state="ended",
        )
        self.failure(
            "SOURCE_REVISION_CONFLICT",
            prepare_import,
            newer,
            token,
            TEMPLATE.sample_csv(),
        )

    def test_parallel_proposals_do_not_claim_an_atomic_commit_winner(self):
        token = self.source.source_revision()
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(
                    preview_member_change, self.source, token, "MEMBER_A", state=state
                )
                for state in ("suspended", "ended")
            ]
            proposals = [f.result().projected for f in futures]
        self.assertEqual(
            [p.members[0].state for p in proposals], ["suspended", "ended"]
        )
        self.assertTrue(all(p.revision == 3 for p in proposals))
        self.assertEqual(self.source.revision, 2)
        # Both hypothetical branches are valid: no storage/commit adapter exists.
        self.failure(
            "SOURCE_REVISION_CONFLICT",
            preview_member_change,
            proposals[0],
            token,
            "MEMBER_A",
            state="ended",
        )

    def test_admission_duplicate_pending_and_terminal_replay_cannot_create_another_member(
        self,
    ):
        self.failure(
            "EXISTING_REFERENCE",
            preview_admission,
            self.source,
            self.source.source_revision(),
            replace(APPLICATION, request_reference="ANOTHER"),
            "apply",
        )
        self.failure(
            "INVALID_TRANSITION",
            preview_admission,
            self.source,
            self.source.source_revision(),
            self.source.policy.requests[0],
            "approve",
        )
        initial = empty()
        pending = preview_admission(
            initial, initial.source_revision(), APPLICATION, "apply"
        ).projected
        self.failure(
            "DUPLICATE_REFERENCE",
            preview_admission,
            pending,
            pending.source_revision(),
            replace(APPLICATION, request_reference="ANOTHER"),
            "apply",
        )
        declined = preview_admission(
            pending, pending.source_revision(), pending.policy.requests[0], "decline"
        ).projected
        self.assertEqual(declined.members, ())
        self.assertEqual(declined.policy.requests[0].state, "declined")

    def test_admission_mode_paths_preserve_existing_evaluator(self):
        for mode, route, event, decision in (
            ("open", "application", "apply", None),
            ("invitation", "invitation", "invite", "accept"),
        ):
            source = MembershipFixture(replace(empty().policy, mode=mode))
            request = replace(APPLICATION, route=route)
            result = preview_admission(
                source, source.source_revision(), request, event
            ).projected
            if decision:
                self.assertFalse(result.members)
                result = preview_admission(
                    result,
                    result.source_revision(),
                    result.policy.requests[0],
                    decision,
                ).projected
            self.assertEqual(len(result.members), 1)
            self.assertEqual(result.members[0].state, "active")

    def test_source_ownership_precedes_member_and_category_details(self):
        foreign = replace(self.source.members[0], organization_id=uuid4())
        self.failure("TENANT_MISMATCH", replace, self.source, members=(foreign,))
        self.failure(
            "TENANT_MISMATCH",
            preview_admission,
            empty(),
            empty().source_revision(),
            replace(APPLICATION, organization_id=uuid4()),
            "apply",
        )
        self.failure(
            "DUPLICATE_REFERENCE", replace, self.source, members=self.source.members * 2
        )
        self.failure(
            "UNKNOWN_CATEGORY",
            replace,
            self.source,
            members=(replace(self.source.members[0], category_reference="UNKNOWN"),),
        )

    def test_import_keeps_csv_diagnostics_and_separates_candidates_from_creation(self):
        raw = TEMPLATE.sample_csv()
        result = prepare_import(
            self.source, self.source.source_revision(), raw
        ).to_summary()
        self.assertEqual(result["candidate_count"], 1)
        self.assertEqual(result["rows"][0]["errors"], ["EXISTING_REFERENCE"])
        self.assertEqual(result["rows"][0]["csv_diagnostics"][0]["column"], 1)
        self.assertEqual(self.source.revision, 2)
        self.assertEqual(len(self.source.members), 1)
        initial = empty()
        pending = preview_admission(
            initial, initial.source_revision(), APPLICATION, "apply"
        ).projected
        self.assertEqual(
            prepare_import(pending, pending.source_revision(), raw).to_summary()[
                "rows"
            ][0]["errors"],
            ["DUPLICATE_REFERENCE"],
        )
        invitation = MembershipFixture(replace(initial.policy, mode="invitation"))
        self.assertEqual(
            prepare_import(invitation, invitation.source_revision(), raw).to_summary()[
                "candidate_count"
            ],
            0,
        )

    def test_import_formula_conflicts_and_fatal_errors_never_retain_cells(self):
        raw = b"record_reference,display_name,category_reference\nA,=PRIVATE_CANARY,ORDINARY\nA,PRIVATE_NAME,ORDINARY\n"
        result = prepare_import(empty(), empty().source_revision(), raw)
        self.assertEqual(result.to_summary()["candidate_count"], 0)
        self.assertEqual(result.diagnostics[1][0].related_records, (2,))
        self.assertNotIn("PRIVATE", json.dumps(result.to_summary()))
        with self.assertRaises(ImportPreviewError):
            prepare_import(empty(), empty().source_revision(), b"private,contact\n")

    def test_immutability_constructor_validation_and_defensive_projection(self):
        for obj, field, value in (
            (self.source, "members", ()),
            (self.source.members[0], "state", "ended"),
            (self.source.history[0], "revision", 9),
        ):
            with self.assertRaises(FrozenInstanceError):
                setattr(obj, field, value)
        for changes in (
            {"members": []},
            {"history": list(self.source.history)},
            {"history": self.source.history[::-1]},
        ):
            self.failure("INVALID_INPUT", replace, self.source, **changes)
        self.failure("INVALID_INPUT", SourceRevision, "private-value")
        self.failure(
            "INVALID_INPUT",
            MemberFixture,
            CATEGORY.organization_id,
            "A",
            "ORDINARY",
            revision=True,
        )
        self.failure(
            "INVALID_INPUT", HistoryFixture, 1, "category", "PRIVATE", "active", True
        )
        self.failure(
            "INVALID_INPUT", ImportPreparation, ((2, ("PRIVATE",), ()),), ((),)
        )
        report = self.source.to_summary()
        report["history"][0]["kind"] = "PRIVATE"
        self.assertNotIn("PRIVATE", json.dumps(self.source.to_summary()))
        for value in (
            "MEMBER_A",
            "ORDINARY",
            "Synthetic",
            str(CATEGORY.organization_id),
        ):
            self.assertNotIn(value, json.dumps(self.source.to_summary()))

    def test_built_in_asset_parity_and_privacy(self):
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/membership_demonstrations.py"),
                "--check",
            ],
            check=True,
            capture_output=True,
        )
        asset = json.loads(
            (
                ROOT / "packages/api-contracts/fixtures/membership-demonstrations.json"
            ).read_text()
        )
        self.assertEqual(asset, demonstrations())
        text = json.dumps(asset)
        for forbidden in (
            "MEMBER_A",
            "Synthetic Ordinary",
            "@",
            "digest",
        ):
            self.assertNotIn(forbidden, text)
        self.assertFalse(asset["commit_available"])
        self.assertEqual(
            asset["scenarios"][3]["steps"][0]["code"], "SOURCE_REVISION_CONFLICT"
        )


class MembershipWorkbenchPostgreSQLTests(TransactionTestCase):
    def test_projections_inside_real_postgresql_transactions_make_no_queries_or_writes(
        self,
    ):
        a = Organization.objects.create(name="Synthetic Workbench A")
        b = Organization.objects.create(name="Synthetic Workbench B")
        counts = (
            Organization.objects.count(),
            OrganizationAccess.objects.count(),
            get_user_model().objects.count(),
        )

        def worker(org):
            close_old_connections()
            try:
                with transaction.atomic():
                    policy = MembershipSnapshotFixture(
                        org, "open", (replace(CATEGORY, organization_id=org),)
                    )
                    source = MembershipFixture(policy)
                    request = replace(APPLICATION, organization_id=org)
                    with self.assertNumQueries(0):
                        proposed = preview_admission(
                            source, source.source_revision(), request, "apply"
                        ).projected
                        summary = proposed.to_summary()
                    return summary, proposed.members[0].organization_id
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            outputs = list(pool.map(worker, (a.pk, b.pk)))
        self.assertEqual([org for _, org in outputs], [a.pk, b.pk])
        self.assertTrue(all(summary["member_count"] == 1 for summary, _ in outputs))
        self.assertEqual(
            counts,
            (
                Organization.objects.count(),
                OrganizationAccess.objects.count(),
                get_user_model().objects.count(),
            ),
        )

    def test_guessed_privileged_routes_are_absent_even_for_staff(self):
        user = get_user_model().objects.create_user(
            username="synthetic-workbench-staff", is_staff=True, is_superuser=True
        )
        self.client.force_login(user)
        for path in (
            "/api/v1/memberships/",
            "/api/v1/memberships/import/",
            "/api/v1/memberships/claim/",
        ):
            self.assertEqual(self.client.get(path).status_code, 404)
            self.assertEqual(
                self.client.post(path, {}, content_type="application/json").status_code,
                404,
            )
