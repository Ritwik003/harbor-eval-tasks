# Harbor evaluation tasks

Three [Harbor](https://github.com/anomalyco/harbor) benchmark tasks measuring
distinct software-engineering capabilities in coding agents, with the design
record and measured baselines for each.

Every task here is a **benchmark task, not a coding exercise**. The difference
is that each one has several ways to make the visible failing test pass and
only one of them is correct. The scoring separates them.

---

## The tasks

| Task | Capability measured | Baseline | Oracle | MiniMax-M2.7 |
| --- | --- | --- | --- | --- |
| [`report-cache-scoping`](harbor-eval/report-cache-scoping/) | Root cause analysis across module boundaries under a preservation constraint | 0.52 | 1.00 | **1.000** (3/3 criteria met) |
| [`exporter-extension-point`](harbor-eval/exporter-extension-point/) | Repository comprehension and implementation planning under an architectural constraint | 0.38 | 1.00 | **1.000** (3/3 criteria met) |
| [`legacy-record-upgrade`](harbor-eval/legacy-record-upgrade/) | Backward-compatibility reasoning during a data format migration | 0.44 | 1.00 | **0.802** (0/3 criteria met) |

*Baseline* = the hidden rubric suite scored against the untouched starting
repository. *Oracle* = the reference solution in `solution/solve.sh`. Model
figures are means over three attempts, run through OpenCode.

### 1. `report-cache-scoping`

Revenue reports are cached, and the cache fingerprints each query from a
hardcoded list of three parameter names. Region filtering was added later but
never added to that list, so two regions collide on one fingerprint and the
second manager silently receives the first region's revenue.

The tempting wrong fix is to add `"region"` to the list. It turns the test
green and leaves the same trap armed for the next parameter — scoring 0.91 on
accuracy but only 0.60 on `key_generalises`.

### 2. `exporter-extension-point`

An export service where each format is a self-registering plugin and the CLI
dispatches generically by name. The agent must add a TSV exporter, with correct
escaping for values containing tabs, newlines or backslashes, without
modifying `cli.py`.

The tempting wrong fix is an `if fmt == "tsv"` branch in the CLI. The output is
byte-perfect and it scores at the floor, because the capability under test is
finding the right place, not producing the right bytes.

### 3. `legacy-record-upgrade`

A record store holds two formats side by side; legacy records predate the
`schema_version` field entirely. Version detection guesses from the payload
instead of reading that field, so a new record saved without a timestamp is
misread as legacy.

The tempting wrong fix is "read `schema_version`, default an absent one to the
latest schema". That passes the whole visible suite while routing every legacy
record — which by definition has no version field — through the new-format
parser, destroying its tags and timestamps. `backward_compatible` drops to
0.00 while `symptom_fixed` reads 1.00.

---

## Repository layout

```
harbor-eval/
  <task-name>/
    task.toml              metadata, timeouts, resources
    instruction.md         the only thing the agent sees
    environment/           built into a Docker image, becomes /app
      Dockerfile
      <package>/           the service under test
      tests/               visible suite; exactly one failing test
      POLICY.md            spec document (legacy-record-upgrade only)
    tests/                 HIDDEN — copied to /tests at verify time only
      test_rubric.py       rubric-marked assertions
      conftest.py          turns outcomes into per-criterion rewards
      test.sh              verifier entrypoint
    solution/solve.sh      reference fix; must score exactly 1.0

EVALUATION-DESIGN.md       design record: objective, anatomy, shortcut
                           mapping, measured numbers, honest limitations
RUNBOOK.md                 how to run and how to read the output
task-summary.csv           one row per task for reporting
```

The agent never sees `tests/` or `solution/`. It gets `instruction.md` and the
container.

---

## Running them

Requires Docker and Python 3.11+.

```bash
python -m venv .venv
.venv/Scripts/activate          # Windows;  source .venv/bin/activate on Unix
pip install harbor

cp .env.example .env            # then add your API key
```

**Always run the oracle first.** If it does not report `accuracy = 1.0` and
`all_criteria_met = 1.0`, the task is broken, not the model:

```bash
harbor run -p ./harbor-eval -a oracle
```

Then the model. Three attempts minimum — one agentic run is noise:

```bash
harbor run -p ./harbor-eval -a opencode -m minimax/MiniMax-M2.7 --env-file .env -k 3
```

---

## Reading the results

The headline accuracy is the least interesting number. Each task emits one
score per rubric criterion to `/logs/verifier/reward.json`:

```bash
cat jobs/<timestamp>/*/verifier/reward.json
```

Read the **capability criteria**, not the guardrails:

| Task | Capability signal | Guardrail (high on an untouched repo — means little alone) |
| --- | --- | --- |
| `report-cache-scoping` | `functional_fix`, `key_generalises`, `cache_effective` | `constraints_respected`, `no_regression` |
| `exporter-extension-point` | `functional_correct`, `extension_point_used` | `constraints_respected` |
| `legacy-record-upgrade` | `symptom_fixed`, `backward_compatible`, `spec_conformance` | `constraints_respected` |

`all_criteria_met` is the strict pass rate: every criterion perfect, or zero.
`/logs/verifier/pytest.log` names the exact assertion that failed — that is the
qualitative finding.

---

## How each task was validated

No task is finished until all three pass:

1. **Baseline** — hidden suite against the untouched repo. Must score well
   below 1.0 (target under 0.5) or the task cannot discriminate.
2. **Oracle** — `solution/solve.sh`, then the hidden suite. Must be exactly 1.0
   on every criterion. If it is not, the task gets fixed — never the tests
   loosened to match.
3. **Every anticipated shortcut** — implemented for real, run against the
   hidden suite, and confirmed to score low on the criterion meant to catch it.

`legacy-record-upgrade` was validated against six failure modes, each
implemented and measured. The full table is in
[EVALUATION-DESIGN.md](EVALUATION-DESIGN.md), along with the limitations of
each task stated plainly rather than omitted.

---

## Design notes

The measured behaviour tables in [EVALUATION-DESIGN.md](EVALUATION-DESIGN.md)
are the point of this repository. A single pass/fail number would call a
superficial fix and a root-cause fix nearly identical — 0.91 against 1.00 on
task 1, 0.84 against 1.00 on task 3. Scoring four to five criteria separately
turns that into a statement about *which* requirement the model missed.

Two of the three tasks currently sit at ceiling for MiniMax-M2.7, which means
they report only that the model clears the bar. That is a finding about task
difficulty, and it is recorded as such.
