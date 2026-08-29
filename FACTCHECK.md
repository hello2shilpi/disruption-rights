# Verified figures

Every number below was read from the actual regulation text on **ecfr.gov**, on **25 August
2026**. Use these to check any case in the golden set — a case whose expected answer
contradicts one of these is wrong.

| Figure | What it is | Section | Check it |
|---|---|---|---|
| **$1,075 / $2,150** | Bumping compensation caps — 200% band and 400% band. A **ceiling**, not the payout. | 14 CFR 250.5 | [open](https://www.ecfr.gov/current/title-14/chapter-II/subchapter-A/part-250/section-250.5) · search `2,150` |
| **$4,700** | Baggage liability minimum per passenger. A **floor on liability**, not a payment — you prove your loss. | 14 CFR 254.4 | [open](https://www.ecfr.gov/current/title-14/chapter-II/subchapter-A/part-254/section-254.4) · search `4,700` |
| **3 hours** | Tarmac: they must let you off. Also the domestic delay that triggers a refund right. | 14 CFR 259.4 · 260.2 | [open](https://www.ecfr.gov/current/title-14/chapter-II/subchapter-A/part-259/section-259.4) · search `three hours` |
| **2 hours** | Tarmac: food and water due, whether or not you're let off. | 14 CFR 259.4 | same page · search `two hours` |
| **6 hours** | International delay that triggers a refund right. Measured on **arrival**, not departure. | 14 CFR 260.2 | [open](https://www.ecfr.gov/current/title-14/chapter-II/subchapter-A/part-260/section-260.2) · search `six` |
| **7 business days** | Refund deadline, credit card. | 14 CFR 260.2 | same page · search `business days` |
| **20 calendar days** | Refund deadline, everything else. | 14 CFR 260.2 | same page |
| **12 hours** | Domestic bag delay that counts as "significantly delayed" and refunds the bag fee. | 14 CFR 260.2 | same page |

Two of these — the § 250.5 caps and the § 254.4 limit — adjust for inflation roughly every two
years, so they are the ones most likely to have moved. `corpus/fetch_corpus.py` stamps the date
into every downloaded file, which makes a disagreement visible rather than silent. **If the
download disagrees with this page, the download is right.**

---

## Rules that decide most cases

**No US regulation pays cash for a delayed flight.** Parts 250, 254, 259 and 260 were each
searched. Every monetary remedy in US law is one of three things: a refund, denied boarding
compensation for an oversale, or a baggage claim. The €600 figure people have heard of is EU
Regulation 261/2004 and does not reach a US domestic itinerary.

**Accepting the rebooking ends the refund right.** § 260.6 gives a refund only where the
passenger *declines* the delayed or changed flight. Someone who flew has nothing left to
decline.

**Meals and hotels are not in the CFR at all.** They are commitments individual airlines
published under their customer service plans. § 259.5(b)(14) requires a carrier only to
*identify* what it offers — it mandates nothing. A case that says "DOT requires a hotel" is
wrong.

**The tarmac rule pays nothing.** § 259.4 is a service and deplaning obligation enforced by
DOT. No money flows to the passenger. This is the most common over-promise in the domain.

**A citation has to say the thing.** § 260.10 looks like the home of the refund deadlines but
says only "promptly" — both numbers live in the § 260.2 definition of *prompt refund*. A right
answer with the wrong section attached is still a failed case, because the retrieval step can
never find what isn't there.

---

## Not verified

- **The superseded editions.** eCFR's historical URLs were not reachable. Check the two files
  `fetch_corpus.py --with-superseded` writes before trusting any case that turns on the older
  dollar figures.
- **EU 261/2004.** Not fetched. Uncontroversial that it doesn't reach a US domestic flight, but
  unchecked against the text.
- **Airline contracts of carriage.** Not chosen yet, so nothing to check.
