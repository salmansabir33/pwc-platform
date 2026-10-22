from django.http import JsonResponse
from django.urls import path
from organizations.views import OrganizationDetailView, OrganizationListView

def health(request):
    return JsonResponse({"status": "ok", "service": "pwc-api"})

urlpatterns = [
    path("api/v1/health/", health),
    path("api/v1/organizations/", OrganizationListView.as_view()),
    path("api/v1/organizations/<uuid:pk>/", OrganizationDetailView.as_view()),
]
