"""Google Trends — premium-egg category search interest, 5yr weekly.

Multi-term comparison query: pytrends.build_payload() takes up to 5 terms
at once and returns them on a single normalized 0-100 interest scale, so the
4 terms below are comparable to each other.

Output: data/google_trends_category_weekly.csv
  columns: week, term, interest

Status: FRAGILE — pytrends hits Google rate limits often; on 429 we retry
with backoff and degrade gracefully (preserve existing CSV on failure).
Per analyst rule: Google Trends absolute levels are unreliable in 2026 (AI
assistants are eating queries), but RELATIVE comparison between 4 terms in
the same window is still meaningful — that's exactly what this fetcher does.
"""
from __future__ import annotations

import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

try:
    from pytrends.request import TrendReq
except ImportError:
    print("ERROR: pytrends not installed. Run: pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
OUT_CSV = DATA_DIR / "google_trends_category_weekly.csv"

# Premium-egg category — 4 terms in one comparison query so they share scale.
TERMS = [
    "pasture raised eggs",
    "organic eggs",
    "cage free eggs",
    "regenerative eggs",
]
TIMEFRAME = "today 5-y"
GEO = "US"  # US-only — VITL is US business


def main() -> int:
    try:
        pt = TrendReq(hl="en-US", tz=360)
    except Exception as exc:
        print(f"  [error] pytrends init failed: {exc}", file=sys.stderr)
        return 0  # exit 0 — don't break the Makefile chain

    df = None
    for attempt in range(3):
        try:
            pt.build_payload(TERMS, timeframe=TIMEFRAME, geo=GEO)
            df = pt.interest_over_time()
            break
        except Exception as exc:
            wait = 5 * (attempt + 1)
            print(f"  [warn] pytrends attempt {attempt+1} failed: {exc} · sleeping {wait}s")
            time.sleep(wait)
    if df is None or df.empty:
        print("  [warn] pytrends returned empty — preserving existing CSV (if any)")
        if not OUT_CSV.exists():
            pd.DataFrame(columns=["week", "term", "interest"]).to_csv(OUT_CSV, index=False)
        return 0

    df = df.reset_index()
    long = df.melt(id_vars=["date"], value_vars=TERMS, var_name="term", value_name="interest")
    long["week"] = pd.to_datetime(long["date"]).dt.strftime("%Y-%m-%d")
    long = long[["week", "term", "interest"]].sort_values(["week", "term"]).reset_index(drop=True)
    long["interest"] = long["interest"].astype(int)
    long.to_csv(OUT_CSV, index=False)

    # Quick summary so stdout shows what was pulled
    latest_week = long["week"].max()
    latest = long[long["week"] == latest_week].set_index("term")["interest"].to_dict()
    print(f"  ✓ wrote {OUT_CSV.name}  rows={len(long)}  range={long['week'].min()}..{latest_week}")
    print(f"  · latest week {latest_week}:")
    for t in TERMS:
        v = latest.get(t, 0)
        print(f"    {t:24s} {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
