"""Section 1: the 2026 TTAADC election (hand-compiled, see data/election/SOURCES.md)."""
import pandas as pd

from . import config as C


def summarise() -> dict:
    d = pd.read_csv(C.ELECTION / "ttaadc_2026_results.csv")
    p = pd.read_csv(C.ELECTION / "party_totals.csv")
    d["total_votes_est"] = (d["winner_votes"] / (d["winner_pct"] / 100)).round().astype(int)
    d["margin_pct"] = (d["winner_pct"] - d["runner_up_pct"]).round(2)
    total = int(p["votes"].sum())
    seats = d.to_dict(orient="records")
    close = d[d["margin_pct"] < 5].sort_values("margin_pct")
    return {
        "seats": seats,
        "parties": [dict(r, vote_share=round(r["votes"] / total, 4)) for r in p.to_dict(orient="records")],
        "summary": {
            "seats_total": int(len(d)),
            "won": d["winner_party"].value_counts().to_dict(),
            "median_margin_pct": float(d["margin_pct"].median()),
            "close_seats": [{"constituency": r.constituency, "winner_party": r.winner_party,
                             "margin": int(r.margin), "margin_pct": float(r.margin_pct)} for r in close.itertuples()],
            "landslides": int((d["winner_pct"] >= 75).sum()),
        },
        "election_date": "2026-04-12", "results_date": "2026-04-17",
        "change_2021": change_since_2021(d),
    }


def change_since_2021(d26: pd.DataFrame) -> dict:
    """Which seats changed hands between the 2021 and 2026 council elections."""
    d21 = pd.read_csv(C.ELECTION / "ttaadc_2021_winners.csv")
    s21 = pd.read_csv(C.ELECTION / "party_shares_2021.csv")
    m = d21.merge(d26[["no", "winner_party", "winner"]], on="no")
    side26 = m["winner_party"].map({"TMP": "TMP alliance", "BJP": "BJP"})
    m["changed"] = m["winner_side"] != side26
    seats = [{"no": int(r.no), "constituency": r.constituency, "won_2021": r.winner_side, "won_2026": r.winner_party,
              "changed": bool(r.changed), "note": r.note if isinstance(r.note, str) else None} for r in m.itertuples()]
    return {"seats": seats,
            "tally_2021": d21["winner_side"].value_counts().to_dict(),
            "tally_2026": d26["winner_party"].value_counts().to_dict(),
            "shares_2021": s21.to_dict(orient="records"),
            "changed_count": int(m["changed"].sum())}
