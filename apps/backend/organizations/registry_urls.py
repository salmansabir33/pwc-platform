from django.urls import path
from .registry_views import RegistryView

urlpatterns = [path("search/", RegistryView.as_view(resource="search"))]
for plural, kind in (("drafts", "draft"), ("claims", "claim")):
    urlpatterns += [
        path(plural + "/", RegistryView.as_view(resource=kind)),
        path(plural + "/<uuid:pk>/", RegistryView.as_view(resource=kind)),
        path(
            plural + "/<uuid:pk>/withdraw/",
            RegistryView.as_view(resource=kind, command="withdraw"),
        ),
        path(
            plural + "/<uuid:pk>/history/",
            RegistryView.as_view(resource=kind, command="history"),
        ),
    ]
urlpatterns += [
    path(
        "drafts/<uuid:pk>/submit/",
        RegistryView.as_view(resource="draft", command="submit"),
    )
]
