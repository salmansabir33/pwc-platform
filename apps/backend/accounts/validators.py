"""Password validation only; this does not set passwords or authenticate users."""

from django.core.exceptions import ValidationError


class MaximumLengthValidator:
    def __init__(self, max_length=128):
        self.max_length = max_length

    def validate(self, password, user=None):
        if len(password) > self.max_length:
            raise ValidationError(self.get_help_text(), code="password_too_long")

    def get_help_text(self):
        return f"Your password must contain at most {self.max_length} characters."
