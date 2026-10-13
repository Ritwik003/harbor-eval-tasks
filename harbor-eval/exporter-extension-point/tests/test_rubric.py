"""Hidden verifier suite.

Rubric criteria:
  functional_correct     - the TSV rendering matches the specification
  extension_point_used   - the format was added through the registry, not by
                           special-casing the dispatcher
  no_regression          - CSV and JSON behaviour and the repo suite are intact
  constraints_respected  - stated constraints are honoured
"""

import hashlib
import subprocess
import sys

import pytest

sys.path.insert(0, "/app")

CLI_SRC = "/app/pipeline/cli.py"
REPO_TESTS = "/app/tests/test_pipeline.py"

# sha256 of pipeline/cli.py as shipped in the starting state.
CLI_SHA256 = "0556026f0c7a64b47116155b7b22639523cacfcfa40d867fd4252d9a2597564d"

ROWS = [
    {"id": 1, "name": "Asha", "score": 91},
    {"id": 2, "name": "Bilal", "score": None},
]
COLUMNS = ["id", "name", "score"]


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def _tsv():
    from pipeline.exporters import get_exporter
    return get_exporter("tsv")


# --- functional_correct -----------------------------------------------------

@pytest.mark.rubric("functional_correct")
def test_basic_rendering():
    assert _tsv().export(ROWS, COLUMNS) == "id\tname\tscore\n1\tAsha\t91\n2\tBilal\t\n"


@pytest.mark.rubric("functional_correct")
def test_column_order_is_respected():
    assert _tsv().export(ROWS, ["name", "id"]) == "name\tid\nAsha\t1\nBilal\t2\n"


@pytest.mark.rubric("functional_correct")
def test_missing_key_renders_empty():
    assert _tsv().export([{"id": 1}], ["id", "absent"]) == "id\tabsent\n1\t\n"


@pytest.mark.rubric("functional_correct")
def test_tab_is_escaped():
    assert _tsv().export([{"a": "x\ty"}], ["a"]) == "a\nx\\ty\n"


@pytest.mark.rubric("functional_correct")
def test_newline_is_escaped():
    assert _tsv().export([{"a": "x\ny"}], ["a"]) == "a\nx\\ny\n"


@pytest.mark.rubric("functional_correct")
def test_carriage_return_is_escaped():
    assert _tsv().export([{"a": "x\ry"}], ["a"]) == "a\nx\\ry\n"


@pytest.mark.rubric("functional_correct")
def test_backslash_is_escaped_first():
    assert _tsv().export([{"a": "x\\ty"}], ["a"]) == "a\nx\\\\ty\n"


@pytest.mark.rubric("functional_correct")
def test_empty_row_set_still_emits_header():
    assert _tsv().export([], ["a", "b"]) == "a\tb\n"


@pytest.mark.rubric("functional_correct")
def test_non_string_values_are_stringified():
    assert _tsv().export([{"a": 3.5, "b": True}], ["a", "b"]) == "a\tb\n3.5\tTrue\n"


@pytest.mark.rubric("functional_correct")
def test_cli_emits_tsv(tmp_path):
    import json
    data = tmp_path / "data.json"
    data.write_text(json.dumps(ROWS), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "pipeline.cli", "--input", str(data),
         "--format", "tsv", "--columns", "id,name,score"],
        capture_output=True, text=True, cwd="/app", timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "id\tname\tscore\n1\tAsha\t91\n2\tBilal\t\n"


# --- extension_point_used ---------------------------------------------------

@pytest.mark.rubric("extension_point_used")
def test_dispatcher_was_not_modified():
    digest = hashlib.sha256(_read(CLI_SRC).encode("utf-8")).hexdigest()
    assert digest == CLI_SHA256, "pipeline/cli.py was modified; the format should plug into the registry"


@pytest.mark.rubric("extension_point_used")
def test_format_is_registered():
    from pipeline.exporters import available_formats
    assert "tsv" in available_formats()


@pytest.mark.rubric("extension_point_used")
def test_exporter_subclasses_the_base_class():
    from pipeline.exporters import Exporter
    assert isinstance(_tsv(), Exporter)


@pytest.mark.rubric("extension_point_used")
def test_list_formats_reports_tsv():
    result = subprocess.run(
        [sys.executable, "-m", "pipeline.cli", "--list-formats"],
        capture_output=True, text=True, cwd="/app", timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert sorted(result.stdout.split()) == ["csv", "json", "tsv"]


# --- no_regression ----------------------------------------------------------

@pytest.mark.rubric("no_regression")
def test_csv_unchanged():
    from pipeline.exporters import get_exporter
    assert get_exporter("csv").export(ROWS, COLUMNS) == "id,name,score\n1,Asha,91\n2,Bilal,\n"


@pytest.mark.rubric("no_regression")
def test_json_unchanged():
    import json
    from pipeline.exporters import get_exporter
    assert json.loads(get_exporter("json").export(ROWS, COLUMNS)) == ROWS


@pytest.mark.rubric("no_regression")
def test_unknown_format_still_raises():
    from pipeline.exporters import UnknownFormat, get_exporter
    with pytest.raises(UnknownFormat):
        get_exporter("parquet")


@pytest.mark.rubric("no_regression")
def test_repository_suite_passes():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "/app/tests", "-q", "-p", "no:cacheprovider"],
        capture_output=True, text=True, cwd="/app", timeout=180,
    )
    assert result.returncode == 0, result.stdout[-3000:]


# --- constraints_respected --------------------------------------------------

@pytest.mark.rubric("constraints_respected")
def test_repository_tests_not_weakened():
    source = _read(REPO_TESTS)
    for fragment in ("def test_csv_export", "def test_json_export_round_trips", "def test_registry_lists_formats"):
        assert fragment in source


@pytest.mark.rubric("constraints_respected")
def test_no_skip_markers_added():
    source = _read(REPO_TESTS)
    for banned in ("skip", "xfail"):
        assert banned not in source


@pytest.mark.rubric("constraints_respected")
def test_no_third_party_dependencies():
    import glob
    for path in glob.glob("/app/pipeline/**/*.py", recursive=True):
        source = _read(path)
        for banned in ("import pandas", "import numpy", "import requests", "import tabulate"):
            assert banned not in source, "{} introduced {}".format(path, banned)
