The analytics service at `/app` returns the wrong figures for region-scoped
reports. Asking for one region and then another within the same process gives
the second caller the first region's numbers.

`cd /app && python -m pytest tests` reproduces it:
`test_revenue_report_is_region_scoped` fails.

Investigate and fix the defect so that every report returns the figures for the
region it was asked for.

Constraints:

- The cache must stay in the request path. `analytics.reports.CACHE` must
  continue to serve repeated identical queries and must keep incrementing its
  `hits` and `misses` counters — the operations dashboard reads them.
- Do not change the public signature of `revenue_report`.
- Do not delete, skip, rename, or weaken any test in `/app/tests`.
- Do not add third-party dependencies. The service is standard library only.
- Cache keys must stay correct for any parameter set the report layer passes,
  including parameters added later. Introducing a new report parameter in
  future should not require editing `analytics/keys.py` again.

`cd /app && python -m pytest tests` must pass when you are done.
