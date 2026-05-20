"""FINRA semi-monthly short interest for VITL.

Two passes:
  1. yfinance snapshot — `info.shortPercentOfFloat`, `info.sharesShort`,
     `info.daysToCover` → appends today's row if not already present.
  2. Historical series — FINRA distributes short-interest data as bulk
     files at cdn.finra.org/equity/regsho/. Pulling them per-ticker requires
     filtering many large files; deferred to a separate pass. Seed CSV has
     24-month history.

Output: data/short_interest.csv  (date, short_interest_shares, short_pct_of_float, days_to_cover, source)
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import yfinance as yf

try:
    from curl_cffi import requests as curl_requests
    _SESSION = curl_requests.Session(impersonate="chrome")
except Exception:  # noqa: BLE001
    _SESSION = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUT_CSV = DATA_DIR / "short_interest.csv"
TICKER = "VITL"


def _ticker(symbol: str) -> yf.Ticker:
    if _SESSION is not None:
        return yf.Ticker(symbol, session=_SESSION)
    return yf.Ticker(symbol)


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.today().strftime("%Y-%m-%d")

    # Load seed/historical
    if OUT_CSV.exists():
        existing = pd.read_csv(OUT_CSV)
    else:
        existing = pd.DataFrame(columns=["date","short_interest_shares","short_pct_of_float","days_to_cover","source"])

    # yfinance snapshot
    snap_row = None
    try:
        info = _ticker(TICKER).info or {}
        shares_short = info.get("sharesShort")
        pct = info.get("shortPercentOfFloat")
        days = info.get("shortRatio")
        if shares_short and pct:
            snap_row = {
                "date": today,
                "short_interest_shares": int(shares_short),
                "short_pct_of_float": round(float(pct) * 100, 1) if float(pct) < 1.5 else round(float(pct), 1),
                "days_to_cover": round(float(days), 2) if days else None,
                "source": "yfinance snapshot",
            }
            print(f"  ✓ yfinance snap: {pct*100 if pct<1.5 else pct:.1f}% float short, {shares_short:,} shares")
    except Exception as exc:  # noqa: BLE001
        print(f"  [warn] yfinance short-interest snapshot failed: {exc}", file=sys.stderr)

    if snap_row is not None:
        existing = existing[existing["date"] != today]
        existing = pd.concat([existing, pd.DataFrame([snap_row])], ignore_index=True)
        existing = existing.sort_values("date").reset_index(drop=True)
        existing.to_csv(OUT_CSV, index=False)
        print(f"  ✓ updated {OUT_CSV.name}  rows={len(existing)}  latest={existing.iloc[-1]['date']} @ {existing.iloc[-1]['short_pct_of_float']:.1f}%")
    else:
        if OUT_CSV.exists():
            print(f"  · {OUT_CSV.name} preserved  rows={len(existing)}  (seed; yfinance snapshot unavailable)")
        else:
            print(f"  [warn] no seed and no live snapshot — empty file", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
