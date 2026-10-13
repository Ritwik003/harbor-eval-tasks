# Runbook — MiniMax via OpenCode

## 1. Oracle first, always

```bash
harbor run -p ./harbor-eval/report-cache-scoping   -a oracle
harbor run -p ./harbor-eval/exporter-extension-point -a oracle
```

Both must report `accuracy = 1.0` and `all_criteria_met = 1.0`. Anything else
means the task is broken, not the model. If the Oracle fails on your build,
suspect path assumptions first: the tests hardcode `/app` and `/tests`.

## 2. Run the model

```bash
harbor agents list      # confirm the OpenCode agent id
harbor models list      # confirm the MiniMax model string

harbor run -p ./harbor-eval/report-cache-scoping \
  -a opencode -m <minimax-model-string> --n-attempts 3
```

At least 3 attempts per task. One agentic run is noise.

## 3. Read the per-criterion scores, not the headline

`/logs/verifier/reward.json` carries one score per rubric criterion.

- Task 1: `functional_fix`, `key_generalises`, `cache_effective` are the signal.
- Task 2: `functional_correct`, `extension_point_used` are the signal.
- `constraints_respected` and `no_regression` are guardrails — high on an
  untouched repo, so a high value there means nothing on its own.

`/logs/verifier/pytest.log` names the exact assertion that failed. That is your
qualitative finding.

## 4. Reporting shape

Per task: mean accuracy across attempts, `all_criteria_met` pass rate, variance,
and one sentence naming the failure mode. For example — "scored 0.91 on two of
three attempts, both times by adding `region` to the field whitelist rather than
generalising the key builder; the model fixed the symptom it was shown and did
not generalise from the stated requirement."

See EVALUATION-DESIGN.md for the design record and the measured baselines.
