"""Fixed fictional preview scenarios only; never source authority or real intake."""

from types import MappingProxyType
from uuid import UUID
from .member_import_preview import HEADERS, TEMPLATE, PreviewCatalog, preview_csv

SCENARIOS = ("valid", "duplicate", "invalid")
ORGANIZATION_ID = UUID("00000000-0000-4000-8000-000000000001")
_HEADER = (",".join(HEADERS) + "\n").encode()
FIXTURE_CSV = MappingProxyType(
    {
        "valid": TEMPLATE.sample_csv(),
        "duplicate": _HEADER
        + b"MEMBER_A,Synthetic Person A,ORDINARY\nMEMBER_A,Synthetic Person B,ORDINARY\n",
        "invalid": _HEADER + b"EXISTING,=FORMULA,UNKNOWN\n",
    }
)


class UnknownFixtureScenario(ValueError):
    pass


def preview_fixture(scenario):
    # Also guards call_command's keyword path, which bypasses argparse choices.
    if type(scenario) is not str or scenario not in SCENARIOS:
        raise UnknownFixtureScenario("Unknown synthetic preview scenario")
    return preview_csv(
        FIXTURE_CSV[scenario],
        organization_id=ORGANIZATION_ID,
        catalog=PreviewCatalog(
            ORGANIZATION_ID, frozenset({"ORDINARY"}), frozenset({"EXISTING"})
        ),
    )
