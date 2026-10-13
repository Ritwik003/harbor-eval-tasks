"""Schema version detection for stored records."""

SCHEMA_LATEST = 2


def detect_version(raw):
    """Return the schema version the record was written with."""
    if "created_at" in raw:
        return 2
    return 1
