import csv
import io

from .registry import Exporter, register


@register("csv")
class CsvExporter(Exporter):
    def export(self, rows, columns):
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(columns)
        for row in rows:
            writer.writerow(["" if row.get(column) is None else row.get(column) for column in columns])
        return buffer.getvalue()
