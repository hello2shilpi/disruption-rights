"""Interactive live demo — ask a flight-disruption question, see what the
passenger is and isn't owed, in plain English instead of raw JSON.

    python demo.py              live AI (needs OPENAI_API_KEY in .env)
    python demo.py --offline    free rule-based fallback, no API key needed

Type a question, press Enter, see the answer. Type 'quit' to exit.
"""

from __future__ import annotations

import argparse

from agent import answer


def format_verdict(result: dict) -> str:
    lines: list[str] = [""]

    if result.get("entitled_to"):
        lines.append("YOU ARE ENTITLED TO:")
        lines += [f"  + {item}" for item in result["entitled_to"]]
    if result.get("not_entitled"):
        lines.append("YOU ARE NOT ENTITLED TO:")
        lines += [f"  - {item}" for item in result["not_entitled"]]
    if not result.get("entitled_to") and not result.get("not_entitled"):
        lines.append("Not enough information given to answer confidently — asking for more facts")
        lines.append("rather than guessing.")

    if result.get("cite"):
        lines.append("")
        lines.append("SOURCES:")
        for c in result["cite"]:
            lines.append(f"  {c.get('source', '?')} {c.get('section', '')} — {c.get('url', '')}")

    lines.append("")
    lines.append(f"Confidence: {result.get('confidence', 0):.0%}")
    if result.get("needs_human"):
        lines.append("This needs a human to approve before any real action is taken.")

    usage = result.get("_usage")
    if usage:
        lines.append(f"(tokens used: {usage['input_tokens']} in / {usage['output_tokens']} out)")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask the disruption-rights AI a question, live.")
    parser.add_argument("--offline", action="store_true",
                        help="use the free rule-based fallback instead of the real AI")
    args = parser.parse_args()

    print("Disruption Rights — live demo")
    print("Type a flight-disruption question and press Enter. Type 'quit' to exit.\n")

    while True:
        try:
            question = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not question:
            continue
        if question.lower() in {"quit", "exit"}:
            break

        case = {"question": question}
        try:
            result = answer(case, use_model=not args.offline)
        except Exception as exc:  # keep a live demo from dying on one bad question
            print(f"(error answering that one: {exc})\n")
            continue

        print(format_verdict(result))
        print()


if __name__ == "__main__":
    main()
