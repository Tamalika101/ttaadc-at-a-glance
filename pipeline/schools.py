"""Schools in the council area vs elsewhere (UDISE records, around 2021-22)."""
import pandas as pd


def summarise(df: pd.DataFrame) -> dict:
    d = df[(df["status"] == "Operational") & (df["location_type"] == "Rural")].copy()
    for c in ["total_teachers", "class_students"]:
        d[c] = pd.to_numeric(d.get(c), errors="coerce").fillna(0)
    gov = d["management"].fillna("").str.contains("Department of Education|Tribal|Local body|Govt|Government", case=False)
    d["govt"] = gov

    def agg(g):
        n = len(g)
        stud, teach = g["class_students"].sum(), g["total_teachers"].sum()
        return {"schools": int(n), "students": int(stud), "teachers": int(teach),
                "pupils_per_teacher": round(stud / teach, 1) if teach else None,
                "single_teacher_share": round(float((g["total_teachers"] == 1).mean()), 3) if n else None,
                "no_teacher": int((g["total_teachers"] == 0).sum()),
                "govt_share": round(float(g["govt"].mean()), 3) if n else None,
                "secondary_share": round(float(g["school_category"].fillna("").str.contains("Secondary").mean()), 3) if n else None}

    by_area = {a: agg(g) for a, g in d.groupby("area") if a in ("council", "outside", "split")}
    zones = [{"zone": z, **agg(g)} for z, g in d[d["area"] == "council"].dropna(subset=["zone"]).groupby("zone")
             if " / " not in z and len(g) >= 10]
    zones.sort(key=lambda r: -(r["single_teacher_share"] or 0))
    return {"by_area": by_area, "zones": zones, "unplaced": int((df["area"] == "unplaced").sum()),
            "note": "UDISE school records via India Data Portal (years covered up to 2021)."}


def points(df: pd.DataFrame) -> list:
    d = df[df["status"] == "Operational"]
    return [[round(float(r.longitude), 5), round(float(r.latitude), 5), r.school_name.title(), r.school_category,
             int(pd.to_numeric(r.total_teachers, errors="coerce") or 0),
             int(pd.to_numeric(r.class_students, errors="coerce") or 0), r.area]
            for r in d.itertuples() if r.area in ("council", "split")]
