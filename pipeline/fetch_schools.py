"""Download Tripura's school list (UDISE, via India Data Portal's open datastore API).

The India Data Portal copy covers years up to 2021 ("years_covered" in its metadata), so these records describe schools
around the 2021-22 school year: the start of the 2021-26 council term. Run: python -m pipeline.fetch_schools
"""
import json

import requests

from . import config as C

API = "https://ckandev.indiadataportal.com/api/3/action/datastore_search"
RESOURCE = "457fddf1-982f-4c85-855d-5095578accc1"   # "Basic Details of Schools"
FIELDS = ["udise_school_code", "school_name", "district_name", "subdistrict_name", "village_name", "school_category",
          "management", "status", "location_type", "latitude", "longitude", "class_rooms", "total_teachers",
          "class_students", "class_with_pre_primary_students"]


def fetch():
    rows, offset = [], 0
    while True:
        r = requests.get(API, params={"resource_id": RESOURCE, "limit": 1000, "offset": offset,
                                      "filters": json.dumps({"state_name": "Tripura"}),
                                      "fields": ",".join(FIELDS)}, timeout=120)
        r.raise_for_status()
        res = r.json()["result"]
        rows += res["records"]
        offset += 1000
        if offset >= res["total"]:
            return rows


def main():
    C.RAW.mkdir(parents=True, exist_ok=True)
    rows = fetch()
    if len(rows) < 3000:
        raise RuntimeError(f"Only {len(rows)} schools fetched")
    (C.RAW / "schools_tripura.json").write_text(json.dumps(rows))
    print(f"Saved {len(rows)} schools")


if __name__ == "__main__":
    main()
