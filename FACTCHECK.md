# Pre-freeze fact-check

Every regulatory claim in `golden.jsonl` was checked against eCFR primary text on
**2026-08-25**, before the set was frozen. Six cases were wrong and were corrected. This file
is the record — it is what makes the freeze mean something, and it is worth keeping in the
repo for the same reason the failing cases stay in the report.

## What was wrong

| Case | Found | Fixed by |
|---|---|---|
| **gold-003** | The deadlines aren't in § 260.10. That section says only "promptly". `7 business days` / `20 calendar days` live in the **§ 260.2 definition of "Prompt refund"**. The case was unpassable on a faithful corpus. | Added `14CFR-260.2.md` to `must_cite`. |
| **gold-007** | The fare-difference refund was sourced to Part 260. But § 260.6 gives a refund only where the consumer *declines* the flight, and this passenger flew. The real hook is the proviso at the end of **§ 250.6(c)**: "a passenger seated in a section for which a lower fare is charged shall be entitled to an appropriate refund." | Re-sourced; added a third `not_entitled` item for the Part 260 refund that does *not* apply. |
| **gold-011** | Itinerary-based scope was cited to § 260.3. That section governs which *carriers* are bound; it contains no geography. Scope is in the **§ 260.2** definitions of "covered carrier" and "covered flight" — "to, from, or within the United States". | `must_cite` → `14CFR-260.2.md`; added the § 250.2 and § 259.4 scope limits as supporting facts. |
| **gold-006** | Said the international trigger was "6 hours of departure **or** arrival delay". § 260.2 keys it to **arrival**; the only departure prong covers a flight moved *earlier* than scheduled. Verdict unchanged, reasoning wrong — and the reasoning is what generalises. | Reworded. The fixture's larger, more salient 4-hour departure delay is now explicit bait. |
| **gold-001** | "Compensation is on top of your ticket" is true and is **not in the CFR**. It appears only in DOT's *Fly Rights* guidance. `must_cite` named two sections, neither of which contains it. | Added `dot-flyrights.md` to the corpus and to `must_cite`, and introduced a third authority tier. Also added the § 250.5(f) ancillary-fee refund, which *is* in the CFR. |
| **gold-009** | Claimed a bag-fee refund for a **destroyed** bag. § 260.5 covers bags that are *lost* or *significantly delayed*; "lost bag" is undefined in Part 260 and a destroyed bag is neither. | Moved to `not_entitled`, with the gap in the definitions named as the reason. |

Four smaller corrections: gold-004 gained the **12-hour** delayed-bag threshold (also in
§ 260.2, not § 260.5) and the Mishandled Baggage Report precondition; gold-001's written
statement is due "immediately after" the denied boarding, not "at the time of"; gold-001's
band wording moved to "not less than 2 hours", because the 2-hour boundary falls into the
400% band, not the 200% one.

## What the check added

**gold-020**, an award-ticket case. § 250.1 defines a **"zero fare ticket"** and § 250.5(d)
says the rules apply to it, with the fare taken as "the lowest cash, check, or credit card
payment charged for a ticket in the same class of service on that flight."

This mattered because gold-012 — no fare supplied, so stop and ask — was one detail away
from teaching the wrong lesson. On an award ticket the passenger *cannot* supply a fare and
is not required to; the rule imputes one. A system that generalises "missing fare → abstain"
passes gold-012 and fails gold-020, which is precisely the overfitting a golden set exists
to expose. gold-012's fixture is now pinned to a cash purchase so the two cases are clean.

## Confirmed against primary text

The 250.5 bands and the `$1,075` / `$2,150` caps; the § 250.6(c) downgrade carve-out; the
§ 259.4 tarmac limits (3h / 4h / 2h) **and the finding that nothing in Part 259 pays a
passenger anything**; the § 260.2 thresholds (3h domestic / 6h international arrival,
downgrade as a significant change); § 260.6's accept-and-you-forfeit structure; the
7/20-day deadlines; § 260.4 and advance seat selection as a named ancillary service; the
§ 254.4 `$4,700` limit as a floor on liability rather than a payout.

And the load-bearing negative, which was attacked directly and held: **no US regulation
requires cash compensation for a flight delay.** Parts 250, 254, 259 and 260 were each
searched. Every monetary remedy in US law is a refund, denied boarding compensation for an
oversale, or a baggage liability claim. § 259.5(b)(14) requires a carrier only to *identify*
the services it provides to mitigate inconvenience — it mandates no hotel, no meal, no
ground transport. DOT's own guidance says it plainly: "Contrary to popular belief, for
domestic itineraries airlines are not required to compensate passengers whose flights are
delayed or canceled."

That sentence is the thesis of the project, and gold-014 is built on it.

## Still unverified

- **The superseded editions.** Historical CFR text was not reachable here. Verify the two
  `@2024-01-01` files after running `fetch_corpus.py --with-superseded`.
- **EU261 Articles 5–9.** Not fetched. gold-014's claim that it doesn't reach a
  Houston–Denver itinerary is uncontroversial but unchecked against the text.
- **`coc-carrier-a.md`** in gold-005. Synthetic until you pick real carriers. The negative
  half — no federal hotel requirement — is confirmed; the positive half is whatever the
  contract you choose actually says.

---

Six wrong citations in nineteen cases, found by reading the sections rather than trusting a
summary of them. Worth saying out loud in the write-up: **the golden set was the first thing
that got graded**, and it failed. Freezing a wrong case is worse than not freezing, because
a frozen wrong case trains the system to be wrong and then certifies it.
