"""Read-only aggregate of existing claimant-owned history; no new intake."""

from .registry_views import RegistryView
from .workspace import history


class WorkspaceView(RegistryView):
    http_method_names = ["get"]
    resource = "workspace"

    def read(self, request, user, pk):
        return history(user, request.query_params)
