"""Invitation-only rollout boundary, not an issuer/activation implementation.

No environment flag, repository identity or staff label supplies missing issuer
or privacy acceptance. Synthetic public-flow regression is test-profile only.
"""

from django.conf import settings
from .flow_security import FlowProblem


def require_registration_policy(purpose):
    if purpose == "registration" and settings.PWC_ENVIRONMENT != "test":
        raise FlowProblem("AUTH_UNAVAILABLE", 503)


def readiness():
    return {
        "policy": "invitation_only",
        "ready_for_real_enrollment": False,
        "public_registration": "test_profile_only",
        "invitation_issue_and_accept": "not_implemented_pending_contract",
        "mail_dispatcher": "synthetic_only",
        "deployment_authorized": False,
        "gates": [
            {
                "id": "PE-ISSUER",
                "status": "unaccepted",
                "required": "Authenticated accepted personal-invitation issuer/source, scoped recipients and revocation; repository ownership and staff flags are not authority.",
            },
            {
                "id": "PE-CONTRACT",
                "status": "unaccepted",
                "required": "Recipient binding, invitation lifetime/digest/consumption/lock/audit/storage/API contract and purpose-separated email proof. No invitations, tables or privilege-bearing endpoints before acceptance.",
            },
            {
                "id": "O1-O2",
                "status": "unaccepted",
                "required": "Provider/region/terms, sender/domain verification, deliverability, budget, worker ownership and rate/abuse limits; SMTP adapter is unwired preparation only.",
            },
            {
                "id": "O4",
                "status": "unaccepted",
                "required": "Eligibility, lawful processing basis, notice/version, retention/start/erasure/hold and audit visibility for invitee/contact/security data.",
            },
            {
                "id": "O3-W2",
                "status": "unaccepted",
                "required": "Exact HTTPS hosts, ingress/source-IP budget acceptance, cookie/CSRF, browser transport and actual-host independent acceptance; separate deployment/activation authorization.",
            },
            {
                "id": "IDENTITY",
                "status": "unaccepted",
                "required": "Separate Founder/AbuBakr account/person binding and distinct-human/non-conflict evidence; authority and independent verification remain separate Issue #42 gates.",
            },
        ],
    }
