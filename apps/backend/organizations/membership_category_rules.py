"""Authority-free C1 product value rules, P4-C1-20261104.1 R02/R05.

Shared by existing preparation code and future accepted services. These functions
validate values only: no tenant lookup, permission, write, read projection or
transport contract is implied. Labels are never rewritten for display/storage.
"""

import unicodedata

ADMISSION_MODES = ("open", "approval", "invitation")
CATEGORY_LABEL_MAX_LENGTH = 250


def valid_category_label(value):
    """R02: Unicode code points, nonblank, no Unicode C-category characters."""
    return (
        type(value) is str
        and bool(value.strip())
        and len(value) <= CATEGORY_LABEL_MAX_LENGTH
        and not any(unicodedata.category(c).startswith("C") for c in value)
    )


def category_label_key(value):
    """R02 active-label comparison key; caller must scope uniqueness by NGO.

    Inactive labels do not reserve a name. This function neither queries nor
    enforces uniqueness. No truncation of the normalized key is permitted.
    """
    if not valid_category_label(value):
        # Never include rejected private input in logs/diagnostics.
        raise ValueError("Invalid category label")
    return " ".join(unicodedata.normalize("NFKC", value).split()).casefold()
