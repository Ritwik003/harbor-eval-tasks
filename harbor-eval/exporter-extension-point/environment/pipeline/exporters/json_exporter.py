import json

from .registry import Exporter, register


@register("json")
class JsonExporter(Exporter):
    def export(self, rows, columns):
        payload = [{column: row.get(column) for column in columns} for row in rows]
        return json.dumps(payload, indent=2) + "\n"
