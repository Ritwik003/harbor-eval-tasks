"""Report computation with caching."""

from .cache import MemoCache
from .data import ROWS
from .keys import build_cache_key

CACHE = MemoCache()


def _in_range(row, start, end):
    return start <= row["date"] <= end


def _compute(params):
    start = params["start"]
    end = params["end"]
    metric = params["metric"]
    region = params["region"]

    selected = [row for row in ROWS if _in_range(row, start, end)]
    if region is not None:
        selected = [row for row in selected if row["region"] == region]

    return {
        "metric": metric,
        "region": region,
        "total": sum(row[metric] for row in selected),
        "row_count": len(selected),
    }


def revenue_report(start, end, metric="revenue", region=None):
    """Aggregate `metric` over the date range, optionally scoped to a region."""
    params = {"start": start, "end": end, "metric": metric, "region": region}
    key = build_cache_key("revenue_report", params)
    return CACHE.get_or_compute(key, lambda: _compute(params))
