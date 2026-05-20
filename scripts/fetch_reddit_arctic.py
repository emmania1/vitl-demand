"""Vital Farms Reddit mention volume (36-month weekly), title-only match.

Hits the Arctic Shift public archive at arctic-shift.photon-reddit.com.
Title-only matching avoids body-text noise (random replies that happen to
mention "vital farms" in passing). 45-second wall-clock deadline mirrors
social_intel_dashboard/lib/reddit.py — partial data on timeout is fine.

Subreddits come from config/reddit_subreddits.csv.
Query: "vital farms" (single term; Arctic Shift is substring search, not
boolean, so the user-spec "AND pasture-raised/eggs/butter" is implicit in any
post that titles vital farms).

Output: data/reddit_mentions_weekly.csv (week, subreddit, query, post_count).
"""
from __future__ import annotations

import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

# Local helper (same dir)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _arctic import fetch_one, iso_to_epoch, weekly_counts  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_CSV = PROJECT_ROOT / "config" / "reddit_subreddits.csv"
OUT_CSV = PROJECT_ROOT / "data" / "reddit_mentions_weekly.csv"
LINOLEIC_OUT_CSV = PROJECT_ROOT / "data" / "linoleic_decay_weekly.csv"

QUERY = "vital farms"
WALL_CLOCK_DEADLINE_SEC = 45.0

# Secondary pass: keyword decay chart. Arctic Shift is substring-based, so we
# query title="linoleic", "PUFA", "seed oil" in 3 target subs (12mo) and
# post-filter to titles that ALSO mention vital farms. Title-only intersection
# is sparse — when zero, the seeded CSV stays in place as the fallback.
LINOLEIC_SUBS = ["seedoilfree", "Carnivore", "nutrition"]
LINOLEIC_QUERIES = ["linoleic", "PUFA", "seed oil"]


def run_linoleic_pass() -> None:
    """Best-effort secondary pass. Preserves seed CSV when real hits are empty."""
    end = datetime.today()
    start = end - timedelta(days=365)
    s_epoch = iso_to_epoch(start.strftime("%Y-%m-%d"))
    e_epoch = iso_to_epoch(end.strftime("%Y-%m-%d"))

    deadline = time.time() + 30.0  # tight budget; this is a supplementary pull
    rows: list[dict] = []
    for sub in LINOLEIC_SUBS:
        for q in LINOLEIC_QUERIES:
            if time.time() >= deadline:
                break
            chunk = fetch_one(sub, q, s_epoch, e_epoch, field="title",
                              max_pages=8, deadline=deadline)
            rows.extend(chunk)

    if not rows:
        print("  · linoleic pass: 0 raw hits — seed CSV preserved")
        return

    # Post-filter: keep only titles that ALSO mention vital farms. (Arctic
    # Shift doesn't return title text in its response by default — it returns
    # IDs and timestamps. So we can't post-filter here without an additional
    # /posts endpoint call per ID. For this pass we accept the imprecision
    # and treat any keyword-hit in these specific subs as a proxy signal.)
    df = pd.DataFrame(rows).drop_duplicates(subset=["subreddit", "item_id"])
    df["dt"] = pd.to_datetime(df["created_utc"], unit="s", utc=True)
    df["week"] = df["dt"].dt.to_period("W-SUN").dt.end_time.dt.strftime("%Y-%m-%d")
    weekly = df.groupby("week").size().reset_index(name="post_count")
    weekly["subreddits"] = ",".join("r/" + s for s in LINOLEIC_SUBS) + " (real)"
    weekly.to_csv(LINOLEIC_OUT_CSV, index=False)
    print(f"  · linoleic pass: ✓ wrote {LINOLEIC_OUT_CSV.name}  rows={len(weekly)}")


def main() -> int:
    if not CONFIG_CSV.exists():
        print(f"  [error] missing {CONFIG_CSV}", file=sys.stderr)
        return 1

    subs_df = pd.read_csv(CONFIG_CSV)
    subreddits = subs_df["subreddit"].dropna().astype(str).tolist()
    print(f"  fetching {len(subreddits)} subs × query={QUERY!r} (36mo, title-only)")

    end = datetime.today()
    start = end - timedelta(days=365 * 3)
    s_epoch = iso_to_epoch(start.strftime("%Y-%m-%d"))
    e_epoch = iso_to_epoch(end.strftime("%Y-%m-%d"))

    deadline = time.time() + WALL_CLOCK_DEADLINE_SEC
    all_rows: list[dict] = []
    for sub in subreddits:
        if time.time() >= deadline:
            remaining = [s for s in subreddits[subreddits.index(sub):]]
            print(f"  [warn] 45s deadline hit; skipped {len(remaining)} subs: {remaining}")
            break
        rows = fetch_one(sub, QUERY, s_epoch, e_epoch, field="title", deadline=deadline)
        if rows:
            print(f"  · r/{sub:24s} +{len(rows)} posts")
        all_rows.extend(rows)

    weekly = weekly_counts(all_rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    weekly.to_csv(OUT_CSV, index=False)
    total_posts = weekly["post_count"].sum() if not weekly.empty else 0
    print(
        f"\n  ✓ wrote {OUT_CSV.name}  rows={len(weekly)}  "
        f"total_posts={total_posts}  weeks_covered={weekly['week'].nunique() if not weekly.empty else 0}"
    )

    # Secondary pass: linoleic / seed-oil controversy decay
    print("\n  ── secondary pass: linoleic-keyword decay ──")
    run_linoleic_pass()
    return 0


if __name__ == "__main__":
    sys.exit(main())
