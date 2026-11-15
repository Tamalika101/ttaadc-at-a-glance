"""Markdown summary of the latest build (shown on the GitHub Actions run page)."""
import json

from . import config as C

w = json.loads((C.OUT / "water.json").read_text())
c, o = w["by_area"]["council"], w["by_area"]["outside"]
print("### Build summary")
print(f"- Water data reported till: {w['reported_till']}")
print(f"- Council villages: {c['villages']}, tap coverage {c['coverage']:.1%} ({c['without_tap']:,} homes without a tap)")
print(f"- Villages outside the council: {o['villages']}, tap coverage {o['coverage']:.1%}")
