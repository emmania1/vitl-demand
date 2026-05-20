"""Brand share-of-voice across pasture-raised egg competitor set, via Arctic Shift.

Same Reddit pipeline as fetch_reddit_arctic.py but ONE query per competitor
brand. Output is keyed on brand so the dashboard can render a stacked-area
chart of weekly mentions across the 6-brand set.

Brand set (per VITL recovery thesis — does competitor mindshare grow during
the ERP shelf-gap?):
  - vital farms        (own brand — included so chart can show relative share)
  - handsome brook
  - alexandre          (Alexandre Family Farm)
  - pete and gerry     (variant: "pete & gerry's"; we use the "and" spelling)
  - happy egg
  - organic valley

Same 45s wall-clock deadline; uses ALL subs from config/reddit_subreddits.csv
because food / health / cooking subs span all brands.

Output: data/competitor_mentions_weekly.csv (week, brand, post_count).
"""
from __future__ import annotations

import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _arctic import fetch_one, iso_to_epoch  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_CSV = PROJECT_ROOT / "config" / "reddit_subreddits.csv"
OUT_CSV = PROJECT_ROOT / "data" / "competitor_mentions_weekly.csv"

# (display_brand, query). One query per brand keeps the substring match clean.
COMPETITORS: list[tuple[str, str]] = [
    ("Vital Farms",      "vital farms"),
    ("Handsome Brook",   "handsome brook"),
    ("Alexandre",        "alexandre"),
    ("Pete & Gerry's",   "pete and gerry"),
    ("Happy Egg",        "happy egg"),
    ("Organic Valley",   "organic valley"),
]
# 6 brands × 15 subs in 45s hits Arctic Shift's rate limiter halfway through.
# Bumped to 240s and we narrow to highest-signal subs only (priority=core OR
# the cooking-anchor subs) to keep the chart readable without burning quota.
WALL_CLOCK_DEADLINE_SEC = 240.0
PER_BRAND_PAUSE_SEC     = 1.5


def main() -> int:
    if not CONFIG_CSV.exists():
        print(f"  [error] missing {CONFIG_CSV}", file=sys.stderr)
        return 1

    subs_df = pd.read_csv(CONFIG_CSV)
    # Narrow to core-priority subs — keeps requests reasonable across 6 brands.
    if "priority" in subs_df.columns:
        core = subs_df[subs_df["priority"].astype(str).str.lower() == "core"]
        subreddits = core["subreddit"].dropna().astype(str).tolist()
    else:
        subreddits = subs_df["subreddit"].dropna().astype(str).tolist()
    print(
        f"  fetching {len(COMPETITORS)} brands × {len(subreddits)} core subs "
        f"(36mo, title-only, {int(WALL_CLOCK_DEADLINE_SEC)}s deadline)"
    )

    end = datetime.today()
    start = end - timedelta(days=365 * 3)
    s_epoch = iso_to_epoch(start.strftime("%Y-%m-%d"))
    e_epoch = iso_to_epoch(end.strftime("%Y-%m-%d"))

    deadline = time.time() + WALL_CLOCK_DEADLINE_SEC
    all_rows: list[dict] = []
    deadline_hit = False
    for brand_display, query in COMPETITORS:
        if deadline_hit:
            break
        brand_count = 0
        for sub in subreddits:
            if time.time() >= deadline:
                print(f"  [warn] {int(WALL_CLOCK_DEADLINE_SEC)}s deadline hit during {brand_display} (sub {sub})")
                deadline_hit = True
                break
            rows = fetch_one(
                sub, query, s_epoch, e_epoch, field="title",
                max_pages=15, deadline=deadline, page_sleep=0.6,
            )
            for r in rows:
                r["brand"] = brand_display
            all_rows.extend(rows)
            brand_count += len(rows)
        print(f"  · {brand_display:18s}  +{brand_count} posts")
        time.sleep(PER_BRAND_PAUSE_SEC)

    if not all_rows:
        out = pd.DataFrame(columns=["week", "brand", "post_count"])
    else:
        df = pd.DataFrame(all_rows).drop_duplicates(subset=["brand", "subreddit", "item_id"])
        df["dt"] = pd.to_datetime(df["created_utc"], unit="s", utc=True)
        df["week"] = df["dt"].dt.to_period("W-SUN").dt.end_time.dt.strftime("%Y-%m-%d")
        out = (
            df.groupby(["week", "brand"])
            .size()
            .reset_index(name="post_count")
            .sort_values(["week", "brand"])
            .reset_index(drop=True)
        )

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    if not out.empty:
        per_brand = out.groupby("brand")["post_count"].sum().sort_values(ascending=False)
        print("\n  brand totals (36mo, all subs):")
        for b, v in per_brand.items():
            print(f"    {b:18s}  {v:>5d}")
    print(f"\n  ✓ wrote {OUT_CSV.name}  rows={len(out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
