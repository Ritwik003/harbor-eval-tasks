The record archive at `/app` loads some stored records incorrectly. Records
that the vendor feed imported without a creation time come back carrying a
timestamp they were never stored with — `u-2003` loads with a `created_at` of
`1970-01-01T00:00:00Z` instead of none at all.

`cd /app && python -m pytest tests` reproduces it:
`test_imported_record_has_no_creation_time` fails.

Investigate and fix the defect so that every stored record loads as
`POLICY.md` specifies.

Constraints:

- `POLICY.md` is the specification for this loader. The loaded form of every
  record must conform to it. Do not edit `POLICY.md`.
- The store holds records in both formats and will keep doing so. Records
  written before the `schema_version` field existed are still live data and
  must continue to load completely — losing, corrupting or defaulting any of
  their fields is a failure even when no repository test covers it.
- Do not edit `archive/data.py`. The stored records are the input to this
  problem, not something to rewrite or backfill.
- Do not change the public API of `archive.store` — `load`, `read_all` and
  `get` keep their names and their meanings.
- Do not delete, skip, rename, or weaken any test in `/app/tests`.
- Do not add third-party dependencies. The service is standard library only.

`cd /app && python -m pytest tests` must pass when you are done.
