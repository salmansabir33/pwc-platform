"""Synthetic 05A business decisions, not runtime authority or a member writer."""

from dataclasses import FrozenInstanceError, replace
from io import StringIO
import json
from uuid import UUID, uuid4
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase
from .member_import_preview import (
    TEMPLATE,
    ImportPreviewError,
    preview_csv,
    valid_reference,
)
from .membership_preview import (
    MODES,
    ROUTES,
    STATES,
    EVENTS,
    TRANSITIONS,
    CategoryFixture,
    AdmissionRequestFixture,
    MembershipSnapshotFixture,
    AdmissionPreview,
    MembershipPreviewError,
    evaluate_admission,
)
from .membership_fixtures import (
    SCENARIOS,
    preview_membership_fixture,
    UnknownMembershipScenario,
)
from .models import Organization, OrganizationAccess


class MembershipPreviewTests(SimpleTestCase):
    def setUp(self):
        self.organization = uuid4()
        self.category = CategoryFixture(
            self.organization, "ORDINARY", "Synthetic Ordinary"
        )
        self.other_category = CategoryFixture(
            self.organization, "ASSOCIATE", "Synthetic Associate"
        )
        self.request = AdmissionRequestFixture(
            self.organization, "REQUEST_A", "MEMBER_A", "ORDINARY", "application"
        )
        self.snapshot = MembershipSnapshotFixture(
            self.organization, "approval", (self.category, self.other_category)
        )

    def assert_failure(self, code, function, *args, **kwargs):
        with self.assertRaises(MembershipPreviewError) as error:
            function(*args, **kwargs)
        self.assertEqual(error.exception.to_diagnostic(), {"code": code})
        self.assertEqual(str(error.exception), "Invalid membership preview fixture")

    def test_all_mode_route_state_event_combinations_against_explicit_fixture_contract(
        self,
    ):
        expected = {
            ("open", "application", "draft", "apply"): "accepted",
            ("approval", "application", "draft", "apply"): "pending",
            ("approval", "application", "pending", "approve"): "accepted",
            ("approval", "application", "pending", "decline"): "declined",
            ("approval", "application", "pending", "cancel"): "cancelled",
            ("invitation", "invitation", "draft", "invite"): "pending",
            ("invitation", "invitation", "pending", "accept"): "accepted",
            ("invitation", "invitation", "pending", "decline"): "declined",
            ("invitation", "invitation", "pending", "cancel"): "cancelled",
        }
        for mode in MODES:
            for route in ROUTES:
                for state in STATES:
                    request = replace(self.request, route=route, state=state)
                    snapshot = replace(
                        self.snapshot,
                        mode=mode,
                        requests=() if state == "draft" else (request,),
                    )
                    for event in EVENTS:
                        with self.subTest(
                            mode=mode, route=route, state=state, event=event
                        ):
                            result = evaluate_admission(snapshot, request, event)
                            target = expected.get((mode, route, state, event))
                            self.assertEqual(result.proposed_state, target)
                            self.assertEqual(
                                result.transition_valid, target is not None
                            )
                            self.assertIs(
                                result.to_summary()["commit_available"], False
                            )
                            self.assertTrue(result.to_summary()["non_authoritative"])

    def test_open_proposal_never_changes_snapshot_or_creates_a_membership(self):
        snapshot = replace(self.snapshot, mode="open")
        before = (snapshot.requests, snapshot.existing_references, self.request)
        result = evaluate_admission(snapshot, self.request, "apply")
        self.assertEqual(result.proposed_state, "accepted")
        self.assertEqual(
            (snapshot.requests, snapshot.existing_references, self.request), before
        )
        self.assertEqual(self.request.state, "draft")
        self.assertFalse(hasattr(result, "user_id"))
        self.assertFalse(hasattr(result, "grant"))

    def test_own_pending_request_can_be_decided_but_terminal_decisions_cannot_replay(
        self,
    ):
        request = replace(self.request, state="pending")
        snapshot = replace(self.snapshot, requests=(request,))
        self.assertEqual(
            evaluate_admission(snapshot, request, "approve").proposed_state, "accepted"
        )
        for state in ("accepted", "declined", "cancelled"):
            terminal = replace(request, state=state)
            final = replace(snapshot, requests=(terminal,))
            for event in ("approve", "apply", "accept"):
                self.assertEqual(
                    evaluate_admission(final, terminal, event).errors,
                    ("INVALID_TRANSITION",),
                )
            self.assertEqual(
                evaluate_admission(final, self.request, "apply").errors,
                ("STALE_REQUEST",),
            )

    def test_pending_decision_requires_exact_snapshot_not_forged_state_or_category(
        self,
    ):
        pending = replace(self.request, state="pending")
        self.assertEqual(
            evaluate_admission(self.snapshot, pending, "approve").errors,
            ("UNKNOWN_REQUEST",),
        )
        snapshot = replace(self.snapshot, requests=(pending,))
        for changes in (
            {"state": "draft"},
            {"category_reference": "ASSOCIATE"},
            {"record_reference": "MEMBER_B"},
            {"route": "invitation"},
        ):
            forged = replace(pending, **changes)
            self.assertEqual(
                evaluate_admission(snapshot, forged, "approve").errors,
                ("STALE_REQUEST",),
            )

    def test_membership_and_pending_references_block_duplicate_admission_across_categories(
        self,
    ):
        existing = replace(self.snapshot, existing_references=frozenset({"MEMBER_A"}))
        self.assertEqual(
            evaluate_admission(existing, self.request, "apply").errors,
            ("EXISTING_REFERENCE",),
        )
        pending = replace(
            self.request,
            request_reference="REQUEST_B",
            category_reference="ASSOCIATE",
            state="pending",
        )
        snapshot = replace(self.snapshot, requests=(pending,))
        self.assertEqual(
            evaluate_admission(snapshot, self.request, "apply").errors,
            ("DUPLICATE_REFERENCE",),
        )
        accepted = replace(pending, state="accepted")
        self.assertEqual(
            evaluate_admission(
                replace(snapshot, requests=(accepted,)), self.request, "apply"
            ).errors,
            ("DUPLICATE_REFERENCE",),
        )

    def test_declined_and_cancelled_history_does_not_invent_a_permanent_membership(
        self,
    ):
        for state in ("declined", "cancelled"):
            old = replace(self.request, request_reference="REQUEST_OLD", state=state)
            snapshot = replace(self.snapshot, requests=(old,))
            self.assertEqual(
                evaluate_admission(snapshot, self.request, "apply").proposed_state,
                "pending",
            )
            self.assertEqual(snapshot.requests[0].state, state)

    def test_accepted_history_and_its_member_reference_can_coexist_without_double_counting(
        self,
    ):
        accepted = replace(self.request, state="accepted")
        snapshot = replace(
            self.snapshot,
            requests=(accepted,),
            existing_references=frozenset({"MEMBER_A"}),
        )
        self.assertEqual(
            snapshot.to_import_catalog().existing_references, frozenset({"MEMBER_A"})
        )
        self.assertEqual(
            evaluate_admission(snapshot, accepted, "approve").errors,
            ("INVALID_TRANSITION",),
        )

    def test_category_reference_conflicts_include_inactive_categories(self):
        duplicate = replace(
            self.category, label="Different synthetic label", active=False
        )
        self.assert_failure(
            "DUPLICATE_CATEGORY_REFERENCE",
            replace,
            self.snapshot,
            categories=(self.category, duplicate),
        )

    def test_active_label_conflicts_use_nfkc_casefold_and_whitespace_normalization(
        self,
    ):
        for label in ("  SYNTHETIC   ORDINARY  ", "Ｓｙｎｔｈｅｔｉｃ Ordinary"):
            duplicate = replace(self.other_category, label=label)
            self.assert_failure(
                "DUPLICATE_CATEGORY_LABEL",
                replace,
                self.snapshot,
                categories=(self.category, duplicate),
            )
            inactive = replace(duplicate, active=False)
            self.assertEqual(
                len(
                    replace(
                        self.snapshot, categories=(self.category, inactive)
                    ).categories
                ),
                2,
            )

    def test_unknown_inactive_category_and_inactive_policy_fail_closed(self):
        self.assertEqual(
            evaluate_admission(
                self.snapshot,
                replace(self.request, category_reference="UNKNOWN"),
                "apply",
            ).errors,
            ("UNKNOWN_CATEGORY",),
        )
        inactive = replace(
            self.snapshot, categories=(replace(self.category, active=False),)
        )
        self.assertEqual(
            evaluate_admission(inactive, self.request, "apply").errors,
            ("INACTIVE_CATEGORY",),
        )
        self.assertEqual(
            evaluate_admission(
                replace(self.snapshot, active=False), self.request, "apply"
            ).errors,
            ("INACTIVE_POLICY",),
        )

    def test_policy_change_or_unsupported_event_does_not_infer_a_transition(self):
        for event in ("grant", "pay", "renew", "private-canary", True, None, []):
            self.assertEqual(
                evaluate_admission(self.snapshot, self.request, event).errors,
                ("UNSUPPORTED_EVENT",),
            )
        pending = replace(self.request, state="pending")
        snapshot = replace(self.snapshot, mode="invitation", requests=(pending,))
        self.assertEqual(
            evaluate_admission(snapshot, pending, "approve").errors,
            ("MODE_ROUTE_CONFLICT",),
        )
        snapshot = replace(snapshot, mode="open")
        self.assertEqual(
            evaluate_admission(snapshot, pending, "approve").errors,
            ("INVALID_TRANSITION",),
        )

    def test_snapshot_rejects_request_conflicts_and_missing_categories(self):
        pending = replace(self.request, state="pending")
        duplicate = replace(
            pending, request_reference="REQUEST_B", category_reference="ASSOCIATE"
        )
        self.assert_failure(
            "DUPLICATE_REFERENCE", replace, self.snapshot, requests=(pending, duplicate)
        )
        self.assert_failure(
            "DUPLICATE_REFERENCE",
            replace,
            self.snapshot,
            requests=(pending,),
            existing_references=frozenset({"MEMBER_A"}),
        )
        self.assert_failure(
            "DUPLICATE_REQUEST_REFERENCE",
            replace,
            self.snapshot,
            requests=(pending, pending),
        )
        self.assert_failure(
            "UNKNOWN_CATEGORY",
            replace,
            self.snapshot,
            requests=(replace(pending, category_reference="UNKNOWN"),),
        )

    def test_cross_ngo_requests_fail_before_any_policy_or_conflict_information(self):
        foreign = replace(self.request, organization_id=uuid4())
        result = evaluate_admission(self.snapshot, foreign, "private-canary")
        self.assertEqual(result.errors, ("TENANT_MISMATCH",))
        self.assertEqual(result.organization_id, self.organization)
        self.assertNotIn(str(foreign.organization_id), json.dumps(result.to_summary()))
        self.assert_failure(
            "TENANT_MISMATCH", replace, self.snapshot, requests=(foreign,)
        )
        foreign_category = replace(
            self.category, organization_id=foreign.organization_id
        )
        self.assert_failure(
            "TENANT_MISMATCH",
            replace,
            self.snapshot,
            categories=(self.category, foreign_category),
        )

    def test_identical_references_and_labels_in_different_ngos_remain_independent(self):
        pending = replace(self.request, state="pending")
        first = replace(self.snapshot, requests=(pending,))
        other_org = uuid4()
        other_request = replace(self.request, organization_id=other_org)
        second = MembershipSnapshotFixture(
            other_org, "open", (replace(self.category, organization_id=other_org),)
        )
        self.assertEqual(
            evaluate_admission(first, self.request, "apply").errors, ("STALE_REQUEST",)
        )
        self.assertEqual(
            evaluate_admission(second, other_request, "apply").proposed_state,
            "accepted",
        )
        self.assertEqual(
            evaluate_admission(first, pending, "approve").proposed_state, "accepted"
        )
        self.assertEqual(first.requests, (pending,))

    def test_05b_adapter_reuses_parser_without_claiming_structural_acceptance_is_admission(
        self,
    ):
        pending = replace(
            self.request,
            request_reference="REQUEST_B",
            record_reference="MEMBER_B",
            state="pending",
        )
        accepted = replace(self.request, state="accepted")
        snapshot = replace(
            self.snapshot,
            requests=(accepted, pending),
            existing_references=frozenset({"EXISTING"}),
        )
        report = preview_csv(
            TEMPLATE.sample_csv(),
            organization_id=self.organization,
            catalog=snapshot.to_import_catalog(),
        )
        self.assertEqual(report.rows[0].errors, ("EXISTING_REFERENCE",))
        self.assertEqual(report.rows[1].errors, ())
        duplicate = replace(
            self.request, request_reference="REQUEST_C", record_reference="MEMBER_B"
        )
        self.assertEqual(
            evaluate_admission(snapshot, duplicate, "apply").errors,
            ("DUPLICATE_REFERENCE",),
        )
        self.assertEqual(
            snapshot.to_import_catalog().existing_references,
            frozenset({"EXISTING", "MEMBER_A"}),
        )

    def test_05b_adapter_excludes_inactive_categories_and_preserves_tenant_binding(
        self,
    ):
        snapshot = replace(
            self.snapshot,
            categories=(replace(self.category, active=False), self.other_category),
        )
        report = preview_csv(
            TEMPLATE.sample_csv(),
            organization_id=self.organization,
            catalog=snapshot.to_import_catalog(),
        )
        self.assertTrue(all(r.errors == ("UNKNOWN_CATEGORY",) for r in report.rows))
        self.assertFalse(replace(snapshot, active=False).to_import_catalog().categories)
        with self.assertRaises(ImportPreviewError) as error:
            preview_csv(
                TEMPLATE.sample_csv(),
                organization_id=uuid4(),
                catalog=snapshot.to_import_catalog(),
            )
        self.assertEqual(error.exception.code, "CATALOG_TENANT_MISMATCH")

    def test_handles_reuse_05b_syntax_and_reject_identity_or_authority_inputs(self):
        for value in (
            "",
            "lowercase",
            "A" * 65,
            "person@example.invalid",
            "=FORMULA",
            None,
            [],
            True,
        ):
            self.assertFalse(valid_reference(value))
            self.assert_failure(
                "INVALID_INPUT", replace, self.request, record_reference=value
            )
        for changes in (
            {"state": "paid"},
            {"state": "admin"},
            {"route": "staff"},
            {"organization_id": UUID(int=0)},
        ):
            self.assert_failure("INVALID_INPUT", replace, self.request, **changes)
        for changes in (
            {"mode": "paid"},
            {"mode": []},
            {"active": 1},
            {"categories": list(self.snapshot.categories)},
            {"requests": []},
            {"existing_references": set()},
            {"organization_id": "private-canary"},
        ):
            self.assert_failure("INVALID_INPUT", replace, self.snapshot, **changes)
        for changes in (
            {"label": "\u202eprivate"},
            {"label": " "},
            {"label": "x" * 251},
            {"label": None},
            {"active": 1},
        ):
            self.assert_failure("INVALID_INPUT", replace, self.category, **changes)
        self.assert_failure(
            "INVALID_INPUT", evaluate_admission, {}, self.request, "apply"
        )

    def test_technical_fixture_bounds_are_enforced_without_defining_real_business_quotas(
        self,
    ):
        categories = tuple(
            CategoryFixture(self.organization, f"C{i}", f"Synthetic {i}")
            for i in range(200)
        )
        self.assertEqual(
            len(replace(self.snapshot, categories=categories).categories), 200
        )
        self.assert_failure(
            "INVALID_INPUT",
            replace,
            self.snapshot,
            categories=categories + (self.category,),
        )
        self.assert_failure(
            "INVALID_INPUT", replace, self.snapshot, requests=(self.request,) * 201
        )
        self.assert_failure(
            "INVALID_INPUT",
            replace,
            self.snapshot,
            existing_references=frozenset(f"R{i}" for i in range(201)),
        )

    def test_immutable_reports_and_value_free_projection_are_deterministic(self):
        category = replace(self.category, label="Private canary person@example.invalid")
        snapshot = replace(self.snapshot, categories=(category,))
        request = replace(
            self.request,
            record_reference="SECRET_RECORD",
            request_reference="SECRET_REQUEST",
        )
        result = evaluate_admission(snapshot, request, "apply")
        for value, key, replacement in (
            (category, "active", False),
            (request, "state", "accepted"),
            (snapshot, "mode", "open"),
            (result, "proposed_state", "accepted"),
        ):
            with self.assertRaises(FrozenInstanceError):
                setattr(value, key, replacement)
        with self.assertRaises(TypeError):
            TRANSITIONS[("open", "application", "draft", "apply")] = "pending"
        text = json.dumps(result.to_summary())
        for private in (
            "canary",
            "example.invalid",
            "SECRET_REQUEST",
            "SECRET_RECORD",
            "ORDINARY",
        ):
            self.assertNotIn(private, text)
            self.assertNotIn(private, repr(snapshot))
        summary = result.to_summary()
        summary["errors"].append("PRIVATE")
        self.assertEqual(
            result.to_summary(),
            evaluate_admission(snapshot, request, "apply").to_summary(),
        )
        self.assert_failure(
            "INVALID_INPUT",
            AdmissionPreview,
            self.organization,
            None,
            ["INVALID_INPUT"],
        )
        self.assert_failure(
            "INVALID_INPUT",
            AdmissionPreview,
            self.organization,
            "accepted",
            ("INVALID_INPUT",),
        )
        self.assert_failure(
            "INVALID_INPUT",
            AdmissionPreview,
            self.organization,
            None,
            ("private-canary",),
        )

    def test_fixed_cli_scenarios_include_system_checks_but_never_database_access(self):
        expected = {
            "open": ("accepted",),
            "approval": ("pending", "accepted"),
            "invitation": ("pending", "accepted"),
            "conflict": (None,),
        }
        for scenario in SCENARIOS:
            output = StringIO()
            if scenario == "conflict":
                with self.assertRaises(CommandError):
                    call_command(
                        "preview_membership_fixture",
                        scenario=scenario,
                        stdout=output,
                        skip_checks=False,
                    )
            else:
                call_command(
                    "preview_membership_fixture",
                    scenario=scenario,
                    stdout=output,
                    skip_checks=False,
                )
            report = json.loads(output.getvalue())
            self.assertEqual(
                set(report), {"synthetic_only", "commit_available", "steps"}
            )
            self.assertTrue(report["synthetic_only"])
            self.assertIs(report["commit_available"], False)
            self.assertEqual(
                tuple(s["proposed_state"] for s in report["steps"]), expected[scenario]
            )
            self.assertEqual(
                report["steps"],
                [p.to_summary() for p in preview_membership_fixture(scenario)],
            )
            self.assertNotIn("Synthetic Ordinary", output.getvalue())
            self.assertNotIn("MEMBER_A", output.getvalue())
        self.assertEqual(report["steps"][0]["errors"], ["DUPLICATE_REFERENCE"])

    def test_unsupported_programmatic_scenarios_fail_with_constant_redacted_error(self):
        for scenario in ("../private.csv", "private-canary", "", None, [], True):
            with self.assertRaises(UnknownMembershipScenario):
                preview_membership_fixture(scenario)
            output = StringIO()
            with self.assertRaises(CommandError) as error:
                call_command(
                    "preview_membership_fixture",
                    scenario=scenario,
                    stdout=output,
                    skip_checks=False,
                )
            self.assertEqual(
                str(error.exception), "Unknown synthetic membership scenario"
            )
            self.assertEqual(output.getvalue(), "")


class MembershipPreviewPostgreSQLTests(TestCase):
    def test_preparation_is_zero_query_zero_write_and_keeps_ngos_and_authority_separate(
        self,
    ):
        a = Organization.objects.create(name="Synthetic Membership A")
        b = Organization.objects.create(name="Synthetic Membership B")
        counts = (
            Organization.objects.count(),
            get_user_model().objects.count(),
            OrganizationAccess.objects.count(),
        )
        with self.assertNumQueries(0):
            category_a = CategoryFixture(a.pk, "ORDINARY", "Synthetic Ordinary")
            category_b = replace(category_a, organization_id=b.pk)
            request_a = AdmissionRequestFixture(
                a.pk, "REQUEST_A", "MEMBER_A", "ORDINARY", "application"
            )
            request_b = replace(request_a, organization_id=b.pk)
            first = MembershipSnapshotFixture(
                a.pk,
                "approval",
                (category_a,),
                existing_references=frozenset({"MEMBER_A"}),
            )
            second = MembershipSnapshotFixture(b.pk, "open", (category_b,))
            rejected = evaluate_admission(first, request_a, "apply").to_summary()
            proposed = evaluate_admission(second, request_b, "apply").to_summary()
            foreign = evaluate_admission(first, request_b, "apply").to_summary()
            imported = preview_csv(
                TEMPLATE.sample_csv(),
                organization_id=b.pk,
                catalog=second.to_import_catalog(),
            ).to_summary()
            for scenario in SCENARIOS:
                preview_membership_fixture(scenario)
        self.assertEqual(rejected["errors"], ["EXISTING_REFERENCE"])
        self.assertEqual(proposed["proposed_state"], "accepted")
        self.assertEqual(foreign["errors"], ["TENANT_MISMATCH"])
        self.assertEqual(imported["accepted_count"], 2)
        self.assertEqual(
            counts,
            (
                Organization.objects.count(),
                get_user_model().objects.count(),
                OrganizationAccess.objects.count(),
            ),
        )
