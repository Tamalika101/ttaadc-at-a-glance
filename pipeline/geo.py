"""Map layers: village outlines labelled by council area, water coverage and zone; schools placed in villages."""
import json

import pandas as pd
from shapely.geometry import Point, shape
from shapely.strtree import STRtree

from . import config as C, reference as R


def load_villages():
    j = json.loads((C.REF / "tripura_villages_pc11.geojson").read_text())
    v = pd.read_csv(C.REF / "lgd_villageofSpecificState.csv", skiprows=3, dtype=str).iloc[1:]
    v = v.iloc[:, [5, 7, 11]]
    v.columns = ["lgd", "lgd_name", "c2011"]
    v = v.dropna(subset=["lgd"])
    v["c2011"] = v["c2011"].fillna("").str.zfill(6)
    by_c2011 = v[v["c2011"] != "000000"].drop_duplicates("c2011").set_index("c2011")["lgd"].to_dict()
    return j, by_c2011


def village_layer(water_villages: pd.DataFrame) -> dict:
    """GeoJSON of villages with area (council/split/outside), zone and tap coverage where known."""
    gj, by_c2011 = load_villages()
    with_gp = R.villages_with_gram_panchayat()
    w = water_villages.drop_duplicates("lgd_village_code").set_index("lgd_village_code")
    feats = []
    for f in gj["features"]:
        p = f["properties"]
        name = p.get("town_village_name", "").replace("(Part)", "").strip()
        lgd = by_c2011.get(p["pc11_town_village_id"])
        props = {"name": name}
        if lgd is None:
            props["area"] = "town or unmatched"
        elif lgd in w.index:
            r = w.loc[lgd]
            props.update({"area": r["area"], "zone": None if pd.isna(r["zone"]) else r["zone"],
                          "hh": int(r["households"]), "tap": int(r["hh_connections"]),
                          "cov": round(float(r["coverage"]), 3) if pd.notna(r["coverage"]) else None})
        else:
            props["area"] = "council" if lgd not in with_gp else "outside"
        feats.append({"type": "Feature", "properties": props, "geometry": f["geometry"]})
    return {"type": "FeatureCollection", "features": feats}


def place_schools(schools: list, layer: dict) -> pd.DataFrame:
    """Point-in-polygon: which village (and so which area) each school sits in."""
    geoms = [shape(f["geometry"]) for f in layer["features"]]
    tree = STRtree(geoms)
    areas = [f["properties"]["area"] for f in layer["features"]]
    zones = [f["properties"].get("zone") for f in layer["features"]]
    out = []
    for s in schools:
        try:
            pt = Point(float(s["longitude"]), float(s["latitude"]))
        except (TypeError, ValueError):
            continue
        hit = next((i for i in tree.query(pt) if geoms[i].contains(pt)), None)
        out.append({**s, "area": areas[hit] if hit is not None else "unplaced",
                    "zone": zones[hit] if hit is not None else None})
    return pd.DataFrame(out)
