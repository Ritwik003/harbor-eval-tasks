"""Command line entry point for the export pipeline.

This module dispatches through the exporter registry and must not need to
change when a format is added.
"""

import argparse
import json
import sys

from .exporters import UnknownFormat, available_formats, get_exporter


def main(argv=None):
    parser = argparse.ArgumentParser(prog="export")
    parser.add_argument("--input", help="path to a JSON file containing a list of records")
    parser.add_argument("--format", default="csv")
    parser.add_argument("--columns", help="comma separated column order")
    parser.add_argument("--list-formats", action="store_true")
    args = parser.parse_args(argv)

    if args.list_formats:
        print("\n".join(available_formats()))
        return 0

    if not args.input:
        print("error: --input is required", file=sys.stderr)
        return 2

    with open(args.input, encoding="utf-8") as handle:
        rows = json.load(handle)

    columns = args.columns.split(",") if args.columns else sorted({k for row in rows for k in row})

    try:
        exporter = get_exporter(args.format)
    except UnknownFormat:
        print("error: unknown format {}".format(args.format), file=sys.stderr)
        return 2

    sys.stdout.write(exporter.export(rows, columns))
    return 0


if __name__ == "__main__":
    sys.exit(main())
