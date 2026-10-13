#!/bin/bash
# Reference solution: plug a new format into the existing registry.
# One valid path, not the only one.
set -euo pipefail

cat > /app/pipeline/exporters/tsv_exporter.py <<'PYEOF'
from .registry import Exporter, register

_ESCAPES = (("\\", "\\\\"), ("\t", "\\t"), ("\n", "\\n"), ("\r", "\\r"))


def _escape(value):
    if value is None:
        return ""
    text = value if isinstance(value, str) else str(value)
    for raw, replacement in _ESCAPES:
        text = text.replace(raw, replacement)
    return text


@register("tsv")
class TsvExporter(Exporter):
    def export(self, rows, columns):
        lines = ["\t".join(_escape(column) for column in columns)]
        for row in rows:
            lines.append("\t".join(_escape(row.get(column)) for column in columns))
        return "\n".join(lines) + "\n"
PYEOF

python - <<'PYEOF'
import pathlib
path = pathlib.Path("/app/pipeline/exporters/__init__.py")
source = path.read_text()
marker = "from . import json_exporter  # noqa: F401,E402\n"
if "tsv_exporter" not in source:
    source = source.replace(marker, marker + "from . import tsv_exporter  # noqa: F401,E402\n")
    path.write_text(source)
PYEOF

cd /app && python -m pytest tests -q
