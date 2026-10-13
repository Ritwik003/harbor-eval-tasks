# archive

Read access to the record store.

- `archive/data.py` — the stored records (static in this checkout). Records
  written before the `schema_version` field existed are still present.
- `archive/store.py` — the public read API: `load`, `read_all`, `get`.
- `archive/upgrade.py` — upgrades a stored record to the canonical form.
- `archive/versioning.py` — schema version detection.

`POLICY.md` is the specification the loader is required to conform to.

Run the suite with:

    cd /app && python -m pytest tests
