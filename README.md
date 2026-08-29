# Disruption Rights

**Modern AI Pro · Level 2 · Track C · Project C5**

An agent that takes a flight disruption and the US DOT rules corpus and returns a verdict:
what the passenger is entitled to, **what they are not**, and the section that says so.

The `not_entitled` list is the point. Most passenger-rights tools only ever say yes, because
saying yes reads as helpful and nobody grades it. This one is graded on saying no correctly.

---

## Status

| | |
|---|---|
| Golden set | `golden/golden.jsonl` — frozen before the system produced anything |
| Candidates | `golden/candidates-shilpi.jsonl` — extra cases offered into the merge, not scored |
| Corpus | 30 CFR sections, downloaded by script — see `corpus/MANIFEST.md` |
| Harness | `eval.py` — runs the cases, prints the score |
| Agent | in progress |

---

## Run it

```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env        # then put your key in .env
python corpus/fetch_corpus.py --with-superseded

python eval.py --list       # what's in the golden set
python eval.py              # run every case and score it
```

---

## A case

```json
{"case_id": "C01",
 "question": "My domestic flight was cancelled for weather and I rejected rebooking. What am I owed?",
 "expected": {
   "entitled_to":  ["Refund to the original form of payment"],
   "not_entitled": ["Automatic additional cash compensation"],
   "cite":         [{"source": "...", "section": "...", "url": "..."}],
   "why":          "Cancellation reason does not remove the refund right when the passenger declines alternatives."}}
```

`type`, `fixture` and `agent` are optional. The harness uses them when a case has them and
ignores them when it doesn't.

## What the agent returns

```python
def answer(case: dict) -> dict:
    return {
        "entitled_to":  [...],
        "not_entitled": [...],
        "cite":         [{"source": ..., "section": ..., "url": ...}],
        "tool_calls":   [{"name": "search_rules", "args": {...}}],
        "needs_human":  False,
        "confidence":   0.8,
    }
```

Two lookups — flight status, and the rules corpus — then one grounded model call. If the
sources don't support a view, say so and keep `confidence` at or below 0.5.

---

## Layout

```
golden/golden.jsonl               the frozen cases
golden/candidates-shilpi.jsonl    extra candidates, not scored
corpus/MANIFEST.md                what the corpus is and why
corpus/fetch_corpus.py            downloads 30 CFR sections from eCFR
corpus/md/                        the downloaded documents (not committed)
eval.py                           the harness
FACTCHECK.md                      regulation figures verified against eCFR
PROJECT.md                        the build plan
```

---

## The rule

The golden set was committed **before** the system produced anything. From that commit,
questions and expected answers change only by a reviewed commit with a stated reason.

Cases written after you see the output grade whatever you already built.

---

## Corpus

Real US federal aviation regulation, downloaded from ecfr.gov — 14 CFR Parts 250, 254, 259 and
260. Not the practice corpora supplied with the course. Every file carries the date and version
it was fetched at, which is what makes the superseded-version cases scoreable at all.

Regulation figures were verified on 25 August 2026 — see `FACTCHECK.md`, which lists each one
with a link so anyone can re-check it in a couple of minutes.
