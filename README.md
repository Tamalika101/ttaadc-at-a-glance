# TTAADC at a Glance

**Live site → https://tamalika101.github.io/ttaadc-at-a-glance/**

A data view of the **Tripura Tribal Areas Autonomous District Council (TTAADC)**, which governs about two-thirds of Tripura's land. It is built only on real, recent public data, and leaves out anything that can't be backed by it.

1. **The 2026 council election:** winner, runner-up, votes and margin in all 28 constituencies, plus party vote shares.
2. **Drinking water:** how many homes have a household tap in the council's own villages, compared with the rest of rural Tripura, by council zone, district and village. This section **refreshes automatically every week** from the national Jal Jeevan Mission dashboard.

## Key findings (as of November 2026)

- Tipra Motha Party won **24 of 28 seats** on about 59% of the votes cast for the five main parties. Two seats were decided by under 2 percentage points.
- Homes in villages wholly under the council are **less likely to have a tap: about 82%, against 89%** in villages outside it. That leaves roughly 48,000 council-village homes without one.
- **29 council villages are below 50% coverage, against 2 outside the council area.**
- The gap shows up in 6 of Tripura's 8 districts.

## How it works

```
Jal Jeevan Mission (J7 report) ──► pipeline/fetch_jjm.py ──► data/raw/ ─┐
LGD lists (data/reference/, manual) ────────────────────────────────────┼─► pipeline/run_all.py ─► site/data/*.json ─► site/ (GitHub Pages)
Election results (data/election/, hand-compiled) ───────────────────────┘
GitHub Actions runs the chain every Monday
```

| Path | What it is |
|---|---|
| `pipeline/fetch_jjm.py` | Scrapes the J7 village-wise tap coverage report for Tripura (ASP.NET page flow) |
| `pipeline/reference.py` | Loads Local Government Directory lists: villages, Gram Panchayats, TTAADC village councils and zones |
| `pipeline/water.py` | Labels each village as wholly in the council area, split, or outside; aggregates coverage |
| `pipeline/election.py` | Election summary from `data/election/` |
| `data/election/SOURCES.md` | Where every election number came from and how it was cross-checked |
| `data/reference/README.md` | The LGD lists and how they were downloaded |
| `site/` | Static website (HTML + Plotly) |

## Run it yourself

```bash
pip install -r requirements.txt
python -m pipeline.run_all --fetch      # download water data + build
python -m http.server -d site 8000      # open http://localhost:8000
```

## Method and limitations

- **Council area:** the LGD links every non-council village to a Gram Panchayat. A village with none is counted as wholly in the council area. A village with Gram Panchayats whose water record also names a TTAADC village council is counted as *split*, and shown separately because the water data can't be divided.
- **Zones** are the council's 40 Block Advisory Committees. Water figures are not shown by constituency, because no public list maps villages to constituencies.
- **Election data** were compiled by hand because the State Election Commission's portal can't be reached from outside India. Only the top two candidates per seat are included.
- **Water data** are self-reported by state departments and count connections, not reliable supply or water quality.
- **Jobs (MGNREGA)** are not included yet. The scheme was replaced by VB-G RAM G on 1 July 2026, and the official portal is unreachable from outside India.

## Sources

- [Jal Jeevan Mission, Format J7](https://ejalshakti.gov.in/JJM/JJMReports/Physical/JJMRep_VillageWiseFHTCCoverage.aspx), Ministry of Jal Shakti
- [Local Government Directory](https://lgdirectory.gov.in/), Ministry of Panchayati Raj
- [2026 TTAADC election, Wikipedia](https://en.wikipedia.org/wiki/2026_Tripura_Tribal_Areas_Autonomous_District_Council_election), cross-checked with news reports (see `data/election/SOURCES.md`)
