# Disruption Rights

**Modern AI Pro · Level 2 · Track C · Project C5**

An agent that takes a flight disruption and the US DOT rules corpus and returns a JSON verdict:
what the passenger is entitled to, **what they are not**, and the section that says so.

The `not_entitled` list is the point. Every passenger-rights tool over-promises, because
over-promising reads as helpful and nobody grades it. This one is graded on it.

---

## Status

| | |
|---|---|
| Golden set | **20 cases, frozen** — see `golden/golden.jsonl` |
| Corpus | 37 documents specified, 30 machine-fetchable — see `corpus/MANIFEST.md` |
| Harness | in progress — `eval.py` |
| Agent | in progress |

---

## The verdict

```json
{
  "entitled_to": [
    { "item": "Denied boarding compensation of $880",
      "basis": "400% of the $220 fare, under the $2,150 cap",
      "authority": "regulation",
      "cite": ["14 CFR 250.5(a)(3)"] }
  ],
  "not_entitled": [
    { "item": "Additional payment for the 3-hour delay itself",
      "why": "The delay is what sets the 400% band; it is not separately compensable",
      "cite": ["14 CFR 250.5(a)"] }
  ],
  "unknown": [],
  "needs_human": false,
  "confidence": 0.9
}
```

`authority` is one of `regulation` · `contract` · `guidance`. Meals and hotels for a
controllable delay are **not** in the CFR — they are promises individual airlines published.
A tool that merges the two sends a passenger to argue a rule that does not exist.

---

## Run it

```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env        # then put your key in .env
python corpus/fetch_corpus.py --with-superseded
python eval.py --summary
```

---

## Layout

```
golden/golden.jsonl      the 20 frozen test cases
corpus/MANIFEST.md       what the corpus is and why
corpus/fetch_corpus.py   downloads 30 CFR sections from eCFR
corpus/md/               the downloaded documents (not committed)
eval.py                  the harness: runs the cases, prints two scorecards
PROJECT.md               the build plan
FACTCHECK.md             the pre-freeze review against eCFR
```

---

## The rule

The golden set was written and committed **before** the system produced anything. From that
commit, `question` and `expect` change only by a reviewed commit with a stated reason.

Cases written after you see the output grade whatever you already built.

---

## Provenance

The 20 cases were drafted with Claude, then re-checked against the eCFR text on 25 August
2026. **Six were wrong and were corrected**, one was added, two adjusted — `FACTCHECK.md` has
the record. Three claims remain unverified and are marked as such.

Regulations are real and current as of that date. Flight numbers are invented.
