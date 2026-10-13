#!/bin/bash
# Reference solution.
#
# Two things are wrong and both live behind the failing test:
#   1. versioning.detect_version sniffs the payload for a "created_at" key
#      instead of reading schema_version. POLICY rule 2 fixes the default:
#      an absent schema_version means version 1, never the latest schema.
#   2. the version 1 upgrade path does not conform to POLICY rules 4 and 5 —
#      it leaves tag whitespace in place and reports a stale schema_version.
#
# This is ONE valid path, not the only one. The rubric scores observable
# properties of the loaded record, not the text of these files.
set -euo pipefail

cat > /app/archive/versioning.py <<'PYEOF'
"""Schema version detection for stored records."""

SCHEMA_LATEST = 2


def detect_version(raw):
    """Return the schema version the record was written with.

    The schema_version field is the only marker. Records written before the
    field existed do not carry it, so an absent field means version 1 — never
    the latest schema. Nothing else about the payload is evidence of a
    version: optional fields may be absent from a record of any version.
    """
    if "schema_version" in raw:
        return int(raw["schema_version"])
    return 1
PYEOF

cat > /app/archive/upgrade.py <<'PYEOF'
"""Upgrade stored records into the canonical latest-schema form."""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from archive.versioning import SCHEMA_LATEST, detect_version


@dataclass
class Record:
    """A stored record in canonical form."""

    id: str
    name: str
    tags: list = field(default_factory=list)
    created_at: object = None
    schema_version: int = SCHEMA_LATEST


def to_canonical(raw):
    """Return the canonical form of one raw stored record."""
    if detect_version(raw) == 2:
        return _from_v2(raw)
    return _from_v1(raw)


def _from_v1(raw):
    return Record(
        id=raw["id"],
        name=raw["name"],
        tags=_split_tags(raw.get("tags")),
        created_at=_epoch_to_iso(raw.get("created", 0)),
        schema_version=SCHEMA_LATEST,
    )


def _from_v2(raw):
    return Record(
        id=raw["id"],
        name=raw["name"],
        tags=list(raw.get("tags") or []),
        created_at=raw.get("created_at"),
        schema_version=SCHEMA_LATEST,
    )


def _split_tags(raw_tags):
    """Split a v1 tag string: strip each tag, drop empties, keep order and duplicates."""
    tags = []
    for segment in (raw_tags or "").split(","):
        tag = segment.strip()
        if tag:
            tags.append(tag)
    return tags


def _epoch_to_iso(epoch):
    moment = datetime.fromtimestamp(epoch, tz=timezone.utc)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")
PYEOF

cd /app && python -m pytest tests -q
