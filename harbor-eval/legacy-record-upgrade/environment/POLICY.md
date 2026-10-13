# Record storage policy

This document is the specification for how stored records are versioned and
loaded. The loader in `archive/` is required to conform to it.

## Versioning

1. A record's schema version is determined **solely** by its `schema_version`
   field.

2. A record with **no** `schema_version` field is a **version 1** record.
   Version 1 predates the field, so the absence of the field is the only marker
   a version 1 record carries.

3. The version must never be inferred from the shape or the contents of the
   payload. Optional fields may be absent from a record of any version, so the
   presence or absence of any field other than `schema_version` says nothing
   about which version wrote the record.

## Canonical form

4. Loading a record returns it in the canonical latest-schema form. The
   canonical form always reports `schema_version` of 2 — including for records
   that were stored as version 1 and upgraded on read.

## Fields

5. `tags`

   - Version 1 stores tags as a single comma-separated string.
   - Version 2 stores tags as a list of strings.
   - In canonical form `tags` is always a list of strings.
   - When splitting a version 1 tag string: surrounding whitespace is stripped
     from each tag, empty segments are discarded, the stored order is
     preserved, and duplicates are **not** removed.

6. `created_at`

   - Version 1 stores `created`, a Unix epoch integer.
   - Version 2 stores `created_at`, an ISO-8601 UTC timestamp ending in `Z`.
   - In canonical form `created_at` is always the ISO-8601 string.
   - `created_at` is **optional** in version 2. A record stored without one has
     a canonical `created_at` of `None`. A missing creation time is never
     replaced with a default, a placeholder, or the Unix epoch.
