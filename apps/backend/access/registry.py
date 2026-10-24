"""ADR-0002 frozen synthetic registry; never mutate v1 to broaden a grant."""
from types import MappingProxyType

REGISTRY_VERSION = "ngo_kernel_v1"
ENTER = "ngo.context.enter"
READ = "ngo.private_stub.read"
SETTINGS = "ngo.kernel_settings.read"
ACTIONS = frozenset((ENTER, READ, SETTINGS))
BUNDLES = MappingProxyType({
    ("ngo_kernel_reader", 1): frozenset((ENTER, READ)),
    ("ngo_kernel_admin_probe", 1): frozenset((ENTER, READ, SETTINGS)),
})
