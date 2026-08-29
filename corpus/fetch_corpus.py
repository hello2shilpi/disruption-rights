"""Build the Disruption Rights corpus from eCFR.

    python corpus/fetch_corpus.py            # current editions only
    python corpus/fetch_corpus.py --with-superseded

Writes one markdown file per CFR section into corpus/md/, each with YAML
front-matter. The front-matter is not decoration: `effective_date` and
`version` are what make the superseded cases in golden.jsonl scoreable at all.
Similarity cannot tell two editions of 14 CFR 250.5 apart. Metadata can.

Source: eCFR versioner API, https://www.ecfr.gov/developers/documentation/api/v1
No key, no rate limit published - be polite anyway.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

OUT = Path(__file__).resolve().parent / "md"
API = ("https://www.ecfr.gov/api/versioner/v1/full/{date}/title-14.xml"
       "?chapter=II&subchapter=A&part={part}&section={section}")
# The versioner endpoint wants the ancestry, hence chapter/subchapter. Parts
# 250 / 254 / 259 / 260 all sit in Title 14 > Chapter II > Subchapter A.
#
# NOTE: run this from your own machine. It will not run inside a sandbox whose
# egress proxy only permits the assistant's own fetch tool - you will get
# "Tunnel connection failed: 403" on the first call and no files.

# The current corpus. One entry per document.
#   part, section, short title
CURRENT = [
    # Part 250 - Oversales. The money rule, and the exceptions that switch it off.
    ("250", "250.1",  "Definitions"),
    ("250", "250.2a", "Policy regarding denied boarding"),
    ("250", "250.2b", "Carriers to request volunteers for denied boarding"),
    ("250", "250.3",  "Boarding priority rules"),
    ("250", "250.5",  "Amount of denied boarding compensation"),
    ("250", "250.6",  "Exceptions to eligibility for denied boarding compensation"),
    ("250", "250.7",  "Transparency Improvements and Compensation Act implementation"),
    ("250", "250.8",  "Denied boarding compensation - payment"),
    ("250", "250.9",  "Written explanation of denied boarding compensation"),
    ("250", "250.11", "Public disclosure of deliberate overbooking"),
    # Part 254 - Baggage liability.
    ("254", "254.4",  "Carrier liability limit for baggage"),
    # Part 259 - Enhanced protections. Service obligations, no money attached.
    ("259", "259.3",  "Definitions"),
    ("259", "259.4",  "Contingency plan for lengthy tarmac delays"),
    ("259", "259.5",  "Customer service plan"),
    ("259", "259.6",  "Posting of contracts of carriage and plans"),
    ("259", "259.7",  "Response to consumer problems"),
    ("259", "259.8",  "Notification of delays, cancellations and diversions"),
    ("259", "259.9",  "One-page passenger rights summary"),
    # Part 260 - Refunds. The 2024 automatic refund rule.
    ("260", "260.1",  "Purpose"),
    ("260", "260.2",  "Definitions"),
    ("260", "260.3",  "Applicability"),
    ("260", "260.4",  "Refunding fees for ancillary services not provided"),
    ("260", "260.5",  "Refunding fees for significantly delayed or lost bags"),
    ("260", "260.6",  "Refunding fare for cancelled or significantly changed flights"),
    ("260", "260.7",  "Affirmative acceptance of alternative compensation"),
    ("260", "260.8",  "Disclosing material restrictions and limitations"),
    ("260", "260.9",  "Notification to consumers"),
    ("260", "260.10", "Providing prompt refunds"),
    ("260", "260.11", "Contract of carriage provisions related to refunds"),
]

# The superseded editions. Same sections, an earlier point in time, tagged.
# 2024-01-01 predates the October 2024 inflation adjustment (89 FR 84818),
# so 250.5 and 254.4 carry different dollar figures on that date.
SUPERSEDED_DATE = "2024-01-01"
SUPERSEDED = [
    ("250", "250.5", "Amount of denied boarding compensation"),
    ("254", "254.4", "Carrier liability limit for baggage"),
]


def get(url: str, tries: int = 3) -> bytes:
    """One HTTP GET, with a couple of retries on anything but a 404."""
    for attempt in range(tries):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "disruption-rights-corpus/1.0 (coursework)"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404 or attempt == tries - 1:
                raise
            time.sleep(2 ** attempt)
        except urllib.error.URLError:
            if attempt == tries - 1:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("unreachable")


def latest_issue_date() -> str:
    """Ask eCFR which date it actually has data for.

    The versioner serves a point in time, and asking for a date later than the
    most recent published issue returns 404 on every section. Today's date is
    therefore the wrong default - use the date eCFR reports.
    """
    data = json.loads(get("https://www.ecfr.gov/api/versioner/v1/titles.json"))
    for t in data.get("titles", []):
        if t.get("number") == 14:
            d = t.get("latest_issue_date") or t.get("up_to_date_as_of")
            if d:
                return d[:10]
    raise SystemExit("Could not read the latest issue date for Title 14 from eCFR.")


def fetch(date: str, part: str, section: str) -> str:
    return get(API.format(date=date, part=part, section=section)).decode("utf-8")


def to_text(xml: str) -> str:
    """eCFR section XML -> readable text, one paragraph per line."""
    root = ET.fromstring(xml)
    lines: list[str] = []
    for el in root.iter():
        if el.tag not in {"P", "HEAD", "FP"}:
            continue
        txt = "".join(el.itertext()).strip()
        txt = re.sub(r"\s+", " ", txt)
        if not txt:
            continue
        lines.append(f"## {txt}" if el.tag == "HEAD" else txt)
    return "\n\n".join(lines)


def write_doc(part: str, section: str, title: str, date: str,
              body: str, superseded: bool) -> Path:
    tag = f"@{date}" if superseded else ""
    path = OUT / f"14CFR-{section}{tag}.md"
    url = (f"https://www.ecfr.gov/current/title-14/chapter-II/subchapter-A/"
           f"part-{part}/section-{section}")
    front = "\n".join([
        "---",
        f"doc_id: 14CFR-{section}{tag}.md",
        f"cite: 14 CFR {section}",
        f"title: {title}",
        f"part: {part}",
        f"section: {section}",
        "jurisdiction: US-DOT",
        f"as_of: {date}",
        f"version: {'superseded' if superseded else 'current'}",
        f"superseded: {'true' if superseded else 'false'}",
        f"source_url: {url}",
        "---",
        "",
    ])
    path.write_text(front + f"# 14 CFR {section} - {title}\n\n" + body + "\n",
                    encoding="utf-8")
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--date", default="current",
                    help="YYYY-MM-DD point in time, or 'current' (default: ask "
                         "eCFR for its most recent issue date)")
    ap.add_argument("--with-superseded", action="store_true",
                    help=f"also fetch the {SUPERSEDED_DATE} editions of the "
                         "sections the golden set uses as version traps")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    if args.date == "current":
        date = latest_issue_date()
        print(f"eCFR's most recent issue of Title 14 is {date} - using that.\n")
    else:
        date = args.date

    jobs = [(p, s, t, date, False) for p, s, t in CURRENT]
    if args.with_superseded:
        jobs += [(p, s, t, SUPERSEDED_DATE, True) for p, s, t in SUPERSEDED]

    ok = fail = 0
    for part, section, title, when, sup in jobs:
        try:
            body = to_text(fetch(when, part, section))
            if len(body) < 120:
                print(f"  ! {section} came back nearly empty - check the parse")
            path = write_doc(part, section, title, when, body, sup)
            print(f"  ok {path.name}  ({len(body):,} chars)")
            ok += 1
        except Exception as e:                                   # noqa: BLE001
            print(f"  X  {section} @ {when}: {type(e).__name__}: {e}")
            fail += 1
        time.sleep(0.4)

    print(f"\n{ok} written, {fail} failed -> {OUT}")
    print("Still to add by hand (not machine-fetchable, see MANIFEST.md):")
    print("  - 3 airline contracts of carriage / customer service plans")
    print("  - the DOT airline customer service dashboard commitments")
    print("  - DOT Fly Rights consumer guidance (authority: guidance)")
    print("  - EU 261/2004 Arts 5-9, tagged jurisdiction: EU (wrong-jurisdiction trap)")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
