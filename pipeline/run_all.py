"""Build every JSON file the website reads.

Run:  python -m pipeline.run_all            (uses data/raw/jjm_tripura_villages.json)
      python -m pipeline.run_all --fetch    (download fresh water data first)
"""
import argparse
import datetime as dt
import json

import pandas as pd

from . import config as C, election, geo, schools, water


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
    hist_file = (raw_file.parent if raw_file else C.RAW) / "jjm_tripura_history.json"
    if hist_file.exists():
        snaps = json.loads(hist_file.read_text())
        write("water_history", water.history(snaps, v, f"Now ({blob.get('reported_till')})"))

    print("Map and schools")
    layer = geo.village_layer(v)
    write("map_villages", layer)
    sch_file = (raw_file.parent if raw_file else C.RAW) / "schools_tripura.json"
    if sch_file.exists():
        placed = geo.place_schools(json.loads(sch_file.read_text()), layer)
        write("schools", schools.summarise(placed))
        write("school_points", schools.points(placed))

    write("meta", {"built_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"),
                   "water_reported_till": blob.get("reported_till")})
    print("Done.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    if ap.parse_args().fetch:
        from . import fetch_jjm, fetch_schools
        fetch_jjm.main()
        fetch_schools.main()
    main()
