# Disruption Rights — evaluation report

> Fill this report from a frozen run. Do not edit cases after seeing results.

## Executive summary

The system determines US flight-disruption entitlements and, critically, remedies that are
not available. State the most important result, limitation, and safety finding here.

## Scorecards

| Scorecard | Result | Notes |
|---|---:|---|
| Safety (pass/fail) | TBD | One failure fails the run |
| Answer quality | TBD | Deterministic score plus reviewed close calls |
| Citation retrieval | TBD | Required sources present |
| Trajectory | TBD | Expected tools, forbidden tools, and call budget |

Command used:

```bash
python eval.py --file golden/candidates-shilpi.jsonl --agent --model
```

Record model, corpus `as_of`, git commit, run timestamp, total cost, median cost per verdict,
and p50/p95 latency. A scored run without these identifiers is not reproducible.

## Ablation

| Feature off → on | Exact figures | Old versions | Unanswerable | Safety |
|---|---:|---:|---:|---:|
| Hybrid lexical retrieval | TBD | — | — | — |
| Version filter | — | TBD | — | — |
| Abstain instruction | — | — | TBD | — |
| Structural risk tags | — | — | — | TBD |

## Three failures, verbatim

Quote the full question, returned verdict, expected behavior, and diagnosis for three cases.
Do not clean up the output. Label each as retrieval, reasoning, citation, or safety failure.

### Failure 1

TBD

### Failure 2

TBD

### Failure 3

TBD

## Limitations

- This tool provides policy information, not legal advice.
- Live status data may be delayed or incomplete; graded runs use recorded fixtures.
- Airline meals and hotels depend on carrier commitments not yet present in the base corpus.
- A filing or refund submission always requires explicit human approval.
