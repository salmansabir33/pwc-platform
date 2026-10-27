from django.http import JsonResponse
from django.urls import include, path
from organizations.directory import DirectoryView
from organizations.views import OrganizationDetailView, OrganizationListView

def health(request):
    return JsonResponse({"status": "ok", "service": "pwc-api"})

urlpatterns = [
    path("api/v1/directory/", DirectoryView.as_view()),
    path("api/v1/controlled-onboarding/", include("organizations.controlled_urls")),
    path("api/v1/verification/", include("organizations.verification_urls")),
    path("api/v1/registry/", include("organizations.registry_urls")),
    path("api/v1/", include("access.urls")),
    path("api/v1/auth/", include("accounts.registration_urls")),
    path("api/v1/health/", health),
    path("api/v1/organizations/", OrganizationListView.as_view()),
    path("api/v1/organizations/<uuid:pk>/", OrganizationDetailView.as_view()),
]
