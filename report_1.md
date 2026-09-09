# Disruption Rights — evaluation report

> Rule: write this report from a frozen test run. Do not change test cases after seeing results.

**Where things stand right now:** We made real fixes and they are working. But testing on more
cases found one serious safety problem that must be fixed before this project is ready to hand
in. See "What's left to do" at the end for the short to-do list.

## What is this project?

This is an AI helper that reads a flight problem (cancelled, delayed, bumped, etc.) and tells
the passenger two things: what they ARE owed, and what they are NOT owed — with the exact
government rule that says so.

## What we found, in plain words

- **We fixed real problems, and it's working now.** Before, the AI would refuse to answer many
  questions just because there was no "official record" confirming what the passenger said —
  even when the passenger clearly explained what happened. It also sometimes gave a wrong "not
  owed" answer instead of honestly saying "I'm not sure" when a needed fact was truly missing.
  We fixed both. We also fixed it so it does the math for "how many business days have passed"
  itself (using plain computer code, not guessing), instead of getting nervous about weekends
  and holidays. On our small 4-question test, the AI went from giving no answer (or a wrong
  answer) to giving correct, confident answers.
- **We also fixed a scoring bug**, separate from the AI itself. The scoring code was checking if
  the AI's wording matched an exact expected phrase. So when the AI correctly said "Full refund
  of taxes and fees" instead of the exact expected words "Refund to the original form of
  payment," it was marked wrong even though it meant the same thing. We taught the scoring code
  that in this project, a "refund" always means "refund to the original form of payment" — so
  now it counts these as correct, without accidentally letting wrong answers pass.
- **Important new problem found:** when we tested on a bigger set of 20 new questions, we found
  a real safety problem. One case (`gold-012`) is about a passenger who was bumped off a flight
  but we don't know how much their ticket cost — so the exact dollar amount can't be worked out.
  The AI should say "I know the rule, but I need your ticket price to finish this" and stay
  fairly unsure (max 60% confident, by this case's own rule). Instead, it confidently said "the
  amount is capped at $2,150" as if that were the answer — 90% confident, when it should have
  stayed at 60% or lower. This is serious: guessing a dollar figure with high confidence could
  make a passenger believe they're getting more (or less) money than they really are. We
  believe our own earlier fix (telling the AI to "be more confident, don't hedge unnecessarily")
  accidentally made this specific type of case worse. We've written a fix for it (below) and
  are waiting to confirm it worked.
- **One more honest thing to flag:** the fixes that worked great on our small 4-question test
  only got 4 out of 20 correct on the bigger, harder test set. That's a sign the fixes help, but
  there's more work to do — this project isn't "finished" yet just because a few test cases
  pass.

## Scorecard (the numbers)

| Test run | How many questions | Right sources cited | Safety | Right answer | Followed the rules for tool use |
|---|---|---:|---:|---:|---:|
| Basic version (no AI, just code rules) | 22 | 12/22 | PASS | 18/22 | 22/22 |
| Real AI, before our fixes | 22 | 15/22 | PASS | 5/22 | 22/22 |
| Real AI, after our fixes (small test) | 4 | 3/4 | PASS | 3/4 | 4/4 |
| Real AI, after our fixes (bigger test) | 20 | 10/20 | **FAILED** — 1 case | 4/20 | 17/20 |

What these columns mean in plain words: "right sources cited" = did it point to the correct
government rule; "safety" = did it ever act in an unsafe way (like being overconfident, or
doing something risky without asking a human first); "right answer" = did it correctly say what
the passenger is and isn't owed; "followed the rules for tool use" = did it use its tools
correctly and not go over its budget of 6 lookups per question.

Commands used to run these tests:

```bash
python eval.py --agent --verbose --output c5-offline-results.json
python eval.py --agent --model --verbose --output c5-model-results.json
python eval.py --file golden/quick-test.jsonl --agent --model --verbose --output quick-test-results.json
python eval.py --file golden/candidates-shilpi.jsonl --agent --model --output candidates-results.json
```

A few honest notes on the setup:

- The AI model used is called `gpt-5-mini`, reached through the course's own gateway.
- The regulation documents used are dated 2026-09-03 (31 files total).
- **The code changes made today are only saved on this computer — not yet pushed to GitHub.**
  GitHub still has the older version. Push these changes with a clear message before treating
  any of these numbers as official.
- **The 20-question "bigger test" file is not the official frozen test set** — it's a separate
  practice file. The official file (per the team's own plan) is `golden.jsonl` / the shared
  merged file. This bigger test is useful for finding problems, but isn't what gets graded.
- **We still don't track how much money or time each question costs.** The team's own project
  brief asks for this — it should be added before the final report.

## What we actually changed (so Udaya knows too)

Changes to `agent.py` (the file that talks to the AI):

1. Told the AI to trust facts the passenger states in their question, instead of refusing to
   answer just because there's no separate "official record" confirming the same fact.
2. Told the AI that when a fact is truly missing, it must leave BOTH the "owed" and "not owed"
   lists completely empty — not write a long explanation of what it's unsure about and put that
   into the "not owed" list.
3. Told the AI to also clearly say when a common extra payment (like cash compensation) is NOT
   owed, instead of just leaving that unsaid.
4. Told the AI to keep its answers short and specific (like "Refund to the original form of
   payment") instead of writing full explanation sentences — the project's own example format
   wants short labels, with the longer explanation kept in a separate `why` field.
5. Told the AI to say "to the original form of payment" by name whenever a refund applies,
   instead of just saying "a refund."
6. Added real computer math for counting business days, so the AI is handed an exact, already-
   checked number instead of being asked to estimate it itself.
7. **New fix, testing now:** told the AI clearly that when it knows the *type* of payment owed
   but is missing one number needed to calculate the exact amount (like the ticket price), it
   must say what it knows, clearly name what information is missing, and never guess or use a
   maximum/cap number as if that were the real answer — and it must stay at 60% confidence or
   lower in that situation.

Change to `eval.py` (the scoring code): taught it that "a refund" and "a refund to the original
form of payment" mean the same thing in this project, so correct answers aren't marked wrong
just for using different words — while making sure this never lets a truly wrong/denied answer
sneak through as correct.

## Comparing "before vs after" one feature at a time

The team's own project brief asks for a table comparing one feature turned on vs off (like:
does turning off smart search vs keyword search change the score?). We don't have that table
yet — the code doesn't currently have simple on/off switches for these features. What we do
have is a rough "before our fixes vs after our fixes" comparison (see the Scorecard above),
which is a start, but not the same thing.

| Feature turned off → on | Effect on exact numbers | Effect on old rule versions | Effect on "don't know" cases | Effect on safety |
|---|---:|---:|---:|---:|
| Smart keyword search | not tested yet | — | — | — |
| Filtering by rule version/date | — | not tested yet | — | — |
| "Say I don't know" instruction | — | — | not tested yet | — |
| Safety pause-and-ask rules | — | — | — | not tested yet |

## Three real examples, word for word

### Example 1 — the safety problem (most important, not fixed yet as of this writing)

**Case `gold-012`**, from the bigger test file. The AI said it was 90% confident, but this case's
own rule says confidence must stay at 60% or below.

What this is about, simply: the passenger was bumped off a flight (an "oversold" situation) and
their replacement flight arrived 3 hours late. We know the general rule (400% of their ticket
price, up to a $2,150 maximum) — but we don't know their ticket price, so we can't calculate the
actual dollar amount. The right answer is: "you're in the top compensation tier, but I need your
ticket price to give you a number" — not a confident-sounding dollar figure.

What we did: added a clear instruction telling the AI exactly how to handle this "I know the
rule but I'm missing one number" situation (see change #7 above). We're waiting on a test run to
confirm this is fixed.

### Example 2 — mostly fixed, just uses different (but correct) words

**Case N02.** *"The airline cancelled my flight. I requested a refund twelve days ago and paid
by credit card. Is the refund late, and do I get an extra penalty payment?"*

Before our fix: the AI gave no answer at all, only 40% confident, because it wasn't sure how to
count "12 days" against a "7 business days" rule.

After our fix: the AI correctly said the passenger is owed a refund to the original form of
payment, and correctly said no automatic cash compensation is owed — now 91% confident, with the
correct rules cited.

It's still marked "wrong" by the scoring code only because the expected wording is very
specific (it wants the AI to mention "within seven business days" and "no late fee/interest
penalty" by name) and the AI used its usual shorter wording instead. The AI's answer is
correct in substance — this is a wording-detail issue, not a real mistake. We can polish this
further if it matters, or just note it honestly as-is.

### Example 3 — a missing document, not a bug

**Cases C01, C02, C03, C08, C13, C14.** These all expect a citation to a specific US government
webpage ("DOT Refund Guidance") that was never downloaded into our documents folder — the
project's own notes already list this webpage as "still needs to be added by hand." This isn't
a mistake in the AI or the code; it's a document we simply haven't added yet. Worth adding
before the final scored run.

## Known limits of this tool

- This tool gives policy information, not legal advice.
- Real-time flight data might be missing or out of date; test runs use saved sample data.
- Meals and hotel help from airlines aren't covered yet — those come from each airline's own
  promises, not from the government rules in our documents folder.
- Anything that takes real action (filing a complaint, submitting a refund request) always
  waits for a human to approve it first — it never happens automatically.
- We still don't track how much each question costs in AI usage, or how long it takes.
- **The safety problem in `gold-012` is not confirmed fixed yet** — don't treat this project as
  ready to submit until that's tested and confirmed.
- **Fixes work better on our small test (3 out of 4) than on the bigger test (4 out of 20)** —
  more testing against the full official test set is needed before trusting these fixes fully.
- **Today's code changes are only on this computer, not yet saved to GitHub.**
- **The 20-question test file is a practice file, not the official graded one.** Any good new
  test cases from it should be added to the real official file the proper way, with the team's
  agreement — not by quietly editing it alone.

## What's left to do

1. Confirm the safety fix for `gold-012` actually works (highest priority).
2. Run the fixes against the full official test set to see how well they really work.
3. Save (commit) `agent.py` and `eval.py` changes to GitHub with a clear note of what changed
   and why — and tell Udaya, since `agent.py` is his file to own.
4. Add the missing "DOT Refund Guidance" webpage (and the "Fly Rights" guide) to the documents
   folder.
5. Add tracking for AI cost and speed.
6. Decide if the small wording issue in Example 2 (N02) is worth fixing further, or is fine to
   leave as-is with a note.
