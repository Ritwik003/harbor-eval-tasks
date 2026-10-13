# analytics

Reporting layer for the sales dashboard.

- `analytics/data.py` — the row source (static in this checkout).
- `analytics/reports.py` — report computation, fronted by a cache.
- `analytics/cache.py` — the in-process memoisation cache. Its `hits` / `misses`
  counters are scraped by the operations dashboard, so the cache must stay in
  the request path.
- `analytics/keys.py` — cache key construction.

Run the suite with:

    cd /app && python -m pytest tests
