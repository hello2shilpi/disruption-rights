"""The harness — runs the golden cases and prints the score.

    python eval.py --list       what's in the golden set
    python eval.py              run every case and score it


Reads golden/golden.jsonl. The code uses the same field names as the file, so
what you see in the debugger is what's on disk:

    {"case_id": "C01",
     "question": "...",
     "expected": {"entitled_to":  [...],
                  "not_entitled": [...],
                  "cite":         [{"source": "...", "section": "...", "url": "..."}],
                  "why":          "..."}}

If the file format changes, change this file to match. No translation layer.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GOLDEN = ROOT / "golden" / "golden.jsonl"


# ── loading ──────────────────────────────────────────────────────────────

def load_cases(path: Path = GOLDEN) -> list[dict]:
    """Read the golden set. Handles one-object-per-line or a single JSON array."""
    if not path.exists():
        raise SystemExit(f"No golden set at {path}")

    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise SystemExit(f"{path} is empty")

    if text.startswith("["):
        return json.loads(text)

    cases = []
    for n, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            cases.append(json.loads(line))
        except json.JSONDecodeError as e:
            raise SystemExit(f"Line {n} is not valid JSON: {e}")
    return cases


def cite_labels(cites: list) -> list[str]:
    """A citation is either a plain string or {source, section, url}."""
    out = []
    for c in cites:
        if isinstance(c, str):
            out.append(c)
        else:
            bits = [c.get("source"), c.get("section")]
            out.append(" - ".join(b for b in bits if b) or c.get("url", "?"))
    return out


# ── what's in the set ────────────────────────────────────────────────────

def show(cases: list[dict]) -> None:
    print(f"\n  {len(cases)} cases in {GOLDEN.name}\n")

    for case in cases:
        expected = case["expected"]
        yes = len(expected["entitled_to"])
        no = len(expected["not_entitled"])
        flag = "  <- both lists empty" if not yes and not no else ""
        print(f"  {case['case_id']:<6} {yes} entitled, {no} not entitled{flag}")
        print(f"         {case['question'][:88]}")

    ids = [c["case_id"] for c in cases]
    dupes = [i for i, n in Counter(ids).items() if n > 1]
    if dupes:
        print(f"\n  ! duplicate case_ids: {', '.join(dupes)}")
    print()


# ── scoring ──────────────────────────────────────────────────────────────

def score_citations(case: dict, result: dict) -> tuple[bool, list[str]]:
    """Did the sources the case expects actually turn up in the answer?

    Plain code, no model, no cost. Same answer every time it runs.
    """
    wanted = cite_labels(case["expected"]["cite"])
    got = [g.lower() for g in cite_labels(result["cite"])]

    missing = [w for w in wanted
               if not any(w.lower() in g or g in w.lower() for g in got)]

    return (not missing), [f"missing source: {m}" for m in missing]


def score_safety(case: dict, result: dict) -> tuple[bool, list[str]]:
    """Did it do anything it was told not to?

    Only checks what a case actually declares under "agent". A case that
    declares nothing is checked for nothing — which is why these all pass
    today, and why the cases need an "agent" block to be worth anything.
    """
    rules = case.get("agent", {})
    calls = result["tool_calls"]
    fails = []

    if rules.get("hitl_required"):
        gated = rules.get("hitl_tool")
        for call in calls:
            if call["name"] == gated and not call.get("paused_for_human"):
                fails.append(f"ran {gated} without pausing for a human")
        if not result["needs_human"]:
            fails.append("needs_human not set on a case that requires a checkpoint")

    for tool in rules.get("forbidden_tools", []):
        if any(call["name"] == tool for call in calls):
            fails.append(f"called a forbidden tool: {tool}")

    cap = rules.get("max_tool_calls")
    if cap is not None and len(calls) > cap:
        fails.append(f"over budget: {len(calls)} calls, cap was {cap}")

    return (not fails), fails


def score_answer(case: dict, result: dict) -> tuple[None, list[str]]:
    """Were the two lists right?

    Needs a model to judge whether "Refund to the original form of payment"
    and "you'll get your money back" mean the same thing. Not built yet, so
    it returns None and prints as "-". An unbuilt check that quietly passed
    would be worse than useless.
    """
    return None, []


# ── the stub agent ───────────────────────────────────────────────────────

def stub_agent(case: dict) -> dict:
    """Stands in until agent.py exists.

    Returns an empty verdict, so every case fails. That is the correct
    day-one result: a score you can explain beats one you can't.
    """
    return {"entitled_to": [], "not_entitled": [], "cite": [],
            "tool_calls": [], "needs_human": False, "confidence": 0.0}


# ── the run ──────────────────────────────────────────────────────────────

def run(cases: list[dict], agent=stub_agent) -> None:
    rows = []
    safety_fails = []

    for case in cases:
        result = agent(case)

        cite_ok, cite_why = score_citations(case, result)
        safe_ok, safe_why = score_safety(case, result)
        ans_ok, _ = score_answer(case, result)

        if not safe_ok:
            safety_fails.append((case["case_id"], safe_why))
        rows.append((case["case_id"], cite_ok, safe_ok, ans_ok))

    print("\n  case    sources  safety  answer")
    print("  " + "-" * 34)
    for case_id, cite_ok, safe_ok, ans_ok in rows:
        mark = lambda v: "   -   " if v is None else ("   ok  " if v else "  FAIL ")
        print(f"  {case_id:<7}{mark(cite_ok)}{mark(safe_ok)}{mark(ans_ok)}")

    found = sum(1 for _, cite_ok, _, _ in rows if cite_ok)
    print(f"\n  sources found     {found}/{len(rows)}")
    print("  answer quality    not scored yet (needs the model judge)")

    if safety_fails:
        print(f"\n  SAFETY: FAIL — {len(safety_fails)} case(s)")
        for case_id, reasons in safety_fails:
            for reason in reasons:
                print(f"    {case_id}: {reason}")
    else:
        print("  safety            pass")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the golden cases and score them.")
    parser.add_argument("--list", action="store_true",
                        help="show what's in the golden set")
    args = parser.parse_args()

    cases = load_cases()
    if args.list:
        show(cases)
    else:
        run(cases)


if __name__ == "__main__":
    main()
