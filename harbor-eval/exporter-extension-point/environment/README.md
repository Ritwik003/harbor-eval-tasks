# export pipeline

Records in, a rendered document out.

- `pipeline/cli.py` — command line entry point. Dispatches through the
  registry; it does not know which formats exist and must not need to change
  when one is added.
- `pipeline/exporters/registry.py` — the `Exporter` base class and the
  `register` / `get_exporter` / `available_formats` plumbing.
- `pipeline/exporters/csv_exporter.py`, `json_exporter.py` — the formats.

Run the suite with:

    cd /app && python -m pytest tests
