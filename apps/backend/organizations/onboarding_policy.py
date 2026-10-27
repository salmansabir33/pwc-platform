"""27 October 2026 initial rollout. No production escape or operator bootstrap."""

from django.conf import settings


def historical_test_exercise():
    # Not environment-configurable, never consulted for controlled commands.
    # Retains historical wire regression coverage without reopening rollout.
    return (
        settings.PWC_ENVIRONMENT == "test"
        and getattr(settings, "PWC_LEGACY_ONBOARDING_TEST_EXERCISE", False) is True
    )


POLICY = {
    "policy_version": "offline_initial_2026_10_27",
    "self_service_available": False,
    "raw_documents_accepted": False,
    "operator_commands_available": False,
    "invitation_available": False,
    "grant_activation_available": False,
    "required_separation": "independently_authorized_distinct_individuals",
    "blockers": [
        "reviewer_provisioning_root",
        "issuer_command_matrix",
        "command_assurance",
        "privacy_reference_contract",
        "recipient_bound_invitation_contract",
    ],
}
