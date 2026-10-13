# Evaluation design record

Four Harbor tasks
(§3.14 "Before You Start Designing" and the §3.23 Evaluation Design Checklist).

All four were validated end to end: Oracle scores 1.0, the untouched starting
state scores well below it, and each anticipated shortcut was implemented and
confirmed to be caught.

---

## Task 1 — `harbor-eval/report-cache-scoping`

### Evaluation objective (§3.15)

> Evaluate whether the agent can trace a data-correctness symptom to a
> cache-key defect in a different module, and apply a minimal general fix that
> preserves the caching behaviour the system depends on.

**Capability:** root cause analysis across module boundaries under an explicit
preservation constraint. Not "Python", not "caching" — those are the setting.

### Anatomy (§3.4)

| Element | In this task |
| --- | --- |
| Context | A small analytics service; reports are memoised because they are expensive. Cache hit/miss counters feed an ops dashboard. |
| Trigger | A `region` parameter was added to `revenue_report`. |
| Symptom | `test_revenue_report_is_region_scoped` fails: the second region queried returns the first region's figures. |
| Constraint | Cache stays in the request path and keeps counting; public signature unchanged; tests not weakened; key must stay correct for parameters added later. |
| Decision | Where is the real fault — the report layer, the filter, or the key builder? And is a whitelist entry a fix or a patch? |
| Outcome | All regions correct, cache still effective, key construction general. |

### Looking beyond the symptom (§3.3)

The symptom is in `reports.py`. The cause is in `keys.py`, which builds keys
from a hardcoded field whitelist and silently drops everything else. An agent
that only reads the failing test and the module it names will not find it.

### Shortcuts anticipated and detected (§3.5, §3.19)

| Shortcut | Detected by |
| --- | --- |
| Remove or bypass the cache | `cache_effective`: hit/miss counters must move as specified |
| Skip the cache only for region queries | `cache_effective`: 2 misses / 1 hit across an interleaved north-south-north sequence |
| Delete, skip, or weaken the failing test | `constraints_respected`: source fragments must survive; no skip/xfail markers |
| Add `"region"` to the field whitelist | `key_generalises`: keys must also separate an unanticipated parameter |

The whitelist patch is the interesting one. It turns the failing test green and
is a plausible-looking fix; the instruction states the generality requirement
explicitly so scoring it is fair rather than a gotcha.

### Multiple valid solutions (§3.20)

Nothing requires the reference implementation. Sorting and stringifying params,
hashing a frozenset of items, `repr` of a sorted tuple, or a versioned key all
pass. The rubric checks properties of the key — completeness, determinism,
order-independence — not its text.

### Measured behaviour

| Repository state | accuracy | functional_fix | key_generalises | cache_effective | all_criteria_met |
| --- | --- | --- | --- | --- | --- |
| Untouched (starting state) | 0.52 | 0.00 | 0.40 | 0.75 | 0 |
| Cache disabled to "fix" it | 0.65 | 1.00 | 0.40 | 0.00 | 0 |
| Whitelist patch (superficial) | 0.91 | 1.00 | 0.60 | 1.00 | 0 |
| Root cause fixed (Oracle) | 1.00 | 1.00 | 1.00 | 1.00 | 1 |

Four different engineering behaviours produce four distinguishable profiles.
That is the §3.10 requirement — the score alone would have called rows 3 and 4
nearly identical.

---

## Task 2 — `harbor-eval/exporter-extension-point`

### Evaluation objective (§3.15)

> Evaluate whether the agent can understand an unfamiliar repository, identify
> the correct extension point for a new feature, and implement it to a precise
> specification without disturbing the existing dispatch path.

**Capability:** repository comprehension and implementation planning under an
architectural constraint.

### Anatomy (§3.4)

| Element | In this task |
| --- | --- |
| Context | An export pipeline where formats are plugins registered with a decorator; the CLI dispatches generically. |
| Trigger | A new `tsv` format is requested. |
| Symptom | None — this is a feature task (§3.8), not a bug. |
| Constraint | `pipeline/cli.py` must not change; follow the existing pattern; CSV/JSON behaviour untouched; standard library only. |
| Decision | Where does a format belong? Registration is a two-step pattern — subclass and register, then import for side effect — visible only by reading the package. |
| Outcome | TSV renders to spec, reachable through the registry and the CLI. |

### Shortcuts anticipated and detected (§3.5, §3.19)

| Shortcut | Detected by |
| --- | --- |
| `if fmt == "tsv"` branch in the CLI | `extension_point_used`: `cli.py` is checksummed against the starting state |
| Standalone function, not an `Exporter` | `extension_point_used`: base-class check |
| Registered but never imported | `extension_point_used`: `--list-formats` subprocess check |
| Weakening the repo suite | `constraints_respected` |

### Measured behaviour

| Repository state | accuracy | functional_correct | extension_point_used | all_criteria_met |
| --- | --- | --- | --- | --- |
| Untouched | 0.38 | 0.00 | 0.25 | 0 |
| CLI special-case (works, wrong architecture) | 0.38 | 0.10 | 0.00 | 0 |
| Registered plugin (Oracle) | 1.00 | 1.00 | 1.00 | 1 |

Row 2 is the point of the task. An agent can make `--format tsv` produce byte-
correct output and still score near the floor, because the capability under
measurement is not "can it write a TSV writer".

---

## Task 3 — `harbor-eval/legacy-record-upgrade`

### Evaluation objective (§3.15)

> Evaluate whether the agent can fix a defect on a new data format path while
> preserving records written in the old format, when the cheapest fix silently
> drops or corrupts the old data.

**Capability:** backward-compatibility reasoning during a data format
migration. Not "schema versioning" — that is the setting.

### Anatomy (§3.4)

| Element | In this task |
| --- | --- |
| Context | A record archive whose store holds two formats side by side. Records written before the `schema_version` field existed were never rewritten in place. |
| Trigger | The vendor feed imported version 2 records with no creation time. |
| Symptom | `test_imported_record_has_no_creation_time` fails: `u-2003` loads with `created_at` of `1970-01-01T00:00:00Z` instead of `None`. |
| Constraint | `POLICY.md` is the spec and may not be edited; legacy records must keep loading completely; `archive/data.py` may not be rewritten; public API of `archive.store` unchanged; tests not weakened. |
| Decision | What identifies a record's version — and when the field is absent, is that an old record or a new one with a default? |
| Outcome | Both formats load to spec; the version rule matches POLICY, not the payload shape. |

### Looking beyond the symptom (§3.3)

The failing test names `archive.store`. The defect is two modules away in
`archive/versioning.py`, which sniffs the payload for a `created_at` key
instead of reading `schema_version`.

But the tracing is not what this task measures — Task 1 already does that. The
measurement here is what the agent does *after* it finds the defect.

### The trap (§3.5)

The failing record is a **version 2** record. The natural repair is "read
`schema_version`, and default an absent one to the latest schema." That turns
the failing test green and passes the whole repository suite.

It also routes every legacy record — which by definition has no
`schema_version` — through the version 2 parser. Tags stay raw strings,
timestamps vanish. The repository suite checks only `id` and `name` for legacy
records, so nothing visible objects.

The correct default is stated only in `POLICY.md` rule 2: absence of the field
is the *marker* of a version 1 record, never a reason to assume the latest.
Rule 3 forbids inferring a version from the payload shape at all. Neither rule
appears in any repository test.

### Shortcuts anticipated and detected (§3.5, §3.19)

| Shortcut | Detected by | Measured |
| --- | --- | --- |
| Default an absent `schema_version` to the latest schema | `backward_compatible`: legacy records must still upgrade completely | 0.00 |
| Delete the version 1 upgrade path outright | `backward_compatible` | 0.00 |
| Hardcode the expected value for the record named in the ticket | `symptom_fixed`: unseen synthetic v2 records with no creation time | 0.71 |
| Delete the failing repository test | `constraints_respected`: source fragments and test count | 0.60 |
| Rewrite `POLICY.md` so the spec matches the convenient behaviour | `constraints_respected`: spec fragments must survive | 0.80 |
| Backfill `archive/data.py` instead of fixing the loader | `constraints_respected`: stored records checksummed by fragment | guarded |

### Multiple valid solutions (§3.20)

Every criterion is scored through the public API — `store.load`,
`store.read_all`, `store.get` — against records the agent has never seen.
Nothing requires the reference implementation, the reference module layout, or
the reference `Record` type; a dataclass, a namedtuple or a plain class all
pass. The rubric checks properties of the loaded record, not the text of any
file.

### Measured behaviour

| Repository state | accuracy | symptom_fixed | backward_compatible | version_detection | spec_conformance | constraints | all_criteria_met |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Untouched (starting state) | 0.4375 | 0.00 | 1.00 | 0.33 | 0.29 | 1.00 | 0 |
| Failing test deleted | 0.4062 | 0.14 | 1.00 | 0.33 | 0.29 | 0.60 | 0 |
| v1 upgrade path deleted | 0.5938 | 1.00 | 0.00 | 0.56 | 0.29 | 1.00 | 0 |
| Hardcoded for the named record | 0.5938 | 0.71 | 1.00 | 0.33 | 0.29 | 1.00 | 0 |
| `POLICY.md` rewritten to match | 0.5938 | 1.00 | 0.00 | 0.67 | 0.29 | 0.80 | 0 |
| Absent version defaulted to latest | 0.6250 | 1.00 | 0.00 | 0.67 | 0.29 | 1.00 | 0 |
| Detection fixed, spec never read | 0.8438 | 1.00 | 1.00 | 1.00 | 0.29 | 1.00 | 0 |
| Root cause fixed (Oracle) | 1.0000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1 |

Seven engineering behaviours, seven distinguishable profiles. The two rows that
carry the task are the last two before the Oracle: **0.625 with
`backward_compatible` at zero** is the agent that broke every legacy record to
make one test pass, and **0.844 with `spec_conformance` at 0.29** is the agent
that fixed the real defect but never opened the spec. A single headline number
would have called both of them "nearly right".

Deleting the failing test scores **below** doing nothing, which is the intended
ordering.

---

## Task 4 — `harbor-eval/delivery-failure-diagnosis`

### Evaluation objective (§3.15)

> Evaluate whether the agent can read an execution log to distinguish the true
> root cause from a louder, more visible symptom, and fix the cause, when the
> plausible reading of the log points at the wrong component.

**Capability:** diagnosing a fault from runtime evidence rather than from
source code alone. Not "retries", not "logging" — those are the setting.

### Anatomy (§3.4)

| Element | In this task |
| --- | --- |
| Context | A courier that delivers jobs to an endpoint allowed to fail, with a retry layer and a five-attempt budget. `run.log` is the recorded output of a dispatch window that overran. |
| Trigger | A destination was switched off before the window opened. |
| Symptom | `test_disabled_destination_is_permanent` fails: job `jb-4418` finishes as `retries_exhausted (upstream_unavailable)` after five attempts, and two jobs are deferred. |
| Constraint | `POLICY.md` and `run.log` may not be edited; the retry budget is fixed at five by the scheduler contract; public API of `courier.service` unchanged; tests not weakened; deterministic, no sleeping or clock reads. |
| Decision | The log's loud lines all name the retry layer. Is the retry layer the fault, or is it faithfully executing a decision made once, quietly, before the first backoff? |
| Outcome | A permanent condition is recognised on the first attempt, whatever status carried it, and costs exactly one call. |

### Why the log is the artefact (§3.3)

Every loud entry comes from the retry layer behaving exactly as designed: five
`WARN` lines, doubling backoff, an `ERROR`, and a stack trace naming
`courier/retry.py`. The defect is a single `DEBUG` line, repeated but never
emphasised:

```
INFO  courier.transport attempt=1 destination=dst-2210 -> 503 destination_disabled
DEBUG courier.policy    status=503 -> retryable
```

The transport reported a status **and** a code. The classifier considered only
the status. The log also contains the contrast case: `dst-1002` fails `404`,
is classified `permanent`, and costs one attempt — the shape a correct
classification produces.

The failing test names `courier.service`. The defect is in `courier/policy.py`,
which the test never mentions and which reads as correct in isolation: 4xx are
permanent, 5xx and 408/429 are retryable. It is wrong only against POLICY rule
4, and only visible as wrong when the log shows a permanent code arriving on a
retryable status.

### Shortcuts anticipated and detected (§3.5, §3.19)

| Shortcut | Detected by | Measured |
| --- | --- | --- |
| Classify after the budget is spent instead of before the first retry | `attempt_efficiency`: the transport counts the calls it received | 0.33 |
| Raise the retry budget or shorten the backoff | `attempt_efficiency`, and the budget is fixed by POLICY rule 5 | 0.25 |
| Catch the exhaustion exception and report a generic permanent failure | `spec_conformance`: the two outcomes must stay distinguishable | 0.38 |
| Special-case the code named in the ticket | `root_cause_fixed`: unseen codes on unseen statuses | 0.64 |
| Delete the failing repository test | `constraints_respected`: fragments and test count | 0.67 |
| Edit `POLICY.md` or `run.log` to match the behaviour | `constraints_respected`: spec and log fragments must survive | guarded |

The first is the point of the task. It is the fix an agent reaches for after
reading the loudest lines, it turns the entire visible suite green, and it
produces the correct final outcome — while still calling a dead endpoint five
times.

### Multiple valid solutions (§3.20)

Every criterion is scored through `courier.service.deliver` against scripted
destinations the agent has never seen. Attempt counts are read from the
transport, which records the calls it actually received, so efficiency is
measured as behaviour rather than as a number the service reports about itself.
A set, a mapping, a predicate function or a rewritten classifier all pass.

### Measured behaviour

| Repository state | accuracy | root_cause_fixed | attempt_efficiency | spec_conformance | retry_intact | constraints | all_criteria_met |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Raise the budget, soften backoff | 0.4146 | 0.00 | 0.25 | 0.63 | 1.00 | 0.83 | 0 |
| Failing test deleted | 0.4146 | 0.00 | 0.33 | 0.63 | 1.00 | 0.67 | 0 |
| Untouched (starting state) | 0.4390 | 0.00 | 0.33 | 0.63 | 1.00 | 0.83 | 0 |
| Suppress the final exception | 0.5366 | 0.64 | 0.25 | 0.38 | 1.00 | 0.83 | 0 |
| Special-case the named code | 0.6585 | 0.64 | 0.42 | 0.63 | 1.00 | 1.00 | 0 |
| **Classify after the budget is spent** | **0.7805** | **0.91** | **0.33** | **1.00** | 1.00 | 1.00 | 0 |
| Root cause fixed (Oracle) | 1.0000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1 |

Seven behaviours, seven distinguishable profiles. The row that carries the task
is the second from bottom: **0.91 on correctness, 1.00 on spec conformance,
1.00 on constraints, and 0.33 on efficiency.** That is an agent that produced
the right answer the wrong way, and no single number would have said so. Two
shortcuts score *below* the untouched repository, which is the intended
ordering.

The visible suite fails exactly one test at baseline and is fully green under
both the classify-at-end and special-case shortcuts, so neither trap announces
itself.

---

## Checklist sign-off (§3.23)

| Check | Task 1 | Task 2 | Task 3 | Task 4 |
| --- | --- | --- | --- | --- |
| Primary capability clearly defined | yes | yes | yes | yes |
| Every requirement supports that capability | yes | yes | yes | yes |
| Starting state complete and reproducible | yes — pinned image, `no-network` | yes | yes — pinned image, static store | yes — pinned image, scripted transport, no clock |
| Runs without unstable external dependencies | yes — pytest baked into the image | yes | yes — pytest baked into the image | yes — no network, no sleeps, no jitter |
| Problem clearly explained, constraints stated | yes | yes | yes | yes |
| Prompt avoids revealing the solution | yes — names the symptom and the module to run, not the cause | yes — names the pattern to follow, not the files to touch | yes — names the record and the wrong value, not the detection rule | yes — names the job and the log, never suggests the retry layer is innocent |
| Successful behaviour measurable | yes | yes | yes | yes — including call counts observed at the endpoint |
| Invalid shortcuts detectable | 4 detected, each verified | 4 detected, each verified | 6 detected, 5 implemented and measured | 6 detected, 5 implemented and measured |
| Multiple valid solutions treated fairly | properties checked, not text | any registered `Exporter` subclass | scored through the public API on unseen records | scored through the public API on unseen status/code pairs |
| Rubric criteria objective and specific | 5 criteria, each independently scored | 4 criteria | 5 criteria, 32 assertions | 5 criteria, 41 assertions |
| Tested from beginning to end | Oracle 1.0, three failure modes measured | Oracle 1.0, one failure mode measured | Oracle 1.0, six failure modes measured | Oracle 1.0, six failure modes measured |

## Known limitations

- **Guardrail criteria inflate the floor.** `constraints_respected` and
  `no_regression` score high on an untouched repository because doing nothing
  violates nothing. Read `functional_fix` + `key_generalises` (task 1) and
  `functional_correct` + `extension_point_used` (task 2) as the capability
  signal, and `all_criteria_met` as the headline pass rate.
- **Trajectory signals are not captured.** Playbook §3.10 also asks which files
  were inspected and how many attempts were needed. That lives in
  `/logs/agent/` and currently needs manual reading; a trajectory-grading
  verifier using a separate verifier environment would be the next step.
- **All three tasks are single-repository and single-language.** None exercises
  cross-service reasoning.

### Task 3 specifically

- **`backward_compatible` reads 1.0 on the untouched repository.** Doing
  nothing preserves the old format perfectly. It is a *preservation* criterion,
  not a progress criterion: it carries no information until the agent has
  changed something, and it must be read next to `symptom_fixed`. The pair
  `symptom_fixed = 1.00, backward_compatible = 0.00` is the finding this task
  exists to produce.
- **`spec_conformance` does not rank the shortcuts.** Every measured failure
  mode leaves it at 0.29, because none of them opens `POLICY.md`. It separates
  "read the spec" from "did not" and nothing finer.
- **`constraints_respected` is a tamper guardrail, not a gradient.** It reads
  1.0 unless the agent edited the tests, the spec or the stored data. Any value
  below 1.0 is the signal; the magnitude means little.
- **The starting v1 path violates two POLICY rules** (tag whitespace, canonical
  `schema_version`) that are unrelated to the reported symptom. This is
  deliberate — it is what makes the spec load-bearing — but it means
  `spec_conformance` and the detection fix are not fully independent axes, and
  an agent could in principle score 1.00 on spec conformance while leaving
  detection wrong. No measured behaviour did so.
- **The trap is a known anti-pattern.** "Default an absent version field to the
  latest schema" is a mistake a strong model may simply not make, in which case
  this task will sit at ceiling and report only that the model clears the bar.
  Task difficulty has not yet been calibrated against a model that fails it.

### Task 4 specifically

- **`retry_behaviour_intact` reads 1.0 on the untouched repository**, because
  the retry layer genuinely is intact at the start. It is a preservation
  criterion: it only carries information once the agent has changed something,
  and exists to stop `attempt_efficiency` being bought by refusing to retry at
  all. Read it beside `attempt_efficiency`, never alone.
- **`constraints_respected` is a tamper guardrail, not a gradient.** It reads
  1.0 unless the tests, the spec or the log were edited. Any value below 1.0 is
  the signal; the magnitude means little.
- **The log is static, not generated by the code under test.** `run.log` is a
  shipped artefact. An agent that changes the classifier does not regenerate
  it, so the log cannot go stale mid-task, but neither can the agent verify a
  fix by re-running the recorded window. Producing the log from a fixture at
  build time would close that gap at the cost of determinism guarantees.
- **The efficiency criterion is only meaningful because the transport counts
  calls.** If a future revision lets the service report its own attempt count
  without the transport observing, that criterion becomes forgeable.
- **`spec_conformance` and `root_cause_fixed` overlap.** Both punish ignoring
  the failure code, so a fix that addresses POLICY rule 4 moves both together.
  They separate only for the suppress-the-exception behaviour, where the
  outcome is right and the outcome *taxonomy* is wrong.
- **Single service, single language, no concurrency.** The dispatch-window
  framing implies a queue and a scheduler that do not exist in the repository.
