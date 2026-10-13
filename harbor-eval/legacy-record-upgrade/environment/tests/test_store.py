"""Repository test suite for the record archive."""

from archive import store


def test_legacy_record_still_loads():
    record = store.get("u-1001")
    assert record.id == "u-1001"
    assert record.name == "Ada Lovelace"


def test_current_record_loads():
    record = store.get("u-2001")
    assert record.name == "Radia Perlman"
    assert record.tags == ["network", "spanning-tree"]
    assert record.created_at == "2024-01-15T08:30:00Z"


def test_imported_record_has_no_creation_time():
    record = store.get("u-2003")
    assert record.created_at is None


def test_all_records_are_loaded():
    assert len(store.read_all()) == 6
