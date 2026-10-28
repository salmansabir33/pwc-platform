"""Read-only aggregate of existing claimant-owned history; no new intake."""

from .registry_views import RegistryView
from .workspace import history, detail
from accounts.flow_security import FlowProblem


class WorkspaceView(RegistryView):
    http_method_names = ["get"]
    resource = "workspace"

    def read(self, request, user, pk):
        return history(user, request.query_params)


class WorkspaceDetailView(RegistryView):
    http_method_names = ["get"]
    resource = "workspace"
    kind = None

    def read(self, request, user, pk):
        if request.query_params:
            raise FlowProblem("VALIDATION_ERROR")
        return detail(user, self.kind, pk)
