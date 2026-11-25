"""Weeks 2 to 4: draft an answer for every pilot ticket from the knowledge base, review it, and apply the gate.

A draft is the article's steps. The simulated analyst compares it with the steps the ticket really needed:
- approved: the draft has exactly the needed steps, so it goes out with no edits
- edited: the draft is missing a step or has one that does not apply
- no draft: the topic has no article, so there is nothing to draft from

The gate: a topic resolves on its own only if at least GATE_PASS of its last GATE_WINDOW drafts were
approved with no edits, and it is not on the exclusion list (those always go to a person).
"""
from __future__ import annotations

GATE_WINDOW = 50
GATE_PASS = 48
VOLUME_BAR = 0.10  # cleared topics should carry at least 10% of all ticket volume


def review(pilot: list[dict], kb: dict) -> list[dict]:
    out = []
    for p in pilot:
        article = kb.get(p["topic"])
        if article is None:
            result, diff = "none", {"missing": p["needed_steps"], "extra": []}
        else:
            need, have = set(p["needed_steps"]), set(article)
            diff = {"missing": [s for s in p["needed_steps"] if s not in have],
                    "extra": [s for s in article if s not in need]}
            result = "approved" if need == have else "edited"
        out.append({"id": p["id"], "topic": p["topic"], "result": result, **diff})
    return out


def gate(scenario: dict, reviews: list[dict], history: list[dict]) -> dict:
    total = len(history)
    volume = {}
    for h in history:
        if h["topic"]:
            volume[h["topic"]] = volume.get(h["topic"], 0) + 1
    topics = []
    for t in scenario["topics"]:
        r = [x for x in reviews if x["topic"] == t["id"]][-GATE_WINDOW:]
        approved = sum(x["result"] == "approved" for x in r)
        if t.get("excluded"):
            verdict = "ALWAYS A PERSON"
        elif len(r) >= GATE_WINDOW and approved >= GATE_PASS:
            verdict = "AUTO-RESOLVE"
        else:
            verdict = "KEEP DRAFTING"
        topics.append({"id": t["id"], "name": t["name"], "verdict": verdict,
                       "excluded": scenario["excluded_reasons"].get(t.get("excluded", ""), None),
                       "approved": approved, "window": len(r),
                       "edited": sum(x["result"] == "edited" for x in r),
                       "no_draft": sum(x["result"] == "none" for x in r),
                       "drafts": [x["result"] for x in r],
                       "volume": volume.get(t["id"], 0), "volume_share": round(volume.get(t["id"], 0) / total, 4)})
    cleared = [t for t in topics if t["verdict"] == "AUTO-RESOLVE"]
    share = round(sum(t["volume"] for t in cleared) / total, 4)
    return {"topics": topics, "cleared": len(cleared), "cleared_share": share,
            "volume_bar": VOLUME_BAR, "meets_bar": share >= VOLUME_BAR, "total_tickets": total}


def coverage(scenario: dict, kb: dict) -> dict:
    """Share of the drafted topics whose article has exactly the steps that close the ticket."""
    named = [t for t in scenario["topics"] if not t.get("excluded")]
    ok = [t["id"] for t in named if kb.get(t["id"]) is not None and set(kb[t["id"]]) == set(t["true_steps"])]
    return {"accurate": len(ok), "of": len(named)}
