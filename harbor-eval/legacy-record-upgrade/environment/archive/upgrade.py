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
    raw_tags = raw.get("tags") or ""
    tags = [tag for tag in raw_tags.split(",") if tag]
    return Record(
        id=raw["id"],
        name=raw["name"],
        tags=tags,
        created_at=_epoch_to_iso(raw.get("created", 0)),
        schema_version=1,
    )


def _from_v2(raw):
    return Record(
        id=raw["id"],
        name=raw["name"],
        tags=list(raw.get("tags", [])),
        created_at=raw.get("created_at"),
        schema_version=SCHEMA_LATEST,
    )


def _epoch_to_iso(epoch):
    moment = datetime.fromtimestamp(epoch, tz=timezone.utc)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")
