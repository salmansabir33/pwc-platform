from django.urls import path
from .controlled_views import ControlledOnboardingView

urlpatterns = [
    path("requirements/", ControlledOnboardingView.as_view(command="requirements")),
    path("records/", ControlledOnboardingView.as_view()),
    path("records/<uuid:pk>/", ControlledOnboardingView.as_view(command="record")),
    path(
        "invitations/<uuid:pk>/accept/",
        ControlledOnboardingView.as_view(command="accept"),
    ),
]
for command in ("submit", "approve", "reject", "return", "withdraw", "invitation"):
    urlpatterns.append(
        path(
            "records/<uuid:pk>/" + command + "/",
            ControlledOnboardingView.as_view(command=command),
        )
    )
