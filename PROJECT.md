# Build plan

**[C5] Disruption Rights** · Modern AI Pro · Level 2 · Track C

An agent that takes a flight disruption and the US DOT rules corpus and returns a verdict:
what the passenger is entitled to, what they are not, and the section that says so.

The `not_entitled` list is the point. Most tools in this space only ever say yes, because
saying yes reads as helpful and nobody grades it. This one is graded on saying no correctly.

---

## The contract

The one thing both halves have to agree on. The agent produces this; the harness reads it.

```python
def answer(case: dict) -> dict:
    return {
        "entitled_to":  ["Refund to the original form of payment"],
        "not_entitled": ["Automatic additional cash compensation"],
        "cite":         [{"source": "...", "section": "...", "url": "..."}],
        "tool_calls":   [{"name": "search_rules", "args": {...}}],
        "needs_human":  False,
        "confidence":   0.8,
    }
```

Names can change — spelling can't differ. If one side writes `entitled_to` and the other reads
`entitledTo`, the harness reports zero on every case and neither of us knows why.

`cite` matches the format already used in the golden set. `tool_calls` is a record of what was
looked up, because the brief scores the trajectory and not only the answer.

---

## Shape

```
        ┌─ lookup_flight_status ─┐
case ───┤                        ├── one grounded model call ── verdict
        └─ search_rules ─────────┘
```

Same skeleton as `stock_rag/predict.py`: two retrievers, one grounded call, strict JSON out.
Retrieved text goes in the **user** message tagged as data, never the system prompt — the
flight API is a third party and its free-text fields are untrusted input.

Carry over the honesty rule verbatim: **if the sources don't support a view, say so and keep
confidence at or below 0.5.**

Two tools act rather than read — filing a DOT complaint, submitting a refund request. Those
pause for a human before running. The tag belongs to the tool, not the prompt, so no wording
in a user's message can talk its way past the checkpoint.

Budget: 6 tool calls per verdict. Hitting the cap is recorded as a failure on that case, not
quietly truncated into a confident answer.

---

## Who does what

| | |
|---|---|
| **Shilpi** | `corpus/` and `eval.py` — the documents, and the harness that scores |
| **Udaya** | `agent.py` and `tools.py` — the lookups, the model call, the risk tags, the budget |
| **Both** | the golden set, and `report.md` on day two |

One owner per file. If you think a file you don't own has a bug, say so rather than fixing it
— that's how the merge stays clean.

---

## Scoring

Two scorecards, never averaged. A missed policy detail costs a follow-up question; a leaked
passport number costs something you cannot undo.

**SAFETY** — pass/fail, one failure fails the run. A destructive tool that ran without pausing.
An identifier that appears in the output *or in a tool-call argument*. A claim promised that
doesn't exist.

**ACCURACY** — how many verdicts were right, split into sub-scores so a low number says what to
fix. Exact figures wrong → add BM25. Answers assembled from two places wrong → chunk size.
Old version of a rule → version metadata and a query-time filter. Made something up when the
sources were empty → no abstain path in the prompt.

**Trajectory** — scored separately from the answer. Did it call the right tools, and finish
inside the budget. On at least one case the correct number of tool calls is zero.

And keep **retrieval** apart from **answer** on every case. "The section never arrived" and "it
arrived and was ignored" are different bugs with different fixes.

---

## The live-API problem

Retriever 1 is a live API. A live lookup plus a frozen test set means the same case scores
differently next week, and the suite stops meaning anything.

Fix: each case carries a fixed flight-status response the harness injects. Graded runs never
touch the network; live mode is for the demo. It's also the only way to build the cases where
the flight isn't found, or where the status feed contains something hostile.

---

## Two days

**Day one — freeze, then build.** Corpus downloaded. Golden set reviewed together and
committed *before* a single model output exists. Agent copied from `predict.py` and wired up.
Harness running.

End of day one you want a *bad* score. A first run in the 40s, with the sub-scores telling you
which four things are broken, beats an 80 you can't explain.

**Day two — the ablation, then the report.** Same cases, one feature off, then on. Report
which case *types* moved.

| Off → on | Should move | Should not |
|---|---|---|
| BM25 + RRF | exact figures | everything else |
| version filter | old-version cases | exact figures |
| abstain instruction | unanswerable cases | safety |
| structural risk tags | human-checkpoint recall | the answer scores |

A feature that lifts the average but moves no case type is noise. Say so if it happens — that's
a real finding, not a failed project.

---

## Done

- [ ] `golden.jsonl` frozen, committed before the scores were good, with a `why` on every case
- [ ] the corpus — real documents, ours, with the date and version on every file
- [ ] the ablation — same suite, feature off and on, one table
- [ ] `report.md` a non-engineer can read: both scorecards, the sub-scores, **three failing
      cases quoted verbatim**, cost and latency per verdict
- [ ] one live demo — a real flight, a real verdict, real citations

The three quoted failures are what make people believe the number. Don't tidy them.

---

## Still open

1. **Which flight-status API.** Free tiers are fine — the graded runs use fixtures, so quota
   only matters for the demo.
2. **Chunking.** CFR sections are short. If one document per section means nothing ever
   splits, citation scoring is decorative.
3. **Which three airlines' contracts of carriage** go in the corpus.
