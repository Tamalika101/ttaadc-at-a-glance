"""Load the Local Government Directory (LGD) lists for Tripura (see data/reference/README.md)."""
import re

import pandas as pd

from . import config as C


def norm(name: str) -> str:
    """Comparable form of a local body name: lowercase letters only."""
    return re.sub(r"[^a-z]", "", str(name).lower())


def load_council_bodies() -> pd.DataFrame:
    """TTAADC village councils with their Block Advisory Committee (the council's zones)."""
    t = pd.read_csv(C.REF / "lgd_tlbSpecificState.csv", skiprows=3, dtype=str)
    t.columns = ["sno", "code", "version", "name", "name_local", "type_code", "type", "parent_code"]
    t = t.dropna(subset=["code"])
    t["type"] = t["type"].str.strip()
    bac = t[t["type"] == "Block Advisory Committee"][["code", "name"]]
    bac = bac.assign(zone=bac["name"].str.replace(r"\s*Bac$", "", regex=True).str.strip())
    vc = t[t["type"] == "Village Council"][["code", "name", "parent_code"]].copy()
    vc = vc.merge(bac[["code", "zone"]].rename(columns={"code": "parent_code"}), on="parent_code", how="left")
    vc["key"] = vc["name"].map(norm)
    return vc


def load_gram_panchayats() -> pd.DataFrame:
    p = pd.read_csv(C.REF / "lgd_priLbSpecificState.csv", skiprows=3, dtype=str).iloc[1:]
    p.columns = ["sno", "type_code", "type", "code", "version", "name", "name_local", "parent_code"]
    p = p[p["type"].str.strip() == "Gram Panchayat"].copy()
    p["key"] = p["name"].map(norm)
    return p


def villages_with_gram_panchayat() -> set:
    """LGD village codes linked to at least one Gram Panchayat (i.e. not wholly under the council)."""
    m = pd.read_csv(C.REF / "lgd_villageGramPanchayatMapping.csv", skiprows=4, dtype=str).iloc[1:]
    m.columns = [c.strip() for c in m.columns]
    return set(m.loc[m["Local Body Code"].notna(), "Village Code"])


def all_villages() -> pd.DataFrame:
    v = pd.read_csv(C.REF / "lgd_villageofSpecificState.csv", skiprows=3, dtype=str).iloc[1:]
    v = v.iloc[:, [1, 2, 3, 4, 5, 7]]
    v.columns = ["district_code", "district", "subdistrict_code", "subdistrict", "village_code", "village"]
    return v.dropna(subset=["village_code"])
