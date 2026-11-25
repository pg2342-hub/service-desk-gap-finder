"""Generates the made-up ticket history, the pilot tickets and the knowledge base from data/scenario.json.

Everything is seeded, so the same scenario always gives the same tickets.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Store tickets are mostly closed by the outside support provider; corporate ones by the internal team.
PROVIDER_SHARE = 0.6
# When a fix is missing from the article and the provider usually does it, internal analysts
# only write it down this often (they follow the article and pass the rest to the provider).
INTERNAL_RECORDS_PROVIDER_STEP = 0.25


def load_scenario(path: Path | None = None) -> dict:
    return json.loads((path or ROOT / "data" / "scenario.json").read_text())


def _needed_steps(topic: dict, rng: random.Random) -> list[str]:
    steps = list(topic["true_steps"])
    if topic["variant_steps"] and rng.random() < topic["variant_rate"]:
        steps.append(rng.choice(topic["variant_steps"]))
    return steps


def _note(steps: list[str], lexicon: dict) -> str:
    return " ".join(lexicon[s].rstrip(".") + "." for s in steps)


def _recorded(topic: dict, steps: list[str], resolved_by: str, rng: random.Random) -> list[str]:
    """The steps the resolution note actually mentions."""
    missing = set(topic["true_steps"]) - set(topic["article_steps"] or [])
    out = []
    for s in steps:
        if (s in missing and topic.get("missing_from") == "provider" and resolved_by == "internal"
                and rng.random() >= INTERNAL_RECORDS_PROVIDER_STEP):
            continue
        out.append(s)
    return out


def generate(scenario: dict) -> dict:
    rng = random.Random(scenario["seed"])
    lex = scenario["steps"]
    topics = scenario["topics"]
    n = scenario["history_tickets"]

    history = []
    for t in topics:
        count = round(n * t["weight"])
        for _ in range(count):
            steps = _needed_steps(t, rng)
            by = "provider" if rng.random() < PROVIDER_SHARE else "internal"
            noted = _recorded(t, steps, by, rng)
            history.append({"topic": t["id"], "resolved_by": by, "note_steps": noted, "note": _note(noted, lex)})
    long_tail = round(n * scenario["long_tail_share"])
    for _ in range(long_tail):
        history.append({"topic": None, "resolved_by": "provider" if rng.random() < PROVIDER_SHARE else "internal",
                        "note_steps": [], "note": "One-off issue outside the named topics."})
    rng.shuffle(history)
    for i, h in enumerate(history, 1):
        h["id"] = f"H{i:05d}"

    pilot = []
    for t in topics:
        if t.get("excluded"):
            continue
        for k in range(scenario["pilot_tickets_per_topic"]):
            pilot.append({"id": f"P-{t['id']}-{k + 1:02d}", "topic": t["id"], "needed_steps": _needed_steps(t, rng)})

    kb = {t["id"]: t["article_steps"] for t in topics}
    return {"history": history, "pilot": pilot, "kb": kb}


def write(out_dir: Path | None = None) -> dict:
    out_dir = out_dir or ROOT / "data"
    data = generate(load_scenario())
    for name in ("history", "pilot", "kb"):
        (out_dir / f"{name}.json").write_text(json.dumps(data[name], indent=1))
    return data


if __name__ == "__main__":
    d = write()
    print(f"history {len(d['history'])} tickets, pilot {len(d['pilot'])} tickets, kb {len(d['kb'])} topics")
