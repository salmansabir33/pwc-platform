from rest_framework import generics, permissions, serializers
from .models import Organization, OrganizationAccess, OrganizationWorkspace

class PublicOrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id", "name", "city", "classification")

class OrganizationListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = PublicOrganizationSerializer
    def get_queryset(self):
        # Only publicly eligible workspaces; never private member records.
        return Organization.objects.filter(workspace__state=OrganizationWorkspace.State.VERIFIED).order_by("name")

class OrganizationDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = PublicOrganizationSerializer
    def get_queryset(self):
        return Organization.objects.filter(workspace__state=OrganizationWorkspace.State.VERIFIED)
