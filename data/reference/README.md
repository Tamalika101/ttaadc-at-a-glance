# Reference files: Local Government Directory (LGD), Tripura

Downloaded manually on 15 Nov 2026 (IST) from https://lgdirectory.gov.in → Download Directory → Tripura
(the download page requires a CAPTCHA, so these are refreshed by hand, not by the scheduled workflow).
Converted from SpreadsheetML (.xls) to CSV without changing any values.

| File | What it lists |
|---|---|
| `lgd_villageofSpecificState.csv` | All 898 revenue villages in Tripura with LGD village codes |
| `lgd_priLbSpecificState.csv` | Panchayati Raj bodies: 607 Gram Panchayats, 35 Block and 8 Zila Panchayats |
| `lgd_tlbSpecificState.csv` | Traditional local bodies: the TTAADC, its 40 Block Advisory Committees and 587 Village Councils (village committees) |
| `lgd_villageGramPanchayatMapping.csv` | Village → Gram Panchayat links. Village councils are not mapped here; 485 villages have no Gram Panchayat at all |

The first rows of each file are the LGD report title and header lines; data starts below them.

## Village map: `tripura_villages_pc11.geojson`

Village and town outlines for Tripura (2011 Census), cut from the SHRUG open polygons (SHRUG 2.2, Development Data Lab,
https://www.devdatalab.org/shrug_download/) on 15 Nov 2026 and simplified for the web (about 30 m tolerance).
Joined to LGD villages through the LGD list's Census 2011 code. Boundaries carry 0–1 km of error (per SHRUG's notes),
so the map is an overview, not a survey map.

Licence: CC BY-NC-SA 4.0. This file is a derivative and is shared under the same licence.
Citation: Asher, Lunt, Matsuura and Novosad (2021), "Development research at high geographic resolution: an analysis of
night-lights, firms, and poverty in India using the SHRUG open data platform", World Bank Economic Review 35(4).
