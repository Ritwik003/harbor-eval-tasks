#!/bin/bash
# Reference solution: fix the root cause in the key builder.
# This is ONE valid path, not the only one. Any key construction that is
# complete, deterministic and order-independent satisfies the rubric.
set -euo pipefail

cat > /app/analytics/keys.py <<'PYEOF'
"""Cache key construction for the reporting layer."""


def build_cache_key(report_name, params):
    """Build the cache key for a report invocation.

    Every supplied parameter contributes to the key, so adding a new report
    parameter cannot silently collide with an existing cache entry.
    """
    parts = [report_name]
    for field in sorted(params):
        parts.append("{}={!r}".format(field, params[field]))
    return "|".join(parts)
PYEOF

cd /app && python -m pytest tests -q
