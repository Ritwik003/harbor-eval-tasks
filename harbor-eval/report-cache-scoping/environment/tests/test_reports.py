import pytest

from analytics.reports import CACHE, revenue_report


@pytest.fixture(autouse=True)
def clear_cache():
    CACHE.clear()
    yield
    CACHE.clear()


def test_unscoped_report_totals_all_regions():
    report = revenue_report("2026-01-01", "2026-01-31")
    assert report["total"] == 6250.0
    assert report["row_count"] == 5


def test_report_respects_date_range():
    report = revenue_report("2026-02-01", "2026-02-28")
    assert report["row_count"] == 3


def test_report_supports_alternate_metric():
    report = revenue_report("2026-01-01", "2026-01-31", metric="units")
    assert report["total"] == 59


def test_repeated_query_is_served_from_cache():
    revenue_report("2026-01-01", "2026-01-31")
    revenue_report("2026-01-01", "2026-01-31")
    assert CACHE.misses == 1
    assert CACHE.hits == 1


def test_revenue_report_is_region_scoped():
    north = revenue_report("2026-01-01", "2026-01-31", region="north")
    south = revenue_report("2026-01-01", "2026-01-31", region="south")

    assert north["region"] == "north"
    assert north["total"] == 3000.0

    assert south["region"] == "south"
    assert south["total"] == 1050.0
