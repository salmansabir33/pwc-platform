"""Explicit public candidate projection; no write serializer or private relations."""

from rest_framework import serializers
from organizations.views import PublicOrganizationSerializer
from .models import Opportunity


class PublicOpportunitySerializer(serializers.ModelSerializer):
    organization = PublicOrganizationSerializer(read_only=True)

    class Meta:
        model = Opportunity
        fields = ("id", "organization", "type", "title", "summary", "published_at")
        read_only_fields = fields
