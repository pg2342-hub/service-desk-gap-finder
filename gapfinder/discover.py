"""Week 1: read the ticket history next to the knowledge base and list where they disagree.

For each topic it counts how often each step shows up in resolution notes, then compares that to the article:
- missing: a step in at least ADD_AT of the topic's notes that the article does not have
- outdated: a step in the article that shows up in fewer than STALE_BELOW of the notes
- occasional: a step outside the article seen in some notes but under ADD_AT; kept as an escalation path,
  not added to the default answer
"""
from __future__ import annotations

from collections import Counter, defaultdict

ADD_AT = 0.40
STALE_BELOW = 0.05


def discover(history: list[dict], kb: dict) -> dict:
    by_topic = defaultdict(list)
    for h in history:
        if h["topic"]:
            by_topic[h["topic"]].append(h)

    out = {}
    for topic, tickets in by_topic.items():
        total = len(tickets)
        by_source = Counter(h["resolved_by"] for h in tickets)
        seen = Counter()
        seen_by = defaultdict(Counter)
        pos = defaultdict(list)
        for h in tickets:
            for i, s in enumerate(h["note_steps"]):
                pos[s].append(i / max(1, len(h["note_steps"]) - 1))
            for s in dict.fromkeys(h["note_steps"]):
                seen[s] += 1
                seen_by[s][h["resolved_by"]] += 1
        article = kb.get(topic)
        art = set(article or [])
        missing, outdated, occasional = [], [], []
        for s, c in seen.most_common():
            share = c / total
            if s in art:
                continue
            item = {"step": s, "share": round(share, 3), "tickets": c,
                    "position": round(sum(pos[s]) / len(pos[s]), 3),
                    "provider_notes": seen_by[s]["provider"], "internal_notes": seen_by[s]["internal"],
                    "provider_rate": round(seen_by[s]["provider"] / max(1, by_source["provider"]), 3),
                    "internal_rate": round(seen_by[s]["internal"] / max(1, by_source["internal"]), 3)}
            # Where the fix lives: mostly in the provider's notes if internal analysts write it down
            # at less than half the provider's rate.
            item["lives_in"] = "provider notes" if item["internal_rate"] < 0.5 * item["provider_rate"] else "all notes"
            (missing if share >= ADD_AT else occasional).append(item)
        for s in article or []:
            share = seen[s] / total
            if share < STALE_BELOW:
                outdated.append({"step": s, "share": round(share, 3), "tickets": seen[s]})
        out[topic] = {"tickets": total, "provider_tickets": by_source["provider"], "internal_tickets": by_source["internal"], "has_article": article is not None,
                      "missing": missing, "outdated": outdated, "occasional": occasional,
                      "step_share": {s: round(c / total, 3) for s, c in seen.items()}}
    return out


def proposed_kb(kb: dict, found: dict) -> dict:
    """The knowledge base after the desk lead approves every suggested update.

    Missing steps are added in the order they most often appear, outdated steps are removed.
    """
    new = {}
    for topic, steps in kb.items():
        f = found.get(topic)
        if not f:
            new[topic] = steps
            continue
        keep = [s for s in (steps or []) if s not in {o["step"] for o in f["outdated"]}]
        add = sorted((m for m in f["missing"] if m["step"] not in keep), key=lambda m: m["position"])
        add = [m["step"] for m in add]
        new[topic] = (keep + add) or None
    return new
