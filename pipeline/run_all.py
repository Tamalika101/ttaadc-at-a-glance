"""Build every JSON file the website reads.

Run:  python -m pipeline.run_all            (uses data/raw/jjm_tripura_villages.json)
      python -m pipeline.run_all --fetch    (download fresh water data first)
"""
import argparse
import datetime as dt
import json

import pandas as pd

from . import config as C, election, water


def write(name, obj):
    C.OUT.mkdir(parents=True, exist_ok=True)
    p = C.OUT / f"{name}.json"
    p.write_text(json.dumps(obj, separators=(",", ":"), ensure_ascii=False, default=str))
    print(f"  wrote {p.name} ({p.stat().st_size / 1e3:.0f} kB)")


def main(raw_file=None):
    print("Section 1: election")
    write("election", election.summarise())

    print("Section 2: drinking water")
    blob = json.loads((raw_file or C.RAW / "jjm_tripura_villages.json").read_text())
    v = water.classify(pd.DataFrame(blob["villages"]))
    write("water", water.summarise(v, blob))
    write("water_villages", water.villages_table(v))

    write("meta", {"built_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"),
                   "water_reported_till": blob.get("reported_till")})
    print("Done.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    if ap.parse_args().fetch:
        from . import fetch_jjm
        fetch_jjm.main()
    main()
