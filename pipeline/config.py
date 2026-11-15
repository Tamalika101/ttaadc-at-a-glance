"""Paths, sources and settings for the TTAADC at a Glance pipeline."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"                      # downloaded each run, not committed
REF = DATA / "reference"                # LGD lists, committed (manual download)
ELECTION = DATA / "election"            # hand-compiled, committed
OUT = ROOT / "site" / "data"

JJM_BASE = "https://ejalshakti.gov.in/JJM/JJMReports/Physical/"
JJM_ENTRY = JJM_BASE + "JJMRep_VillageWiseFHTCCoverage.aspx"   # Format J7
TRIPURA_JJM_STATE_ID = "30"

# Villages with fewer households than this are left out of "furthest behind" lists.
MIN_HOUSEHOLDS_FOR_RANKING = 50

# Water history: one snapshot per financial year from the start of the 2021-26 council term.
HISTORY_FIRST_FY = "2021-2022"
