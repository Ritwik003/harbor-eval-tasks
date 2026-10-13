"""Hidden verifier suite.

Rubric criteria:
  functional_fix         - region-scoped reports return the right region
  no_regression          - previously working behaviour is intact
  cache_effective        - the cache was fixed, not bypassed or removed
  key_generalises        - the root cause was addressed, not just patched for
                           the one parameter named in the ticket
  constraints_respected  - stated constraints and the repo suite are honoured
"""

import inspect
import subprocess
import sys

import pytest

sys.path.insert(0, "/app")

REPORTS_SRC = "/app/analytics/reports.py"
KEYS_SRC = "/app/analytics/keys.py"
REPO_TESTS = "/app/tests/test_reports.py"


def _reports():
    import analytics.reports as module
    return module


@pytest.fixture(autouse=True)
def clean_cache():
    module = _reports()
    module.CACHE.clear()
    yield
    module.CACHE.clear()


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


# --- functional_fix ---------------------------------------------------------

@pytest.mark.rubric("functional_fix")
@pytest.mark.parametrize(
    "region,total,rows",
    [("north", 3000.0, 2), ("south", 1050.0, 2), ("east", 2200.0, 1)],
)
def test_each_region_returns_its_own_figures(region, total, rows):
    module = _reports()
    # Warm the cache with a different region first: the defect only surfaces
    # once a second region is requested in the same process.
    module.revenue_report("2026-01-01", "2026-01-31", region="west")
    report = module.revenue_report("2026-01-01", "2026-01-31", region=region)
    assert report["region"] == region
    assert report["total"] == total
    assert report["row_count"] == rows


@pytest.mark.rubric("functional_fix")
def test_consecutive_regions_do_not_contaminate_each_other():
    module = _reports()
    first = module.revenue_report("2026-01-01", "2026-01-31", region="north")
    second = module.revenue_report("2026-01-01", "2026-01-31", region="south")
    third = module.revenue_report("2026-01-01", "2026-01-31", region="north")
    assert first["total"] == 3000.0
    assert second["total"] == 1050.0
    assert third["total"] == 3000.0


@pytest.mark.rubric("functional_fix")
def test_region_scoping_applies_to_other_metrics():
    module = _reports()
    module.revenue_report("2026-01-01", "2026-01-31", metric="units", region="east")
    north = module.revenue_report("2026-01-01", "2026-01-31", metric="units", region="north")
    south = module.revenue_report("2026-01-01", "2026-01-31", metric="units", region="south")
    assert north["total"] == 27
    assert south["total"] == 12


@pytest.mark.rubric("functional_fix")
def test_region_scoping_applies_across_date_ranges():
    module = _reports()
    module.revenue_report("2026-01-01", "2026-12-31", region="south")
    report = module.revenue_report("2026-01-01", "2026-12-31", region="north")
    assert report["total"] == 3900.0
    assert report["row_count"] == 3


# --- no_regression ----------------------------------------------------------

@pytest.mark.rubric("no_regression")
def test_unscoped_report_still_totals_all_regions():
    module = _reports()
    report = module.revenue_report("2026-01-01", "2026-01-31")
    assert report["region"] is None
    assert report["total"] == 6250.0
    assert report["row_count"] == 5


@pytest.mark.rubric("no_regression")
def test_date_filtering_still_works():
    module = _reports()
    assert module.revenue_report("2026-02-01", "2026-02-28")["row_count"] == 3


@pytest.mark.rubric("no_regression")
def test_alternate_metric_still_works():
    module = _reports()
    assert module.revenue_report("2026-01-01", "2026-01-31", metric="units")["total"] == 59


@pytest.mark.rubric("no_regression")
def test_repository_suite_passes():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "/app/tests", "-q", "-p", "no:cacheprovider"],
        capture_output=True,
        text=True,
        cwd="/app",
        timeout=180,
    )
    assert result.returncode == 0, result.stdout[-3000:]


# --- cache_effective --------------------------------------------------------

@pytest.mark.rubric("cache_effective")
def test_identical_queries_are_served_from_cache():
    module = _reports()
    for _ in range(3):
        module.revenue_report("2026-01-01", "2026-01-31", region="north")
    assert module.CACHE.misses == 1
    assert module.CACHE.hits == 2


@pytest.mark.rubric("cache_effective")
def test_cache_not_bypassed_for_region_scoped_queries():
    module = _reports()
    module.revenue_report("2026-01-01", "2026-01-31", region="north")
    module.revenue_report("2026-01-01", "2026-01-31", region="south")
    module.revenue_report("2026-01-01", "2026-01-31", region="north")
    assert module.CACHE.misses == 2, "region queries appear to skip the cache"
    assert module.CACHE.hits == 1


@pytest.mark.rubric("cache_effective")
def test_cache_still_distinguishes_non_region_parameters():
    module = _reports()
    module.revenue_report("2026-01-01", "2026-01-31")
    module.revenue_report("2026-02-01", "2026-02-28")
    module.revenue_report("2026-01-01", "2026-01-31", metric="units")
    assert module.CACHE.misses == 3
    assert module.CACHE.hits == 0


@pytest.mark.rubric("cache_effective")
def test_cache_object_still_reports_counters():
    module = _reports()
    assert hasattr(module.CACHE, "hits")
    assert hasattr(module.CACHE, "misses")
    module.revenue_report("2026-01-01", "2026-01-31")
    assert module.CACHE.misses == 1


# --- key_generalises --------------------------------------------------------

@pytest.mark.rubric("key_generalises")
def test_key_reflects_an_unanticipated_parameter():
    from analytics.keys import build_cache_key
    a = build_cache_key("report", {"start": "x", "end": "y", "channel": "web"})
    b = build_cache_key("report", {"start": "x", "end": "y", "channel": "mobile"})
    assert a != b, "a newly added parameter is not reflected in the cache key"


@pytest.mark.rubric("key_generalises")
def test_key_distinguishes_different_parameter_names():
    from analytics.keys import build_cache_key
    assert build_cache_key("report", {"alpha": 1}) != build_cache_key("report", {"beta": 1})


@pytest.mark.rubric("key_generalises")
def test_key_is_independent_of_dict_ordering():
    from analytics.keys import build_cache_key
    a = build_cache_key("report", {"alpha": 1, "beta": 2})
    b = build_cache_key("report", {"beta": 2, "alpha": 1})
    assert a == b


@pytest.mark.rubric("key_generalises")
def test_key_distinguishes_report_names():
    from analytics.keys import build_cache_key
    params = {"start": "x", "end": "y"}
    assert build_cache_key("revenue_report", params) != build_cache_key("cost_report", params)


@pytest.mark.rubric("key_generalises")
def test_key_reflects_region():
    from analytics.keys import build_cache_key
    base = {"start": "x", "end": "y", "metric": "revenue"}
    a = build_cache_key("revenue_report", dict(base, region="north"))
    b = build_cache_key("revenue_report", dict(base, region="south"))
    assert a != b


# --- constraints_respected --------------------------------------------------

@pytest.mark.rubric("constraints_respected")
def test_public_signature_unchanged():
    module = _reports()
    signature = inspect.signature(module.revenue_report)
    assert list(signature.parameters) == ["start", "end", "metric", "region"]
    assert signature.parameters["metric"].default == "revenue"
    assert signature.parameters["region"].default is None


@pytest.mark.rubric("constraints_respected")
def test_repository_tests_not_weakened():
    source = _read(REPO_TESTS)
    for fragment in (
        "def test_revenue_report_is_region_scoped",
        'assert south["total"] == 1050.0',
        "def test_repeated_query_is_served_from_cache",
        "assert CACHE.misses == 1",
        "def test_unscoped_report_totals_all_regions",
    ):
        assert fragment in source, "repository test was removed or weakened: {}".format(fragment)


@pytest.mark.rubric("constraints_respected")
def test_no_skip_markers_added_to_repository_tests():
    source = _read(REPO_TESTS)
    for banned in ("skip", "xfail"):
        assert banned not in source, "repository tests appear to be skipped"


@pytest.mark.rubric("constraints_respected")
def test_no_third_party_dependencies_introduced():
    for path in (REPORTS_SRC, KEYS_SRC, "/app/analytics/cache.py"):
        source = _read(path)
        for banned in ("import pandas", "import numpy", "import requests", "import redis", "import cachetools"):
            assert banned not in source, "{} introduced {}".format(path, banned)
