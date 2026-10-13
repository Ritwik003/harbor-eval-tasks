from pipeline.exporters import available_formats, get_exporter

ROWS = [
    {"id": 1, "name": "Asha", "score": 91},
    {"id": 2, "name": "Bilal", "score": None},
]
COLUMNS = ["id", "name", "score"]


def test_csv_export():
    output = get_exporter("csv").export(ROWS, COLUMNS)
    assert output == "id,name,score\n1,Asha,91\n2,Bilal,\n"


def test_json_export_round_trips():
    import json
    output = get_exporter("json").export(ROWS, COLUMNS)
    assert json.loads(output) == ROWS


def test_registry_lists_formats():
    assert "csv" in available_formats()
    assert "json" in available_formats()
