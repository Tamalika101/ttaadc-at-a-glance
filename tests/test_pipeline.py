"""Tests for the TTAADC at a Glance pipeline (offline: no network needed)."""
import pandas as pd
from bs4 import BeautifulSoup

from pipeline import election, fetch_jjm, reference, water

SAMPLE_HTML = """<table id="tableReportTable">
<tr><th>S.No.</th><th>District</th><th>Block</th><th>Panchayat</th><th>Village id</th><th>Village</th><th>House Holds</th><th>House Connection</th></tr>
<tr><td>1</td><td>Dhalai</td><td>Ambassa</td><td>Balaram, West Balaram</td><td>383300</td><td>Balaram [Village LGD Code : 272491]</td><td>810</td><td>733</td></tr>
<tr><td>2</td><td>Dhalai</td><td>DURGACHOWMUHANI</td><td>Kachimchara, Kamalacherra</td><td>383316</td><td>Kamalachhera [Village LGD Code : 272495]</td><td>1,588</td><td>1,376</td></tr>
</table>"""


def test_parse_village_table():
    rows = fetch_jjm.parse_village_table(BeautifulSoup(SAMPLE_HTML, "html.parser"))
    assert len(rows) == 2
    assert rows[0]["lgd_village_code"] == "272491" and rows[0]["village"] == "Balaram"
    assert rows[1]["households"] == 1588 and rows[1]["block"] == "Durgachowmuhani"


def test_financial_year():
    import datetime as dt
    assert fetch_jjm.financial_year(dt.date(2026, 11, 14)) == "2026-2027"
    assert fetch_jjm.financial_year(dt.date(2027, 2, 1)) == "2026-2027"
    assert fetch_jjm.financial_year(dt.date(2027, 4, 1)) == "2027-2028"


def test_reference_lists():
    vc = reference.load_council_bodies()
    assert len(vc) == 587                      # TTAADC village councils
    assert vc["zone"].notna().mean() > 0.9     # almost all belong to a Block Advisory Committee
    assert len(reference.load_gram_panchayats()) == 607


def test_classify_areas():
    v = pd.DataFrame([
        # Kamalachhera has no Gram Panchayat in LGD -> wholly council
        {"district": "Dhalai", "block": "Ambassa", "panchayats": "Kachimchara, Kamalacherra",
         "lgd_village_code": "272495", "households": 100, "hh_connections": 50, "village": "Kamalachhera"},
        # Balaram: Gram Panchayat West Balaram plus council Balaram -> split
        {"district": "Dhalai", "block": "Ambassa", "panchayats": "Balaram, West Balaram",
         "lgd_village_code": "272491", "households": 100, "hh_connections": 90, "village": "Balaram"},
        # Mahabir: Gram Panchayat only -> outside
        {"district": "Dhalai", "block": "Durgachowmuhani", "panchayats": "Mahabir",
         "lgd_village_code": "272445", "households": 100, "hh_connections": 100, "village": "Mahabir"},
    ])
    out = water.classify(v)
    assert list(out["area"]) == ["council", "split", "outside"]
    assert out.loc[0, "zone"] == "Ambassa"
    s = water.summarise(out, {})
    assert s["by_area"]["council"]["coverage"] == 0.5


def test_election_summary():
    e = election.summarise()
    assert e["summary"]["won"] == {"TMP": 24, "BJP": 4}
    for s in e["seats"]:
        assert s["winner_votes"] - s["runner_up_votes"] == s["margin"]


def test_election_change_since_2021():
    c = election.summarise()["change_2021"]
    assert c["tally_2021"] == {"TMP alliance": 18, "BJP": 9, "Independent": 1}
    assert c["changed_count"] == 6


def test_school_summary():
    from pipeline import schools
    df = pd.DataFrame([
        {"status": "Operational", "location_type": "Rural", "management": "Department of Education", "area": "council",
         "zone": "Ambassa", "total_teachers": 1, "class_students": 20, "school_category": "Primary"},
        {"status": "Operational", "location_type": "Rural", "management": "Private", "area": "outside",
         "zone": None, "total_teachers": 10, "class_students": 200, "school_category": "Primary with Upper Primary and Secondary"},
    ])
    s = schools.summarise(df)
    assert s["by_area"]["council"]["single_teacher_share"] == 1.0
    assert s["by_area"]["outside"]["secondary_share"] == 1.0
