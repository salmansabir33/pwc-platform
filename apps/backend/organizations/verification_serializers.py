from rest_framework import serializers
from .registry_serializers import ClosedSerializer, RevisionInput
from .models import VerificationCase, EvidencePreparation, VerificationEvent


class CaseInput(ClosedSerializer):
    source_kind = serializers.ChoiceField(choices=["draft", "claim"])
    source_id = serializers.UUIDField()
    source_revision = serializers.IntegerField(
        min_value=1, max_value=9223372036854775807
    )
    purpose = serializers.ChoiceField(choices=VerificationCase.Purpose.choices)

    def validate_source_revision(self, value):
        if type(self.initial_data.get("source_revision")) is not int:
            raise serializers.ValidationError("Expected integer.")
        return value


class PreparationInput(ClosedSerializer):
    case_revision = serializers.IntegerField(min_value=1, max_value=9223372036854775807)
    prepared_offline = serializers.BooleanField()

    def validate(self, attrs):
        if (
            type(self.initial_data.get("case_revision")) is not int
            or type(self.initial_data.get("prepared_offline")) is not bool
        ):
            raise serializers.ValidationError("Expected exact scalar types.")
        return attrs


class PreparationEdit(PreparationInput, RevisionInput):
    pass


class CaseOutput(serializers.ModelSerializer):
    source_kind = serializers.SerializerMethodField()
    source_id = serializers.SerializerMethodField()

    def get_source_kind(self, case):
        return "draft" if case.draft_id else "claim"

    def get_source_id(self, case):
        return str(case.draft_id or case.claim_id)

    class Meta:
        model = VerificationCase
        fields = (
            "id",
            "organization_id",
            "source_kind",
            "source_id",
            "source_revision",
            "purpose",
            "track",
            "state",
            "revision",
            "created_at",
            "updated_at",
        )


class PreparationOutput(serializers.ModelSerializer):
    class Meta:
        model = EvidencePreparation
        fields = (
            "id",
            "case_id",
            "prepared_offline",
            "state",
            "revision",
            "created_at",
            "updated_at",
        )


class HistoryOutput(serializers.ModelSerializer):
    class Meta:
        model = VerificationEvent
        fields = (
            "id",
            "reason_code",
            "revision",
            "preparation_id",
            "preparation_revision",
            "prepared_offline",
            "created_at",
        )
