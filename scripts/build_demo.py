"""Builds docs/index.html (the GitHub Pages demo) from the tool's real output.

    python3 scripts/build_demo.py
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from run import run  # noqa: E402

REPO = "service-desk-gap-finder"

r = run()
s = r["scenario"]
payload = {"steps": s["steps"], "topics": [{"id": t["id"], "name": t["name"]} for t in s["topics"]],
           "views": r["views"], "found": r["found"], "kb_before": r["kb_before"], "kb_after": r["kb_after"],
           "rules": r["rules"]}
page = (ROOT / "docs" / "template.html").read_text().replace("/*DATA*/null", json.dumps(payload))
page = page.replace("pg2342-hub/REPO", f"pg2342-hub/{REPO}")
out = ROOT / "docs" / "index.html"
out.write_text(page)
subprocess.run([sys.executable, str(ROOT / "scripts" / "demo_chrome.py"), str(out), "--repo", REPO], check=True)
print("wrote docs/index.html", out.stat().st_size, "bytes")
