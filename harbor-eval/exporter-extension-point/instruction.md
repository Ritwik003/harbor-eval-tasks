The export pipeline at `/app` currently supports CSV and JSON. Add support for
a `tsv` format so that `python -m pipeline.cli --input data.json --format tsv`
works and `--list-formats` reports it.

TSV output rules:

- The first line is the column names joined by a single tab character, in the
  order given by `columns`.
- Each record follows on its own line, values in the same column order.
- A missing or `None` value renders as an empty string.
- Non-string values render via `str()`.
- Because tabs and newlines are the delimiters, values must escape them:
  a backslash becomes `\\`, a tab becomes `\t`, a newline becomes `\n`, and a
  carriage return becomes `\r` — each as those two literal characters, not the
  control character.
- Lines are joined by `\n` and the output ends with a trailing newline.

Constraints:

- Adding a format must not require changing `pipeline/cli.py`. That file
  dispatches generically and is expected to stay exactly as it is.
- Follow the pattern the existing formats use.
- Do not change the behaviour of the CSV or JSON exporters.
- Do not delete, skip, or weaken any test in `/app/tests`.
- Standard library only.

`cd /app && python -m pytest tests` must pass when you are done.
