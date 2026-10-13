"""Read access to the record store.

This is the public surface other services import.
"""

from archive.data import RAW_RECORDS
from archive.upgrade import to_canonical


def load(raw):
    """Return the canonical form of a single raw stored record."""
    return to_canonical(raw)


def read_all():
    """Return every stored record in canonical form."""
    return [load(raw) for raw in RAW_RECORDS]


def get(record_id):
    """Return one stored record in canonical form."""
    for record in read_all():
        if record.id == record_id:
            return record
    raise KeyError(record_id)
