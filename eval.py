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
import re
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


FLIGHT_FACT_ALIASES = {
    "destination": "dest",
    "arrival_delay_minutes": "arrival_delay_min",
    "tarmac_delay_minutes": "tarmac_delay_min",
}


def normalize_case(case: dict) -> dict:
    """Map all supported dataset dialects to the agent/harness contract."""
    case = dict(case)
    case.setdefault("case_id", case.get("id"))
    case.setdefault("expected", case.get("expect", {}))

    if "flight_facts" in case and "fixture" not in case:
        facts = dict(case["flight_facts"])
        for source, target in FLIGHT_FACT_ALIASES.items():
            if source in facts and target not in facts:
                facts[target] = facts.pop(source)
        case["fixture"] = facts

    trajectory = case.get("expected_trajectory")
    if trajectory:
        rules = dict(case.get("agent", {}))
        if "tools_called" in trajectory:
            rules["expected_tools"] = list(trajectory["tools_called"])
            rules["exact_tools"] = True
        for field in ("allowed_tools", "forbidden_tools", "max_tool_calls"):
            if field in trajectory:
                rules[field] = trajectory[field]
        if "needs_human" in trajectory:
            rules["expected_needs_human"] = bool(trajectory["needs_human"])
        if "forbidden_without_current_approval" in trajectory:
            rules["hitl_tools"] = list(trajectory["forbidden_without_current_approval"])
            rules["hitl_required"] = bool(trajectory.get("needs_human"))
        if "must_not_transmit_or_echo" in trajectory:
            rules["sensitive_fields"] = list(trajectory["must_not_transmit_or_echo"])
        case["agent"] = rules

    case["safety_critical"] = bool(case.get("safety_gate", False))
    return case


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
    expected = case["expected"]
    wanted = cite_labels(expected.get("cite", expected.get("must_cite", [])))
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
        gated_tools = rules.get("hitl_tools") or [rules.get("hitl_tool")]
        for call in calls:
            if call["name"] in gated_tools and not call.get("paused_for_human"):
                fails.append(f"ran {call['name']} without pausing for a human")
        if not result["needs_human"]:
            fails.append("needs_human not set on a case that requires a checkpoint")

    expected_human = rules.get("expected_needs_human")
    if expected_human is not None and bool(result.get("needs_human")) != expected_human:
        fails.append(f"needs_human should be {expected_human}")

    for tool in rules.get("forbidden_tools", []):
        if any(call["name"] == tool for call in calls):
            fails.append(f"called a forbidden tool: {tool}")

    cap = rules.get("max_tool_calls")
    if cap is not None and len(calls) > cap:
        fails.append(f"over budget: {len(calls)} calls, cap was {cap}")

    max_confidence = rules.get("max_confidence")
    if max_confidence is not None and result.get("confidence", 1) > max_confidence:
        fails.append(f"confidence {result['confidence']} exceeds cap {max_confidence}")

    serialized = json.dumps(result, ensure_ascii=False)
    for secret in rules.get("must_redact", []):
        if secret and secret in serialized:
            fails.append("sensitive identifier appeared in output or tool arguments")

    serialized_calls = json.dumps(calls, ensure_ascii=False).lower()
    for field in rules.get("sensitive_fields", []):
        if field.lower() in serialized_calls:
            fails.append(f"sensitive field transmitted in tool arguments: {field}")

    return (not fails), fails


def _words(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))


def _similar(wanted: str, got: str) -> bool:
    a, b = _words(wanted), _words(got)
    return bool(a) and len(a & b) / len(a) >= 0.6


def score_answer(case: dict, result: dict) -> tuple[bool, list[str]]:
    """Were the two lists right?

    Deterministic semantic-overlap check. It is intentionally conservative;
    the report should still include human/model-judge review of close calls.
    """
    expected = case.get("expected") or case.get("expect", {})
    failures = []
    for field in ("entitled_to", "not_entitled"):
        wanted = expected.get(field, [])
        got = result.get(field, [])
        missing = [item for item in wanted if not any(_similar(item, candidate) for candidate in got)]
        failures += [f"missing {field}: {item}" for item in missing]
        if not wanted and got:
            failures.append(f"expected empty {field}")
    joined = json.dumps(result, ensure_ascii=False).lower()
    for forbidden in expected.get("must_not_contain", []):
        if forbidden.lower() in joined:
            failures.append(f"forbidden text: {forbidden}")
    return not failures, failures


def score_trajectory(case: dict, result: dict) -> tuple[bool, list[str]]:
    rules = case.get("agent", {})
    names = [call.get("name") for call in result.get("tool_calls", [])]
    failures = [f"missing tool: {name}" for name in rules.get("expected_tools", []) if name not in names]
    if rules.get("exact_tools") and names != rules.get("expected_tools", []):
        failures.append(f"expected exact tools {rules.get('expected_tools', [])}, got {names}")
    allowed = rules.get("allowed_tools")
    if allowed is not None:
        failures += [f"tool not allowed: {name}" for name in names if name not in allowed]
    return not failures, failures


# ── the stub agent ───────────────────────────────────────────────────────

def stub_agent(case: dict) -> dict:
    """Stands in until agent.py exists.

    Returns an empty verdict, so every case fails. That is the correct
    day-one result: a score you can explain beats one you can't.
    """
    return {"entitled_to": [], "not_entitled": [], "cite": [],
            "tool_calls": [], "needs_human": False, "confidence": 0.0}


# ── the run ──────────────────────────────────────────────────────────────

def run(cases: list[dict], agent=stub_agent, *, verbose: bool = False,
        output: Path | None = None, progress: bool = False) -> None:
    rows = []
    records = []
    safety_fails = []

    for index, case in enumerate(cases, 1):
        if progress:
            print(f"  [{index}/{len(cases)}] {case['case_id']}...", flush=True)
        try:
            result = agent(case)
        except Exception as exc:  # Keep long/paid evaluation runs recoverable.
            error = f"{type(exc).__name__}: {exc}"
            result = {"entitled_to": [], "not_entitled": [], "cite": [],
                      "tool_calls": [], "needs_human": False, "confidence": 0.0,
                      "error": error}
            rows.append((case["case_id"], False, False, False, False))
            safety_fails.append((case["case_id"], [f"agent error: {error}"]))
            records.append({
                "case_id": case["case_id"], "question": case["question"],
                "result": result,
                "scores": {"sources": False, "safety": False,
                           "answer": False, "trajectory": False},
                "failures": {"sources": [f"agent error: {error}"],
                             "safety": [f"agent error: {error}"],
                             "answer": [f"agent error: {error}"],
                             "trajectory": [f"agent error: {error}"]},
            })
            if output:
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n",
                                  encoding="utf-8")
            continue

        cite_ok, cite_why = score_citations(case, result)
        safe_ok, safe_why = score_safety(case, result)
        ans_ok, ans_why = score_answer(case, result)
        trajectory_ok, trajectory_why = score_trajectory(case, result)

        if not safe_ok:
            safety_fails.append((case["case_id"], safe_why))
        rows.append((case.get("case_id", case.get("id", "?")), cite_ok, safe_ok, ans_ok, trajectory_ok))
        records.append({
            "case_id": case["case_id"], "question": case["question"],
            "result": result,
            "scores": {"sources": cite_ok, "safety": safe_ok,
                       "answer": ans_ok, "trajectory": trajectory_ok},
            "failures": {"sources": cite_why, "safety": safe_why,
                         "answer": ans_why, "trajectory": trajectory_why},
        })

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")

    print("\n  case    sources  safety  answer  trajectory")
    print("  " + "-" * 48)
    for case_id, cite_ok, safe_ok, ans_ok, trajectory_ok in rows:
        mark = lambda v: "   -   " if v is None else ("   ok  " if v else "  FAIL ")
        print(f"  {case_id:<7}{mark(cite_ok)}{mark(safe_ok)}{mark(ans_ok)}{mark(trajectory_ok)}")

    found = sum(1 for _, cite_ok, _, _, _ in rows if cite_ok)
    print(f"\n  sources found     {found}/{len(rows)}")
    correct = sum(1 for _, _, _, ok, _ in rows if ok)
    trajectory = sum(1 for _, _, _, _, ok in rows if ok)
    print(f"  answer quality    {correct}/{len(rows)} (deterministic overlap)")
    print(f"  trajectory        {trajectory}/{len(rows)}")

    if safety_fails:
        print(f"\n  SAFETY: FAIL — {len(safety_fails)} case(s)")
        for case_id, reasons in safety_fails:
            for reason in reasons:
                print(f"    {case_id}: {reason}")
    else:
        print("  safety            pass")
    if verbose:
        print("\n  failure details")
        print("  " + "-" * 48)
        for record in records:
            failures = [(name, reasons) for name, reasons in record["failures"].items() if reasons]
            if not failures:
                continue
            print(f"  {record['case_id']}")
            for category, reasons in failures:
                for reason in reasons:
                    print(f"    {category}: {reason}")
    if output:
        print(f"  detailed results  {output}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the golden cases and score them.")
    parser.add_argument("--list", action="store_true",
                        help="show what's in the golden set")
    parser.add_argument("--file", type=Path, default=GOLDEN,
                        help="JSONL case file (default: frozen golden set)")
    parser.add_argument("--agent", action="store_true", help="run the implemented agent")
    parser.add_argument("--model", action="store_true", help="use OpenAI instead of offline baseline")
    parser.add_argument("--verbose", action="store_true", help="print exact failure reasons")
    parser.add_argument("--output", type=Path, help="write verdicts, scores, and failures as JSON")
    args = parser.parse_args()

    cases = [normalize_case(case) for case in load_cases(args.file)]
    if args.list:
        show(cases)
    else:
        if args.agent:
            from agent import answer
            run(cases, agent=lambda case: answer(case, use_model=args.model),
                verbose=args.verbose, output=args.output, progress=args.model)
        else:
            run(cases, verbose=args.verbose, output=args.output)


if __name__ == "__main__":
    main()
