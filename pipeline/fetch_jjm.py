"""Download Tripura's village-wise tap connection data from the Jal Jeevan Mission (JJM) dashboard.

Report: Format J7, "Village wise percentage FHTC coverage" (ASP.NET WebForms pages).
Flow, as a browser does it:
  1. open the J7 page, choose the financial year and Tripura, press Show  -> district table
  2. for each district, click its "Nos. of Villages" link                -> village list (paged)
  3. choose "All Page" in the pager                                      -> every village at once

Run:  python -m pipeline.fetch_jjm
"""
import datetime as dt
import json
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

from . import config as C

S = requests.Session()
S.headers["User-Agent"] = "Mozilla/5.0 (ttaadc-at-a-glance; +https://github.com/Tamalika101/ttaadc-at-a-glance)"


def _req(method, url, **kw):
    for attempt in range(4):
        try:
            r = S.request(method, url, timeout=120, **kw)
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            if attempt == 3:
                raise
            print(f"  retry after error: {e}", file=sys.stderr)
            time.sleep(10 * (attempt + 1))


def form_fields(soup):
    """Every hidden input and the current value of every <select>, as the browser would post."""
    data = {i["name"]: i.get("value", "") for i in soup.select("input[type=hidden]") if i.get("name")}
    for s in soup.select("select"):
        opt = s.select_one("option[selected]") or s.select_one("option")
        if s.get("name") and opt is not None:
            data[s["name"]] = opt.get("value", "")
    return data


def postback(url, soup, target, extra=None):
    data = form_fields(soup)
    data.update({"__EVENTTARGET": target, "__EVENTARGUMENT": ""})
    data.update(extra or {})
    r = _req("POST", url, data=data)
    return r.url, BeautifulSoup(r.text, "html.parser")


def financial_year(today=None):
    today = today or dt.date.today()
    start = today.year if today.month >= 4 else today.year - 1
    return f"{start}-{start + 1}"


def parse_village_table(soup):
    table = soup.find("table", id="tableReportTable")
    if table is None:
        raise RuntimeError("Village table not found: the JJM page layout may have changed")
    rows = table.find_all("tr")
    head = [c.get_text(" ", strip=True) for c in rows[0].find_all(["th", "td"])]
    expected = ["S.No.", "District", "Block", "Panchayat", "Village id", "Village", "House Holds", "House Connection"]
    if head[:8] != expected:
        raise RuntimeError(f"Unexpected columns {head}")
    out = []
    for tr in rows[1:]:
        cells = [c.get_text(" ", strip=True) for c in tr.find_all("td")]
        if len(cells) < 8 or not cells[0].isdigit():
            continue
        m = re.search(r"Village LGD Code\s*:\s*(\d+)", cells[5])
        out.append({
            "district": cells[1], "block": cells[2].title(), "panchayats": cells[3],
            "jjm_village_id": cells[4],
            "village": re.sub(r"\s*\[.*\]\s*$", "", cells[5]),
            "lgd_village_code": m.group(1) if m else None,
            "households": int(cells[6].replace(",", "")),
            "hh_connections": int(cells[7].replace(",", "")),
        })
    return out


def fetch(fy=None):
    fy = fy or financial_year()
    r = _req("GET", C.JJM_ENTRY)
    soup = BeautifulSoup(r.text, "html.parser")
    reported = re.search(r"Reported till\s*([0-9/]+)", soup.get_text(" "))
    # choosing the state triggers a postback, then Show opens the district table
    url, soup = postback(C.JJM_ENTRY, soup, "ctl00$CPHPage$ddState",
                         {"ctl00$CPHPage$ddFinyear": fy, "ctl00$CPHPage$ddState": C.TRIPURA_JJM_STATE_ID})
    url, soup = postback(url, soup, "", {"ctl00$CPHPage$ddFinyear": fy,
                                         "ctl00$CPHPage$ddState": C.TRIPURA_JJM_STATE_ID,
                                         "ctl00$CPHPage$btnShow": "Show"})
    links = []
    for a in soup.find_all("a", href=True):
        m = re.search(r"__doPostBack\('([^']*\$lnkvillage)'", a["href"])
        if m:
            links.append(m.group(1))
    if not links:
        raise RuntimeError("No district links found on the J7 district page")
    district_url, district_soup = url, soup
    villages = []
    for target in links:
        list_url, list_soup = postback(district_url, district_soup, target)
        _, all_soup = postback(list_url, list_soup, "ctl00$CPHPage$ddPagrno", {"ctl00$CPHPage$ddPagrno": "0"})
        rows = parse_village_table(all_soup)
        print(f"  {rows[0]['district'] if rows else '?'}: {len(rows)} villages")
        villages.extend(rows)
    return {
        "financial_year": fy,
        "reported_till": reported.group(1) if reported else None,
        "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"),
        "villages": villages,
    }


def past_years(first=C.HISTORY_FIRST_FY):
    """Financial years from `first` up to, but not including, the current one."""
    start, now = int(first[:4]), int(financial_year()[:4])
    return [f"{y}-{y + 1}" for y in range(start, now)]


def main():
    C.RAW.mkdir(parents=True, exist_ok=True)
    data = fetch()
    if len(data["villages"]) < 500:
        raise RuntimeError(f"Only {len(data['villages'])} villages fetched; expected about 766")
    out = C.RAW / "jjm_tripura_villages.json"
    out.write_text(json.dumps(data, indent=1))
    print(f"Saved {len(data['villages'])} villages (reported till {data['reported_till']}) -> {out}")

    history = {}
    for fy in past_years():
        print(f"Financial year {fy}")
        try:
            history[fy] = fetch(fy)["villages"]
        except Exception as e:  # history is a bonus: never fail the build over it
            print(f"  skipped {fy}: {e}", file=sys.stderr)
    (C.RAW / "jjm_tripura_history.json").write_text(json.dumps(history))
    print(f"Saved history for {len(history)} past financial years")


if __name__ == "__main__":
    main()
