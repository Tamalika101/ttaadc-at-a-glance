"""Section 2: drinking water. Which villages are in the TTAADC area, and how many homes have a tap.

Area of each JJM village (official LGD lists):
  council  - LGD links the village to no Gram Panchayat: it is wholly under TTAADC village councils
  split    - LGD links it to Gram Panchayat(s), but JJM also lists a TTAADC village council in it
  outside  - only Gram Panchayats
JJM reports one total per village, so a split village cannot be divided between the two areas.
"""
import pandas as pd

from . import config as C, reference as R


def classify(villages: pd.DataFrame) -> pd.DataFrame:
    vc = R.load_council_bodies()
    gp_keys = set(R.load_gram_panchayats()["key"])
    vc_by_key = vc.groupby("key")["zone"].agg(lambda z: sorted(set(z.dropna())))
    with_gp = R.villages_with_gram_panchayat()

    def per_village(row):
        names = [n.strip() for n in str(row.panchayats).split(",") if n.strip()]
        keys = [R.norm(n) for n in names]
        council_only = [k for k in keys if k in vc_by_key.index and k not in gp_keys]
        both = [k for k in keys if k in vc_by_key.index and k in gp_keys]
        gp_only = [k for k in keys if k in gp_keys and k not in vc_by_key.index]
        code = row.get("lgd_village_code") if hasattr(row, "get") else row.lgd_village_code
        if not code or (isinstance(code, float)):
            # older snapshots sometimes lack the LGD code: decide from local body names alone
            area = "council" if council_only and not gp_only else ("split" if council_only else "outside")
            vc_keys = council_only + (both if area == "council" else [])
        elif code not in with_gp:
            area = "council"
            vc_keys = council_only + both
        elif council_only:
            area = "split"
            vc_keys = council_only
        else:
            area = "outside"
            vc_keys = []
        zones = sorted({z for k in vc_keys for z in vc_by_key.get(k, [])})
        # a name shared by councils in two zones: keep the zone named like the JJM block
        if len(zones) > 1:
            block = R.norm(row.block)
            same = [z for z in zones if R.norm(z) == block]
            zones = same or zones
        return pd.Series({"area": area, "zone": zones[0] if len(zones) == 1 else (" / ".join(zones) or None),
                          "council_bodies": len(vc_keys)})

    out = villages.join(villages.apply(per_village, axis=1))
    out["coverage"] = out["hh_connections"] / out["households"].where(out["households"] > 0)
    out["without_tap"] = (out["households"] - out["hh_connections"]).clip(lower=0)
    return out


def _agg(df):
    hh, conn = int(df["households"].sum()), int(df["hh_connections"].sum())
    return {"villages": int(len(df)), "households": hh, "connections": conn,
            "without_tap": hh - conn, "coverage": round(conn / hh, 4) if hh else None,
            "villages_100": int((df["coverage"] >= 1).sum()),
            "villages_below_50": int((df["coverage"] < 0.5).sum())}


def summarise(v: pd.DataFrame, meta: dict) -> dict:
    by_area = {a: _agg(g) for a, g in v.groupby("area")}
    council = v[v["area"] == "council"]

    zones = []
    for z, g in council.dropna(subset=["zone"]).groupby("zone"):
        if " / " in z:
            continue
        zones.append({"zone": z, "district": g["district"].mode().iat[0], **_agg(g)})
    zones.sort(key=lambda r: r["coverage"])

    districts = []
    for d, g in v.groupby("district"):
        row = {"district": d}
        for a in ["council", "outside"]:
            sub = g[g["area"] == a]
            row[a] = round(sub["hh_connections"].sum() / sub["households"].sum(), 4) if len(sub) else None
        districts.append(row)

    clean = lambda z: None if pd.isna(z) else z
    ranked = council[council["households"] >= C.MIN_HOUSEHOLDS_FOR_RANKING].sort_values("coverage")
    behind = [{"village": r.village, "zone": clean(r.zone), "district": r.district, "block": r.block,
               "households": int(r.households), "connections": int(r.hh_connections),
               "coverage": round(float(r.coverage), 4)} for r in ranked.head(15).itertuples()]

    bins = [0, .25, .5, .75, .9, .9999, 1.01]
    labels = ["Under 25%", "25–50%", "50–75%", "75–90%", "90–99%", "100%"]
    dist = {}
    for a in ["council", "outside"]:
        cut = pd.cut(v.loc[v["area"] == a, "coverage"], bins=bins, labels=labels, right=False)
        dist[a] = [int(x) for x in cut.value_counts().reindex(labels).fillna(0)]

    return {
        "reported_till": meta.get("reported_till"), "fetched_at": meta.get("fetched_at"),
        "financial_year": meta.get("financial_year"),
        "by_area": by_area, "zones": zones, "districts": districts,
        "furthest_behind": behind, "distribution": {"bins": labels, **dist},
        "unassigned_council_villages": int(council["zone"].isna().sum()),
    }


def villages_table(v: pd.DataFrame) -> list:
    """Compact per-village rows for the site's search box."""
    keep = v[v["area"] != "outside"]
    return [{"v": r.village, "z": None if pd.isna(r.zone) else r.zone, "d": r.district, "b": r.block, "a": r.area,
             "h": int(r.households), "c": int(r.hh_connections)} for r in keep.itertuples()]


def history(snapshots: dict, current: pd.DataFrame, current_label: str) -> dict:
    """Coverage by area for each financial-year snapshot, plus the current figures."""
    series = []
    for fy, rows in sorted(snapshots.items()):
        if not rows:
            continue
        v = classify(pd.DataFrame(rows))
        a = {k: _agg(g) for k, g in v.groupby("area")}
        series.append({"label": f"FY {fy}", "council": a.get("council"), "outside": a.get("outside"),
                       "no_lgd_code": int(v["lgd_village_code"].isna().sum())})
    a = {k: _agg(g) for k, g in current.groupby("area")}
    series.append({"label": current_label, "council": a.get("council"), "outside": a.get("outside"), "no_lgd_code": 0})

    zones_change = []
    first = next((fy for fy, rows in sorted(snapshots.items()) if rows), None)
    if first:
        v0 = classify(pd.DataFrame(snapshots[first]))
        c0 = v0[v0["area"] == "council"].dropna(subset=["zone"])
        c1 = current[current["area"] == "council"].dropna(subset=["zone"])
        g0 = c0.groupby("zone")[["households", "hh_connections"]].sum()
        g1 = c1.groupby("zone")[["households", "hh_connections"]].sum()
        for z in g1.index.intersection(g0.index):
            if " / " in z:
                continue
            before = g0.loc[z, "hh_connections"] / g0.loc[z, "households"]
            after = g1.loc[z, "hh_connections"] / g1.loc[z, "households"]
            zones_change.append({"zone": z, "before": round(float(before), 4), "after": round(float(after), 4),
                                 "connections_added": int(g1.loc[z, "hh_connections"] - g0.loc[z, "hh_connections"])})
        zones_change.sort(key=lambda r: r["after"] - r["before"])
    return {"series": series, "first_snapshot": first, "zones_change": zones_change}
