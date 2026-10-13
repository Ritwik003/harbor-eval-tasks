"""The stored records, exactly as they sit in the data store.

Records written before the ``schema_version`` field was introduced are still
present here; the store has never been rewritten in place.
"""

RAW_RECORDS = [
    # Written before the schema_version field existed.
    {
        "id": "u-1001",
        "name": "Ada Lovelace",
        "tags": "admin, ops",
        "created": 1700000000,
    },
    {
        "id": "u-1002",
        "name": "Grace Hopper",
        "tags": "compiler,navy, compiler",
        "created": 1700086400,
    },
    {
        "id": "u-1003",
        "name": "Karen Sparck Jones",
        "tags": "",
        "created": 1700172800,
    },
    # Written by the current writer.
    {
        "schema_version": 2,
        "id": "u-2001",
        "name": "Radia Perlman",
        "tags": ["network", "spanning-tree"],
        "created_at": "2024-01-15T08:30:00Z",
    },
    {
        "schema_version": 2,
        "id": "u-2002",
        "name": "Barbara Liskov",
        "tags": ["types"],
        "created_at": "2024-02-20T11:45:00Z",
    },
    # Imported from the vendor feed: the feed supplied no creation time.
    {
        "schema_version": 2,
        "id": "u-2003",
        "name": "Margaret Hamilton",
    },
]
