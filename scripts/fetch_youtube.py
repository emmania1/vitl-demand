"""YouTube Data API v3 — monthly aggregates for Vital Farms search.

Same pattern as social_intel_dashboard/lib/youtube.py BUT bucketed monthly
(per task spec, not weekly). Quota cost: 100 units per search.list call ×
36 months × 2 queries ≈ 7,200 units, well under the 10k/day free tier IF
run weekly (not daily) — this is the QUOTA-HEAVIEST fetcher.

Queries (unioned by video ID):
  - "vital farms"
  - "pasture raised eggs"

Output: data/youtube_monthly.csv with columns:
  month, query, video_count, view_sum

No-ops cleanly (exit 0) when YOUTUBE_API_KEY is missing, so the Makefile
chain doesn't break when running without credentials.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUT_CSV = PROJECT_ROOT / "data" / "youtube_monthly.csv"

QUERIES = ["vital farms", "pasture raised eggs"]
MAX_PER_MONTH = 50  # per query


def _client(api_key: str):
    from googleapiclient.discovery import build
    return build("youtube", "v3", developerKey=api_key, cache_discovery=False)


def _iso_month_windows(start: datetime, end: datetime):
    cur = start.replace(day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    while cur < end:
        nxt = (cur + timedelta(days=32)).replace(day=1)
        yield (
            cur.strftime("%Y-%m-%dT%H:%M:%SZ"),
            min(nxt, end).strftime("%Y-%m-%dT%H:%M:%SZ"),
            cur.strftime("%Y-%m"),
        )
        cur = nxt


def main() -> int:
    api_key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if not api_key:
        # Try loading from .env file if present
        env_path = PROJECT_ROOT / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("YOUTUBE_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break

    if not api_key:
        print("  [skip] YOUTUBE_API_KEY not set in env or .env — no-op exit (0).", file=sys.stderr)
        # Touch the output as an empty CSV so downstream code can degrade cleanly.
        OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=["month", "query", "video_count", "view_sum"]).to_csv(OUT_CSV, index=False)
        return 0

    try:
        from googleapiclient.errors import HttpError
    except ImportError:
        print("  [error] google-api-python-client not installed", file=sys.stderr)
        return 1

    yt = _client(api_key)

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=365 * 3)
    print(f"  fetching {len(QUERIES)} queries × 36mo windows (cap {MAX_PER_MONTH}/q/month)")

    # video_id -> {published, query, views}
    by_id: dict[str, dict] = {}
    per_query_cap = max(10, MAX_PER_MONTH // len(QUERIES))

    for query in QUERIES:
        for win_start, win_end, ym in _iso_month_windows(start, end):
            collected = 0
            page_token = None
            while collected < per_query_cap:
                try:
                    resp = yt.search().list(
                        part="id,snippet",
                        q=query,
                        type="video",
                        order="viewCount",
                        publishedAfter=win_start,
                        publishedBefore=win_end,
                        maxResults=min(50, per_query_cap - collected),
                        pageToken=page_token,
                    ).execute()
                except HttpError as exc:
                    print(f"  [warn] search.list failed for {query!r} {ym}: {exc}")
                    break
                items = resp.get("items", [])
                for it in items:
                    vid = it["id"].get("videoId")
                    if not vid or vid in by_id:
                        continue
                    by_id[vid] = {
                        "published": it["snippet"]["publishedAt"],
                        "query": query,
                    }
                collected += len(items)
                page_token = resp.get("nextPageToken")
                if not page_token:
                    break

    if not by_id:
        print("  no videos found", file=sys.stderr)
        OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=["month", "query", "video_count", "view_sum"]).to_csv(OUT_CSV, index=False)
        return 0

    # videos.list for view counts, batches of 50
    ids = list(by_id.keys())
    for i in range(0, len(ids), 50):
        batch = ids[i : i + 50]
        try:
            resp = yt.videos().list(part="statistics", id=",".join(batch)).execute()
        except HttpError as exc:
            print(f"  [warn] videos.list failed: {exc}")
            continue
        for it in resp.get("items", []):
            by_id[it["id"]]["views"] = int((it.get("statistics") or {}).get("viewCount") or 0)

    rows = []
    for vid, meta in by_id.items():
        rows.append({
            "published": meta["published"],
            "query": meta["query"],
            "views": meta.get("views", 0),
        })
    df = pd.DataFrame(rows)
    df["dt"] = pd.to_datetime(df["published"], utc=True)
    df["month"] = df["dt"].dt.strftime("%Y-%m")
    out = (
        df.groupby(["month", "query"])
        .agg(video_count=("views", "size"), view_sum=("views", "sum"))
        .reset_index()
        .sort_values(["month", "query"])
        .reset_index(drop=True)
    )

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    print(f"\n  ✓ wrote {OUT_CSV.name}  rows={len(out)}  unique_videos={len(by_id)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
