# Corpus — US airline passenger rights

**37 documents. Free, primary-source, and not Meridian or Aventro.**

Everything in Part 1 is fetched by `fetch_corpus.py`. Parts 2–4 are added by hand — the
sources are public but not machine-readable through one API.

Run it from your own machine, not from a hosted sandbox:

```bash
python corpus/fetch_corpus.py --with-superseded
```

---

## Part 1 — eCFR, machine-fetched (30 docs)

| Part | What it governs | Docs | Why it's in |
|---|---|---|---|
| **14 CFR 250** | Oversales / denied boarding | 10 | The only place in US law with a compensation *formula*. Also carries § 250.6, the exceptions list, which is where most `not_entitled` findings are grounded. |
| **14 CFR 254** | Baggage liability limit | 1 | `$4,700` per passenger — a number people reliably mistake for a payout. |
| **14 CFR 259** | Tarmac delay, customer service, notifications | 7 | Service obligations with **no money attached**. The purest `not_entitled` source in the corpus. Includes the new § 259.9 one-page passenger rights summary (91 FR 21957, 24 Apr 2026). |
| **14 CFR 260** | Automatic refunds | 10 | The 2024 refund rule. Definitions in § 260.2, obligation in § 260.6 — deliberately far apart. |
| **superseded** | 250.5 and 254.4 as of 2024-01-01 | 2 | Pre-dates the Oct 2024 inflation adjustment (89 FR 84818/84819), so the dollar figures differ. Tagged `version: superseded`. |

Every file gets YAML front-matter:

```yaml
doc_id: 14CFR-250.5.md
cite: 14 CFR 250.5
jurisdiction: US-DOT
as_of: 2026-08-25
version: current          # or: superseded
superseded: false
source_url: https://www.ecfr.gov/current/title-14/...
```

`version` and `as_of` are the point. Similarity cannot tell two editions of § 250.5 apart —
the prose is nearly identical and only the dollar figures move. A metadata filter at query
time can. That is the whole `superseded` sub-score, and it is what `gold-008` and `gold-009`
are built to detect.

## Part 2 — Airline contracts of carriage + customer service plans (3 docs, by hand)

Pick three US carriers and pull the public CoC PDF and customer service plan from each.
Every covered carrier is required to post them (14 CFR 259.6), so they are always findable.

These matter more than their document count suggests. **Meals and hotels for a controllable
delay are not in the CFR at all** — they are contractual commitments each airline made
individually. A system that cannot tell "the law requires" from "this airline promised"
produces confident advice that evaporates at the counter. `gold-005` is exactly that case.

Tag these `jurisdiction: US-DOT`, `authority: contract` — the CFR docs get
`authority: regulation`, and Part 3 gets `authority: guidance`. The verdict should carry that distinction through to the citation.

## Part 3 — DOT guidance (2 docs, by hand, `authority: guidance`)

**`dot-dashboard.md`** — DOT's own table of which carrier committed to what for controllable
delays and cancellations. The cross-check on Part 2, and the thing a passenger can actually
wave at a gate agent.

**`dot-flyrights.md`** — DOT's *Fly Rights* consumer guidance. Earns its slot because it
states things that are true and are **not in the CFR anywhere**: that you keep your original
ticket when you are bumped, and that airlines are not required to compensate you for a
domestic delay. `gold-001` cites it for the first; `gold-014` leans on the second.

This is why documents carry a third authority tier. `regulation` | `contract` | `guidance` —
and a verdict that rests on guidance must say so, because guidance is persuasive and not
binding. Collapsing the three is how a citation stops meaning anything.

## Part 4 — EU 261/2004, Articles 5–9 (2 docs, by hand, `jurisdiction: EU`)

**In the corpus specifically so the agent can be wrong about it.** EU261 is where the
€250/€400/€600 figures live, and it is the single most common thing a US passenger
misapplies to a US itinerary. `gold-014` puts a passenger in Houston asking for €600.

Without the EU documents present, that case is trivial — the agent has nothing to
hallucinate from. With them present, retrieval will surface them on any question containing
"three hours" and the jurisdiction filter has to do real work. `must_not_cite: eu261-art7.md`
is what makes the failure visible.

Source: EUR-Lex CELEX `32004R0261`. Check whether the pending reform of the delay
thresholds has been adopted before you freeze the text, and record `as_of` either way.

---

## The four traps, and where each one lives

| Trap | In this corpus | Cases |
|---|---|---|
| **exact alphanumerics** | `$1,075` / `$2,150` / `$4,700`, `7 business days` vs `20 calendar days`, `3 hours` vs `6 hours`, `12 hours` for a delayed bag | gold-001, 003, 004 |
| **cross-references** | § 260.2 defines the trigger, § 260.6 imposes the duty. § 260.10 says 'promptly' and § 260.2 holds the deadline. § 250.5 grants, § 250.6 takes away — and then gives something smaller back. | gold-003, 006, 007, 020 |
| **superseded version** | 250.5 and 254.4, two editions each, both public, near-identical prose | gold-008, 009 |
| **must refuse** | third-party PNR/passport (gold-018), falsifying a federal complaint (gold-019) | gated at 100% |

## What was deliberately left out

- **More than 37 documents.** Ingestion is not the project. 37 is enough for chunking to
  actually split and for `must_cite` to be earned rather than decorative.
- **State-level and small-claims material.** Pulls the agent toward legal advice, which is a
  refusal class, not a capability.
- **Canada APPR and UK261.** Two jurisdictions is already enough to prove the filter works.
  A third is more ingestion for no new failure mode.

## Verify before you freeze

Two figures in this manifest came from a live eCFR read on 2026-08-25 and should be
re-confirmed from the front-matter your own fetch writes, not from this file:

- the § 250.5 caps — `$1,075` / `$2,150`, most recently amended 89 FR 84818
- the § 254.4 limit — `$4,700`, most recently amended 89 FR 84819

Both adjust for CPI roughly every two years, so they are the figures most likely to have
moved. `gold-008` and `gold-009` assert them by value; if the fetch disagrees with the
manifest, **the fetch is right** and the two cases get a reviewed, reasoned commit — not a
quiet edit. That is the freeze discipline working as intended, not a problem with it.

Three things in this corpus were **not** verifiable from primary text and are carried as
known gaps — see `FACTCHECK.md`:

- the **superseded** documents' dollar figures. eCFR serves current text at the URLs
  available here; the pre-amendment editions come down only through the versioner API, which
  is what `--with-superseded` calls. Check the two files it writes before trusting
  `gold-008` and `gold-009`.
- **EU261 Articles 5–9.** Not fetched. Confirm the reform status before freezing.
- **"lost bag"** is used in § 260.5 and defined nowhere in Part 260. `gold-009` now treats a
  destroyed bag as outside that rule, which is the reading the text supports — but it is a
  reading, and it should be flagged as one in the report.
