"""No public username fallback. Issuance services recheck under owner locks."""

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.views.decorators.debug import sensitive_variables
from .email_identity import normalize_email
from .models import User, UserContact

# A process-local dummy hash, not a credential or a shortcut for actual checks.
DUMMY_HASH = make_password("synthetic-noncredential-dummy-hash")


@sensitive_variables()
def password_candidate(email, password):
    try:
        target = normalize_email(email)
    except ValidationError:
        target = ""
    contact = (
        UserContact.objects.select_related("user")
        .filter(
            kind="email",
            normalized_value=target,
            is_primary=True,
            verified_at__isnull=False,
            retired_at__isnull=True,
        )
        .first()
    )
    user = contact.user if contact else None
    encoded = user.password if user and user.has_usable_password() else DUMMY_HASH
    valid = check_password(password, encoded)
    if not valid or not user or not user.is_active or not user.has_usable_password():
        return None
    return user, contact, target


class VerifiedEmailBackend(BaseBackend):
    @sensitive_variables()
    def authenticate(self, request, email=None, password=None, **kwargs):
        if not isinstance(password, str) or len(password) > 128:
            return None
        candidate = password_candidate(email, password)
        return candidate[0] if candidate else None

    def get_user(self, user_id):
        # Registry middleware adds online cookie/session/epoch/contact validation.
        return User.objects.filter(pk=user_id, is_active=True).first()
