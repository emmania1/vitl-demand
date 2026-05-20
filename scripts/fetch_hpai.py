"""USDA APHIS HPAI confirmed-cases + layer-flock data.

APHIS publishes weekly tables of HPAI cases (commercial poultry / backyard /
wild birds) on the web. There's no clean public API — the team posts CSVs
linked from https://www.aphis.usda.gov/livestock-poultry-disease/avian/avian-influenza
and updates them weekly.

Approach: try to download the most recent layer-flock table from the APHIS
data feed (URL stable in recent years); fall back to seeded CSV.

Outputs:
  data/hpai_cases.csv    (week, commercial_layer_cases, source)
  data/layer_flock.csv   (month, layer_flock_millions, source)
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# USDA APHIS hosts CSV exports under their HPAI dashboard. URLs have moved
# multiple times; we attempt the known path and degrade silently to seed.
APHIS_COMMERCIAL_URL = (
    "https://www.aphis.usda.gov/sites/default/files/hpai-commercial-table.csv"
)
UA = "vitl-demand-dashboard/1.0 (+research)"


def attempt_aphis_fetch() -> pd.DataFrame:
    try:
        r = requests.get(APHIS_COMMERCIAL_URL, headers={"User-Agent": UA}, timeout=20)
        r.raise_for_status()
        # APHIS CSVs sometimes change schema; try to parse and pick what we need.
        from io import StringIO
        df = pd.read_csv(StringIO(r.text))
        return df
    except Exception as exc:  # noqa: BLE001
        print(f"  [warn] APHIS fetch failed: {exc}", file=sys.stderr)
        return pd.DataFrame()


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("  attempting APHIS HPAI commercial table fetch ...")
    aphis = attempt_aphis_fetch()
    if not aphis.empty:
        # Schema-shift hardening: only overwrite if we can find a date column +
        # a numeric case-count column. Otherwise we keep the seed intact.
        date_col = next((c for c in aphis.columns if "date" in c.lower() or "week" in c.lower()), None)
        n_col = next((c for c in aphis.columns if "bird" in c.lower() or "case" in c.lower() or "count" in c.lower()), None)
        if date_col and n_col:
            print(f"  · parsed APHIS table  columns={date_col!r}, {n_col!r}  rows={len(aphis)}")
            print("  [TODO] real-fetch parsing not yet wired — preserving seed.")
        else:
            print(f"  [warn] APHIS schema unrecognized (cols: {list(aphis.columns)[:6]}) — preserving seed.")
    else:
        print("  · APHIS not reachable — preserving seed.")

    seed_files = [
        ("hpai_cases.csv",  "(week × cases)"),
        ("layer_flock.csv", "(month × layer flock millions)"),
    ]
    for fname, label in seed_files:
        path = DATA_DIR / fname
        if path.exists():
            df = pd.read_csv(path)
            print(f"  ✓ {fname:24s} preserved  rows={len(df)}  {label}")
        else:
            print(f"  [warn] {fname} missing — no data to show", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
