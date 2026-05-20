"""Egg market prices — USDA AMS weekly shell + breaker + BLS CPI eggs cross-check.

Real-source attempts:
  1. BLS public API for CPI eggs series APU0000708111 (no key required, 25 req/day)
     → monthly retail egg price for cross-check
  2. USDA MARS / AMS shell egg wholesale → requires API key registration; not
     wired in this pass. Skeleton ready for it.

Behavior: writes `data/usda_eggs_weekly.csv` and `data/breaker_prices.csv`.
If both real fetches fail, preserves whatever seeded data already exists in
those CSVs (initial seed shipped with the repo).

Outputs:
  data/usda_eggs_weekly.csv  (week, price_per_dozen, source)
  data/breaker_prices.csv    (week, price_per_dozen, source)
  data/bls_cpi_eggs_monthly.csv  (month, price, source)
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

BLS_API = "https://api.bls.gov/publicAPI/v2/timeseries/data/APU0000708111"
UA = "vitl-demand-dashboard/1.0 (+research)"


def fetch_bls_cpi_eggs() -> pd.DataFrame:
    """BLS public API — no auth, no key. Returns latest ~3-year monthly data."""
    end_year = datetime.today().year
    payload = {"seriesid": ["APU0000708111"], "startyear": str(end_year - 3),
               "endyear": str(end_year)}
    try:
        r = requests.post(BLS_API, json=payload, timeout=30, headers={"User-Agent": UA})
        r.raise_for_status()
        j = r.json()
    except (requests.RequestException, ValueError) as exc:
        print(f"  [warn] BLS CPI eggs fetch failed: {exc}", file=sys.stderr)
        return pd.DataFrame()

    if j.get("status") != "REQUEST_SUCCEEDED":
        print(f"  [warn] BLS returned non-success: {j.get('message', j.get('status'))}", file=sys.stderr)
        return pd.DataFrame()

    series = j.get("Results", {}).get("series", [])
    if not series:
        return pd.DataFrame()

    rows = []
    for s in series:
        for d in s.get("data", []):
            year = d.get("year"); period = d.get("period", "")
            if not period.startswith("M"):
                continue
            mo = period[1:].zfill(2)
            try:
                price = float(d.get("value"))
            except (TypeError, ValueError):
                continue
            rows.append({"month": f"{year}-{mo}", "price": price, "source": "BLS APU0000708111"})
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows).sort_values("month").reset_index(drop=True)
    return df


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # ── BLS CPI eggs monthly (real fetch, no key) ─────────────────────────────
    print("  fetching BLS CPI eggs (APU0000708111) ...")
    cpi = fetch_bls_cpi_eggs()
    if not cpi.empty:
        out = DATA_DIR / "bls_cpi_eggs_monthly.csv"
        cpi.to_csv(out, index=False)
        print(f"  ✓ wrote {out.name}  rows={len(cpi)}  range={cpi['month'].min()}..{cpi['month'].max()}")
    else:
        print("  [warn] BLS empty — skipping CPI cross-check write")

    # ── USDA AMS wholesale shell + breaker — preserve seeded data ─────────────
    shell = DATA_DIR / "usda_eggs_weekly.csv"
    breaker = DATA_DIR / "breaker_prices.csv"
    if shell.exists():
        df = pd.read_csv(shell)
        print(f"  · usda_eggs_weekly.csv  preserved  rows={len(df)}  (seed; MARS fetcher TBD)")
    else:
        print(f"  [warn] {shell.name} missing — no seed and MARS fetcher TBD", file=sys.stderr)
    if breaker.exists():
        df = pd.read_csv(breaker)
        print(f"  · breaker_prices.csv    preserved  rows={len(df)}  (seed; MARS fetcher TBD)")
    else:
        print(f"  [warn] {breaker.name} missing — no seed and MARS fetcher TBD", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
