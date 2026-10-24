from django.urls import path
from .views import WorkspaceDiscoveryView, CapabilitiesView, PrivateProbeView, KernelSettingsView

urlpatterns = [
    path("me/ngo-contexts/", WorkspaceDiscoveryView.as_view(), name="ngo-context-discovery"),
    # String converter intentionally reaches kernel validation for malformed UUIDs.
    path("ngo-contexts/<str:organization_uuid>/capabilities/", CapabilitiesView.as_view(), name="ngo-capabilities"),
    path("ngo-contexts/<str:organization_uuid>/private-probe/", PrivateProbeView.as_view(), name="ngo-private-probe"),
    path("ngo-contexts/<str:organization_uuid>/kernel-settings/", KernelSettingsView.as_view(), name="ngo-kernel-settings"),
]
