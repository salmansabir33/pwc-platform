from django.urls import path
from .verification_views import VerificationView

urlpatterns = [
    path("cases/", VerificationView.as_view()),
    path("cases/<uuid:pk>/", VerificationView.as_view()),
    path(
        "cases/<uuid:pk>/requirements/",
        VerificationView.as_view(command="requirements"),
    ),
    path("cases/<uuid:pk>/history/", VerificationView.as_view(command="history")),
    path("cases/<uuid:pk>/submit/", VerificationView.as_view(command="submit")),
    path("cases/<uuid:pk>/withdraw/", VerificationView.as_view(command="withdraw")),
    path(
        "cases/<uuid:pk>/preparation/", VerificationView.as_view(command="preparation")
    ),
    path(
        "cases/<uuid:pk>/preparation/<uuid:item_id>/",
        VerificationView.as_view(command="preparation"),
    ),
    path(
        "cases/<uuid:pk>/preparation/<uuid:item_id>/withdraw/",
        VerificationView.as_view(command="preparation-withdraw"),
    ),
    path("cases/<uuid:pk>/evidence/", VerificationView.as_view(command="upload")),
    path(
        "cases/<uuid:pk>/evidence/<uuid:item_id>/download/",
        VerificationView.as_view(command="download"),
    ),
    path("reviewer-queue/", VerificationView.as_view(command="reviewer-queue")),
]
