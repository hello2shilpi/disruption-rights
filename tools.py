"""Bounded, auditable tools used by the disruption-rights agent."""

from __future__ import annotations

import json
import math
import os
import re
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
CORPUS = ROOT / "corpus" / "md"
SAFE_FLIGHT_FIELDS = {
    "flight", "flight_number", "origin", "dest", "destination", "market",
    "status", "cancelled", "delay_min", "arrival_delay_min", "tarmac_delay_min",
    "deplaned", "denied_boarding", "oversold", "fare_paid_usd",
    "rebooked_arrival_delta_min", "accepted_rebooking", "reason",
    "refund_requested_on", "payment_method", "days_elapsed",
}
FLIGHT_ALIASES = {
    "destination": "dest",
    "arrival_delay_minutes": "arrival_delay_min",
    "tarmac_delay_minutes": "tarmac_delay_min",
}
TOKEN = re.compile(r"[a-z0-9]+(?:[.$-][a-z0-9]+)*", re.I)


def _tokens(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


def _frontmatter(text: str) -> tuple[dict[str, str], str]:
    meta: dict[str, str] = {}
    if not text.startswith("---\n"):
        return meta, text
    _, raw, body = text.split("---", 2)
    for line in raw.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip('"')
    return meta, body.strip()


def _documents() -> list[dict[str, Any]]:
    paths = sorted(CORPUS.glob("*.md")) if CORPUS.exists() else []
    # These checked project notes keep the app usable before corpus download.
    paths += [ROOT / "FACTCHECK.md", ROOT / "corpus" / "MANIFEST.md"]
    docs = []
    for path in paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        meta, body = _frontmatter(text)
        docs.append({"path": path, "id": meta.get("doc_id", path.name),
                     "meta": meta, "text": body})
    return docs


def search_rules(query: str, *, as_of: str | None = None,
                 jurisdiction: str = "US-DOT", limit: int = 5) -> list[dict[str, Any]]:
    """Hybrid lexical retrieval with version and jurisdiction filtering."""
    docs = _documents()
    filtered = []
    for doc in docs:
        meta = doc["meta"]
        if meta.get("jurisdiction") and meta["jurisdiction"] != jurisdiction:
            continue
        if as_of and meta.get("as_of") and meta["as_of"] > as_of:
            continue
        filtered.append(doc)
    if not filtered:
        return []

    query_terms = _tokens(query)
    document_frequency = Counter()
    tokenized = []
    for doc in filtered:
        terms = _tokens(doc["text"] + " " + doc["id"])
        tokenized.append(terms)
        document_frequency.update(set(terms))

    scored = []
    for doc, terms in zip(filtered, tokenized):
        counts = Counter(terms)
        score = 0.0
        for term in query_terms:
            if counts[term]:
                score += (1 + math.log(counts[term])) * math.log(
                    1 + len(filtered) / document_frequency[term]
                )
        # Exact strings (amounts, section numbers, durations) deserve extra weight.
        lowered = doc["text"].lower()
        score += sum(2.0 for t in set(query_terms) if any(c.isdigit() for c in t) and t in lowered)
        if score:
            meta = doc["meta"]
            scored.append({
                "doc_id": doc["id"], "score": round(score, 4),
                "cite": meta.get("cite", doc["id"]),
                "section": meta.get("cite", doc["id"]),
                "url": meta.get("source_url", ""),
                "as_of": meta.get("as_of"), "version": meta.get("version", "current"),
                "text": doc["text"][:5000],
            })
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[: max(1, min(limit, 10))]


def _sanitize_flight(data: dict[str, Any]) -> dict[str, Any]:
    """Drop free-form/vendor fields and passenger identifiers."""
    normalized = dict(data)
    for source, target in FLIGHT_ALIASES.items():
        if source in normalized and target not in normalized:
            normalized[target] = normalized.pop(source)
    return {key: value for key, value in normalized.items() if key in SAFE_FLIGHT_FIELDS}


def lookup_flight_status(case: dict[str, Any], *, live: bool = False) -> dict[str, Any]:
    """Use a recorded fixture by default; Aviationstack is explicit live mode only."""
    fixture = case.get("fixture")
    if isinstance(fixture, dict):
        value = fixture.get("flight_status", fixture)
        return _sanitize_flight(value) if isinstance(value, dict) else {"found": False}
    if not live:
        return {"found": False, "reason": "No recorded flight-status fixture"}
    key = os.getenv("AVIATIONSTACK_API_KEY")
    flight = case.get("flight") or case.get("flight_number")
    if not key or not flight:
        return {"found": False, "reason": "Live lookup requires flight number and AVIATIONSTACK_API_KEY"}
    query = urllib.parse.urlencode({"access_key": key, "flight_iata": flight, "limit": 1})
    with urllib.request.urlopen("https://api.aviationstack.com/v1/flights?" + query, timeout=10) as response:
        payload = json.load(response)
    rows = payload.get("data") or []
    if not rows:
        return {"found": False}
    row = rows[0]
    return _sanitize_flight({
        "flight": flight, "status": row.get("flight_status"),
        "origin": (row.get("departure") or {}).get("iata"),
        "dest": (row.get("arrival") or {}).get("iata"),
        "delay_min": (row.get("arrival") or {}).get("delay"),
    })


def file_dot_complaint(_: dict[str, Any]) -> dict[str, Any]:
    return {"paused_for_human": True, "executed": False,
            "message": "Human approval is required before filing a DOT complaint."}


def submit_refund_request(_: dict[str, Any]) -> dict[str, Any]:
    return {"paused_for_human": True, "executed": False,
            "message": "Human approval is required before submitting a refund request."}
