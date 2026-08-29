# Corpus

Real US federal aviation regulation, downloaded from **ecfr.gov**. Not Meridian, not Aventro —
the course practice corpora everyone else is using.

```bash
python corpus/fetch_corpus.py --with-superseded
```

Run it from your own machine. It writes one markdown file per CFR section into `corpus/md/`,
which is gitignored — the script is what's committed, not its output. Anyone who clones the
repo runs it and gets the same corpus, dated.

---

## What the script downloads — 31 documents

| Part | What it governs | Docs |
|---|---|---|
| **14 CFR 250** | Oversales and denied boarding. The only place in US law with a compensation *formula* — and § 250.6, the exceptions that switch it off. | 10 |
| **14 CFR 254** | Baggage liability limit. | 1 |
| **14 CFR 259** | Tarmac delays, customer service plans, notifications. Service obligations with **no money attached** — the clearest source of "you're not owed anything" findings in the corpus. | 7 |
| **14 CFR 260** | The 2024 automatic refund rule. Definitions in § 260.2, the obligation in § 260.6 — deliberately far apart. | 11 |
| **superseded** | § 250.5 and § 254.4 as they stood on 2024-01-01, before the October 2024 inflation adjustment. Different dollar figures, near-identical prose. | 2 |

Every file carries front-matter:

```yaml
doc_id: 14CFR-250.5.md
cite: 14 CFR 250.5
jurisdiction: US-DOT
as_of: 2026-08-25
version: current          # or: superseded
source_url: https://www.ecfr.gov/current/title-14/...
```

**`version` and `as_of` are the point.** Two editions of § 250.5 read almost identically — only
the numbers move. Similarity search cannot separate them; a metadata filter at query time can.
That's what makes the old-version cases scoreable rather than decorative.

---

## To add by hand — 7 more

Public, but not fetchable through one API.

**Three airline contracts of carriage and customer service plans.** Every covered carrier must
post them (§ 259.6), so they're always findable. These matter more than the count suggests:
**meals and hotels for a controllable delay are not in the CFR at all.** They are promises
individual airlines published. A system that can't tell "the law requires" from "this airline
promised" gives confident advice that evaporates at the gate. Tag them `authority: contract`.

**Two DOT guidance documents** — the airline customer service dashboard, and *Fly Rights*. Tag
them `authority: guidance`. They state things that are true and appear nowhere in the CFR, like
keeping your original ticket when you're bumped. Guidance is persuasive, not binding, and a
verdict resting on it should say so.

**EU 261/2004, Articles 5–9.** Tag `jurisdiction: EU`. In the corpus specifically so the agent
can be wrong about it — it's where the €250/€400/€600 figures live, and misapplying them to a
US flight is the single most common passenger belief. Without it, a case testing that is
trivial. With it, retrieval surfaces it on any question mentioning three hours, and the
jurisdiction filter has to do real work.

That's three authority tiers: `regulation` · `contract` · `guidance`. Collapsing them is how a
citation stops meaning anything.

---

## Why this corpus scores well

A corpus worth grading has four traps in it naturally. This one does:

- **Exact figures** — `$1,075`, `$2,150`, `$4,700`, 7 *business* days vs 20 *calendar* days,
  3 hours vs 6. Embeddings blur these; only keyword search nails them.
- **Cross-references** — § 260.10 says "promptly" and the deadline lives back in § 260.2.
  § 250.5 grants compensation and § 250.6 takes it away, then returns something smaller.
- **Two live versions of the same rule** — § 250.5 and § 254.4, both public, different numbers.
- **Things it must refuse** — a third party's booking details, or help misstating facts to a
  federal agency.

---

## Left out on purpose

**More than ~38 documents.** Ingestion isn't the project. This is enough for chunking to
actually split and for citation scoring to be earned.

**State law and small-claims material.** Pulls the agent toward legal advice, which is a refusal
class, not a capability.

**Canada and the UK.** Two jurisdictions already prove the filter works. A third is more
ingestion for no new failure mode.

---

## Check before freezing

Two figures adjust for inflation every couple of years and are the most likely to have moved —
the § 250.5 caps and the § 254.4 limit. `FACTCHECK.md` lists what they were on 25 August 2026,
with links. **If the download disagrees, the download is right.**

Also unverified: the two superseded files (fetch them and read them), and the EU261 text.
