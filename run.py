"""Runs the whole pilot on the made-up desk and writes reports/results.json and reports/report.md.

    python3 run.py
"""
from __future__ import annotations

import json
from pathlib import Path

from gapfinder.data import ROOT, load_scenario, write
from gapfinder.discover import ADD_AT, STALE_BELOW, discover, proposed_kb
from gapfinder.gate import GATE_PASS, GATE_WINDOW, coverage, gate, review


def run() -> dict:
    scenario = load_scenario()
    data = write()
    found = discover(data["history"], data["kb"])
    kb_after = proposed_kb(data["kb"], found)
    views = {}
    for key, kb in (("before", data["kb"]), ("after", kb_after)):
        g = gate(scenario, review(data["pilot"], kb), data["history"])
        g["coverage"] = coverage(scenario, kb)
        views[key] = g
    sources = {"provider notes": 0, "all notes": 0}
    for t in found.values():
        for m in t["missing"]:
            sources[m["lives_in"]] += 1
    return {"scenario": scenario, "found": found, "kb_before": data["kb"], "kb_after": kb_after, "views": views,
            "rules": {"gate_pass": GATE_PASS, "gate_window": GATE_WINDOW, "add_at": ADD_AT, "stale_below": STALE_BELOW},
            "gap_sources": sources}


def report(r: dict) -> str:
    lex = r["scenario"]["steps"]
    lines = ["# Service desk gap finder: results", ""]
    for key, label in (("before", "Knowledge base as it is"), ("after", "After the desk lead approves the updates")):
        v = r["views"][key]
        lines += [f"## {label}", "",
                  f"{v['cleared']} topics clear the gate ({v['cleared_share']:.1%} of all tickets; bar {v['volume_bar']:.0%}). "
                  f"Accurate articles: {v['coverage']['accurate']} of {v['coverage']['of']} drafted topics.", "",
                  "| Topic | Approved with no edits (last 50) | Edited | No draft | Share of tickets | Verdict |",
                  "|---|---|---|---|---|---|"]
        for t in v["topics"]:
            a = "n/a" if t["excluded"] else f"{t['approved']} of {t['window']}"
            lines.append(f"| {t['name']} | {a} | {t['edited']} | {t['no_draft']} | {t['volume_share']:.1%} | {t['verdict']} |")
        lines.append("")
    lines += ["## Gap list for the desk lead", ""]
    names = {t["id"]: t["name"] for t in r["scenario"]["topics"]}
    for tid, f in r["found"].items():
        for m in f["missing"]:
            lines.append(f"- {names[tid]}: add \"{lex[m['step']]}\" (in {m['share']:.0%} of notes; "
                         f"{m['provider_rate']:.0%} of provider notes, {m['internal_rate']:.0%} of internal notes)")
        for o in f["outdated"]:
            lines.append(f"- {names[tid]}: remove \"{lex[o['step']]}\" (in {o['share']:.0%} of notes)")
        if not f["has_article"] and f["missing"]:
            lines.append(f"- {names[tid]}: no article today; the steps above become a new one")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    r = run()
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports" / "results.json").write_text(json.dumps({k: v for k, v in r.items() if k != "scenario"}, indent=1))
    (ROOT / "reports" / "report.md").write_text(report(r))
    for key in ("before", "after"):
        v = r["views"][key]
        print(f"{key}: {v['cleared']} topics clear the gate, {v['cleared_share']:.1%} of tickets, "
              f"accurate articles {v['coverage']['accurate']} of {v['coverage']['of']}")
    print("wrote reports/results.json and reports/report.md")
