"""Cache key construction for the reporting layer."""

_KEY_FIELDS = ("start", "end", "metric")


def build_cache_key(report_name, params):
    """Build the cache key for a report invocation."""
    parts = [report_name]
    for field in _KEY_FIELDS:
        parts.append("{}={}".format(field, params.get(field)))
    return "|".join(parts)
