"""Pairwise 90-day rolling Pearson correlations across the 5 series in
Section 06's matrix:
  - VITL stock (daily close)
  - Premium Gap % (weekly, derived from usda_eggs_weekly + vitl_retail_price)
  - Conventional egg wholesale ($/dz, weekly)
  - Reddit mention volume (weekly, all subs)
  - News article cadence (weekly count)

All series resampled to weekly (week-ending Sunday) so the matrix is
comparable. Output: data/correlations.csv with rows = pairs and a
correlation column.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUT_CSV = DATA_DIR / "correlations.csv"

LABELS = {
    "stock":   "VITL stock",
    "gap":     "Premium Gap %",
    "conv":    "Conventional egg $",
    "reddit":  "Reddit mentions",
    "news":    "News cadence",
}


def _to_weekly(df: pd.DataFrame, date_col: str, val_col: str,
               agg: str = "mean") -> pd.Series:
    """Bucket a date-indexed series into week-ending-Sunday weekly values."""
    if df.empty: return pd.Series(dtype=float)
    s = df[[date_col, val_col]].copy()
    s[date_col] = pd.to_datetime(s[date_col], errors="coerce")
    s = s.dropna(subset=[date_col])
    s["week"] = s[date_col].dt.to_period("W-SUN").dt.end_time.dt.strftime("%Y-%m-%d")
    if agg == "sum":
        out = s.groupby("week")[val_col].sum()
    else:
        out = s.groupby("week")[val_col].mean()
    out.index = pd.to_datetime(out.index)
    return out.sort_index()


def main() -> int:
    # ── Load each series ──────────────────────────────────────────────────────
    stock = pd.read_csv(DATA_DIR / "vitl_stock.csv") if (DATA_DIR / "vitl_stock.csv").exists() else pd.DataFrame()
    egg   = pd.read_csv(DATA_DIR / "usda_eggs_weekly.csv") if (DATA_DIR / "usda_eggs_weekly.csv").exists() else pd.DataFrame()
    retail = pd.read_csv(DATA_DIR / "vitl_retail_price.csv") if (DATA_DIR / "vitl_retail_price.csv").exists() else pd.DataFrame()
    reddit = pd.read_csv(DATA_DIR / "reddit_mentions_weekly.csv") if (DATA_DIR / "reddit_mentions_weekly.csv").exists() else pd.DataFrame()
    news = pd.read_csv(DATA_DIR / "news_articles.csv") if (DATA_DIR / "news_articles.csv").exists() else pd.DataFrame()

    series: dict[str, pd.Series] = {}

    # VITL stock — weekly mean of daily close
    if not stock.empty:
        series["stock"] = _to_weekly(stock, "date", "close", agg="mean")

    # Conventional egg + Premium Gap %
    if not egg.empty:
        s_conv = _to_weekly(egg, "week", "price_per_dozen", agg="mean")
        series["conv"] = s_conv
        if not retail.empty:
            r = retail.copy()
            r["dt"] = pd.to_datetime(r["month"], format="%Y-%m")
            r = r.sort_values("dt")
            # Forward-fill monthly retail to the egg weeks
            gap_vals = []; gap_dates = []
            for dt, conv_v in s_conv.items():
                prior = r[r["dt"] <= dt]
                if prior.empty or conv_v <= 0: continue
                retail_v = float(prior.iloc[-1]["retail_price_per_dozen"])
                gap_pct = (retail_v / conv_v - 1) * 100
                gap_vals.append(gap_pct); gap_dates.append(dt)
            if gap_vals:
                series["gap"] = pd.Series(gap_vals, index=pd.to_datetime(gap_dates)).sort_index()

    # Reddit mentions — weekly sum across subreddits
    if not reddit.empty:
        r = reddit.copy()
        r["week"] = pd.to_datetime(r["week"], errors="coerce")
        r = r.dropna(subset=["week"])
        s_r = r.groupby("week")["post_count"].sum().sort_index()
        series["reddit"] = s_r

    # News cadence — weekly article count.
    # Normalize index to YYYY-MM-DD at midnight so it joins with the other
    # series (which all go through .strftime("%Y-%m-%d") → pd.to_datetime()
    # and land at 00:00:00). end_time keeps nanosecond precision otherwise.
    if not news.empty:
        n = news.copy()
        n["date"] = pd.to_datetime(n["date"], errors="coerce")
        n = n.dropna(subset=["date"])
        n["week"] = n["date"].dt.to_period("W-SUN").dt.end_time.dt.strftime("%Y-%m-%d")
        s_n = n.groupby("week").size().astype(float)
        s_n.index = pd.to_datetime(s_n.index)
        series["news"] = s_n.sort_index()

    if len(series) < 2:
        print("  [warn] insufficient series available — wrote empty matrix")
        pd.DataFrame(columns=["row","col","correlation","n_overlap"]).to_csv(OUT_CSV, index=False)
        return 0

    # Align to common weekly index — outer join, drop weeks with any NaN per pair
    keys = list(series.keys())
    rows = []
    for i, a in enumerate(keys):
        for b in keys:
            if a == b:
                rows.append({"row": a, "col": b, "correlation": 1.0, "n_overlap": int(series[a].count())})
                continue
            joined = pd.concat([series[a].rename("a"), series[b].rename("b")], axis=1, join="inner").dropna()
            if len(joined) < 10:
                rows.append({"row": a, "col": b, "correlation": None, "n_overlap": int(len(joined))})
                continue
            corr = float(joined["a"].corr(joined["b"]))
            rows.append({"row": a, "col": b, "correlation": round(corr, 3),
                         "n_overlap": int(len(joined))})

    df = pd.DataFrame(rows)
    # Add display labels
    df["row_label"] = df["row"].map(LABELS)
    df["col_label"] = df["col"].map(LABELS)
    df = df[["row","row_label","col","col_label","correlation","n_overlap"]]
    df.to_csv(OUT_CSV, index=False)
    print(f"  ✓ wrote {OUT_CSV.name}  rows={len(df)}  series_in_matrix={len(keys)}")
    for k in keys:
        print(f"    · {LABELS[k]:24s} weeks={len(series[k])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
