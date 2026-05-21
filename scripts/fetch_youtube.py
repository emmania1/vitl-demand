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
OUT_CSV             = PROJECT_ROOT / "data" / "youtube_monthly.csv"
LINOLEIC_OUT_CSV    = PROJECT_ROOT / "data" / "youtube_linoleic_monthly.csv"
COMPETITORS_OUT_CSV = PROJECT_ROOT / "data" / "youtube_competitors_monthly.csv"
RECENT_VIDEOS_CSV   = PROJECT_ROOT / "data" / "youtube_recent_videos.csv"

# Filled by _run_query_set() each pass; main() reads it to write recent-videos feed.
_last_video_detail = pd.DataFrame()

QUERIES = ["vital farms", "pasture raised eggs"]
# Linoleic / seed-oil controversy decay query set. YouTube AND-search via
# space-separated terms, so each entry is "vital farms <keyword>". Union by
# video ID, monthly, 18-month window per task spec.
LINOLEIC_QUERIES = [
    "vital farms linoleic",
    "vital farms PUFA",
    "vital farms seed oil",
]
# Per-brand competitor query set for the new YouTube competitor multi-line
# chart in Section 01B. One query per brand; monthly aggregates over 36mo.
COMPETITOR_BRANDS = [
    "vital farms",
    "handsome brook",
    "alexandre family farm",
    "pete and gerry's",
    "happy egg",
    "organic valley",
]
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


def _load_api_key() -> str:
    api_key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if api_key: return api_key
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("YOUTUBE_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _run_query_set(yt, queries: list[str], start: datetime, end: datetime,
                   max_per_month: int, label: str) -> pd.DataFrame:
    """Return per-(month, query) aggregate. Empty df if quota fails entire run."""
    try:
        from googleapiclient.errors import HttpError
    except ImportError:
        print("  [error] google-api-python-client not installed", file=sys.stderr)
        return pd.DataFrame(columns=["month", "query", "video_count", "view_sum"])

    by_id: dict[str, dict] = {}
    per_query_cap = max(10, max_per_month // max(1, len(queries)))

    for query in queries:
        for win_start, win_end, ym in _iso_month_windows(start, end):
            collected = 0
            page_token = None
            while collected < per_query_cap:
                try:
                    resp = yt.search().list(
                        part="id,snippet", q=query, type="video",
                        order="viewCount",
                        publishedAfter=win_start, publishedBefore=win_end,
                        maxResults=min(50, per_query_cap - collected),
                        pageToken=page_token,
                    ).execute()
                except HttpError as exc:
                    # Quota / 403 — log once per query+month then move on
                    msg = str(exc)[:120]
                    if "quotaExceeded" in str(exc):
                        print(f"  [quota] {label} {query!r} {ym}: quota exhausted")
                    else:
                        print(f"  [warn] {label} search {query!r} {ym}: {msg}")
                    break
                items = resp.get("items", [])
                for it in items:
                    vid = it["id"].get("videoId")
                    if not vid or vid in by_id: continue
                    sn = it.get("snippet", {})
                    by_id[vid] = {
                        "published": sn.get("publishedAt", ""),
                        "query": query,
                        "title": (sn.get("title") or "").strip(),
                        "channel": (sn.get("channelTitle") or "").strip(),
                        "description": (sn.get("description") or "")[:280].strip(),
                    }
                collected += len(items)
                page_token = resp.get("nextPageToken")
                if not page_token: break

    if not by_id:
        return pd.DataFrame(columns=["month", "query", "video_count", "view_sum"])

    # videos.list for view counts, batches of 50
    ids = list(by_id.keys())
    for i in range(0, len(ids), 50):
        batch = ids[i:i + 50]
        try:
            resp = yt.videos().list(part="statistics", id=",".join(batch)).execute()
        except HttpError as exc:
            if "quotaExceeded" in str(exc):
                print(f"  [quota] {label} videos.list: quota exhausted (counts only, no views)")
            else:
                print(f"  [warn] {label} videos.list: {str(exc)[:120]}")
            continue
        for it in resp.get("items", []):
            by_id[it["id"]]["views"] = int((it.get("statistics") or {}).get("viewCount") or 0)

    rows = []
    for vid, m in by_id.items():
        rows.append({
            "video_id":    vid,
            "published":   m["published"],
            "query":       m["query"],
            "title":       m.get("title", ""),
            "channel":     m.get("channel", ""),
            "description": m.get("description", ""),
            "views":       m.get("views", 0),
            "url":         f"https://www.youtube.com/watch?v={vid}",
        })
    df = pd.DataFrame(rows)
    df["dt"] = pd.to_datetime(df["published"], utc=True)
    df["month"] = df["dt"].dt.strftime("%Y-%m")
    # Stash the per-video detail for the recent-videos feed on the dashboard.
    # _last_video_detail is read by main() after each query set returns.
    global _last_video_detail
    _last_video_detail = df.sort_values("dt", ascending=False).copy()
    out = (
        df.groupby(["month", "query"])
          .agg(video_count=("views", "size"), view_sum=("views", "sum"))
          .reset_index().sort_values(["month", "query"]).reset_index(drop=True)
    )
    return out


def main() -> int:
    api_key = _load_api_key()
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    if not api_key:
        print("  [skip] YOUTUBE_API_KEY not set — no-op exit (0)", file=sys.stderr)
        for p in (OUT_CSV, LINOLEIC_OUT_CSV):
            if not p.exists():
                pd.DataFrame(columns=["month","query","video_count","view_sum"]).to_csv(p, index=False)
        return 0

    yt = _client(api_key)
    end = datetime.now(timezone.utc)

    all_video_details = []  # accumulate per-video metadata across all passes

    # General — 36mo window
    print(f"  ── general pass: {len(QUERIES)} queries × 36mo ──")
    general_df = _run_query_set(yt, QUERIES, end - timedelta(days=365*3), end, MAX_PER_MONTH, "general")
    if not _last_video_detail.empty:
        general_videos = _last_video_detail.copy()
        general_videos["pass"] = "general"
        all_video_details.append(general_videos)
    if not general_df.empty:
        general_df.to_csv(OUT_CSV, index=False)
        print(f"  ✓ wrote {OUT_CSV.name}  rows={len(general_df)}  "
              f"video_total={int(general_df['video_count'].sum())}  "
              f"view_total={int(general_df['view_sum'].sum()):,}")
    else:
        print(f"  · {OUT_CSV.name} preserved (general fetch empty; likely quota)")

    # Linoleic / seed-oil — 18mo window, separate output
    print(f"\n  ── linoleic pass: {len(LINOLEIC_QUERIES)} queries × 18mo ──")
    lin_df = _run_query_set(yt, LINOLEIC_QUERIES,
                            end - timedelta(days=365 + 180), end,
                            max_per_month=30, label="linoleic")
    if not lin_df.empty:
        # Roll to month totals so chart consumer doesn't have to split by query
        lin_monthly = (lin_df.groupby("month")
                       .agg(video_count=("video_count","sum"), view_sum=("view_sum","sum"))
                       .reset_index().sort_values("month").reset_index(drop=True))
        lin_monthly.to_csv(LINOLEIC_OUT_CSV, index=False)
        print(f"  ✓ wrote {LINOLEIC_OUT_CSV.name}  rows={len(lin_monthly)}  "
              f"video_total={int(lin_monthly['video_count'].sum())}  "
              f"view_total={int(lin_monthly['view_sum'].sum()):,}")
    else:
        print(f"  · {LINOLEIC_OUT_CSV.name} preserved (linoleic fetch empty; likely quota)")
        if not LINOLEIC_OUT_CSV.exists():
            pd.DataFrame(columns=["month","video_count","view_sum"]).to_csv(LINOLEIC_OUT_CSV, index=False)

    if not _last_video_detail.empty:
        lin_videos = _last_video_detail.copy()
        lin_videos["pass"] = "linoleic"
        all_video_details.append(lin_videos)

    # Competitor brands — 36mo window, separate output
    print(f"\n  ── competitor pass: {len(COMPETITOR_BRANDS)} brands × 36mo ──")
    comp_df = _run_query_set(yt, COMPETITOR_BRANDS,
                             end - timedelta(days=365*3), end,
                             max_per_month=20, label="competitor")
    if not _last_video_detail.empty:
        comp_videos = _last_video_detail.copy()
        comp_videos["pass"] = "competitor"
        all_video_details.append(comp_videos)
    if not comp_df.empty:
        # Tag each row with the brand it came from (use query as brand label)
        comp_df = comp_df.rename(columns={"query": "brand"})
        comp_df = (comp_df.groupby(["month", "brand"])
                   .agg(video_count=("video_count","sum"), view_sum=("view_sum","sum"))
                   .reset_index().sort_values(["month","brand"]).reset_index(drop=True))
        comp_df.to_csv(COMPETITORS_OUT_CSV, index=False)
        print(f"  ✓ wrote {COMPETITORS_OUT_CSV.name}  rows={len(comp_df)}  "
              f"unique_brands={comp_df['brand'].nunique()}")
    else:
        print(f"  · {COMPETITORS_OUT_CSV.name} preserved (competitor fetch empty; likely quota)")
        if not COMPETITORS_OUT_CSV.exists():
            pd.DataFrame(columns=["month","brand","video_count","view_sum"]).to_csv(COMPETITORS_OUT_CSV, index=False)

    # ── Recent-videos feed (titles + channels + URLs) ────────────────────
    # Concatenate all per-video metadata across passes, dedupe by video_id,
    # write the latest 50 sorted by published date. This is what the
    # dashboard renders as the "Recent VITL Videos" feed.
    if all_video_details:
        all_v = pd.concat(all_video_details, ignore_index=True)
        all_v = all_v.drop_duplicates(subset=["video_id"]).sort_values("dt", ascending=False)
        out_cols = ["video_id", "published", "title", "channel", "description",
                    "views", "url", "query", "pass"]
        all_v[out_cols].head(50).to_csv(RECENT_VIDEOS_CSV, index=False)
        print(f"  ✓ wrote {RECENT_VIDEOS_CSV.name}  rows={min(50, len(all_v))}  (most-recent VITL videos)")
    else:
        if not RECENT_VIDEOS_CSV.exists():
            pd.DataFrame(columns=["video_id","published","title","channel","description","views","url","query","pass"]).to_csv(RECENT_VIDEOS_CSV, index=False)

    return 0


if __name__ == "__main__":
    sys.exit(main())
