"""Closed, bounded claimant DTOs. No reviewer notes, evidence, roles or grants."""

import unicodedata
from rest_framework import serializers
from .models import Organization, OrganizationDraft, OrganizationClaim, RegistryEvent


def clean_text(value):
    value = unicodedata.normalize("NFKC", value)
    if any(unicodedata.category(c).startswith("C") for c in value):
        raise serializers.ValidationError("Unsupported control characters.")
    return " ".join(value.split())


def normalize(value):
    return clean_text(value).casefold()


class ClosedSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if not isinstance(data, dict) or set(data) - set(self.fields):
            raise serializers.ValidationError("Unsupported fields.")
        return super().to_internal_value(data)


class Text(serializers.CharField):
    def to_internal_value(self, value):
        if not isinstance(value, str):
            raise serializers.ValidationError("Expected text.")
        # Normalize before length validation, but bound the raw input too.
        if len(value) > 4 * self.max_length:
            raise serializers.ValidationError("Too long.")
        return super().to_internal_value(clean_text(value))


class DraftInput(ClosedSerializer):
    name = Text(max_length=250)
    legal_name = Text(max_length=250, allow_blank=True, default="")
    aliases = serializers.ListField(
        child=Text(max_length=250), max_length=5, default=list
    )
    city = Text(max_length=100, allow_blank=True, default="")
    jurisdiction = Text(max_length=100, allow_blank=True, default="")
    classification = serializers.ChoiceField(
        choices=Organization.Classification.choices
    )
    contact_email = serializers.EmailField(max_length=254, allow_blank=True, default="")
    contact_phone = Text(max_length=40, allow_blank=True, default="")

    def validate_aliases(self, values):
        return list(dict.fromkeys(values))


class RevisionInput(ClosedSerializer):
    revision = serializers.IntegerField(min_value=1, max_value=9223372036854775807)

    def validate_revision(self, value):
        if type(self.initial_data.get("revision")) is not int:
            raise serializers.ValidationError("Expected integer.")
        return value


class DraftEdit(DraftInput, RevisionInput):
    """Full replacement of editable fields; not partial ambiguous patch semantics."""


class ClaimInput(ClosedSerializer):
    organization_id = serializers.UUIDField()


class DraftOutput(serializers.ModelSerializer):
    class Meta:
        model = OrganizationDraft
        fields = (
            "id",
            "organization_id",
            "name",
            "legal_name",
            "aliases",
            "city",
            "jurisdiction",
            "classification",
            "contact_email",
            "contact_phone",
            "state",
            "revision",
            "created_at",
            "updated_at",
        )


class ClaimOutput(serializers.ModelSerializer):
    class Meta:
        model = OrganizationClaim
        fields = (
            "id",
            "organization_id",
            "state",
            "revision",
            "created_at",
            "updated_at",
        )


class EventOutput(serializers.ModelSerializer):
    class Meta:
        model = RegistryEvent
        fields = ("id", "action", "revision", "created_at")
