"""Shared Arctic Shift helper used by fetch_reddit_arctic.py and
fetch_competitor_mentions.py. Mirrors the pager / 45s wall-clock-deadline
pattern from social_intel_dashboard/lib/reddit.py exactly — title-only
matching, paginate by `after`, cap at 100 rows per page, 0.25s sleep
between pages, hard wall-clock deadline.

This file is private to scripts/ (underscore prefix). Don't import it
from the generator.
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Iterable

import pandas as pd
import requests

ARCTIC_BASE = "https://arctic-shift.photon-reddit.com/api/posts/search"
USER_AGENT = os.environ.get(
    "REDDIT_USER_AGENT", "vitl-demand-dashboard/1.0 (+research)"
)


def iso_to_epoch(d: str) -> int:
    return int(
        datetime.strptime(d, "%Y-%m-%d")
        .replace(tzinfo=timezone.utc)
        .timestamp()
    )


def fetch_one(
    sub: str,
    query: str,
    start_epoch: int,
    end_epoch: int,
    field: str = "title",
    max_pages: int = 40,
    deadline: float | None = None,
    page_sleep: float = 0.6,
) -> list[dict]:
    """Page through Arctic Shift /posts/search for one sub × one query.

    Returns a list of row dicts: {item_id, created_utc, subreddit, query}.
    Stops paging when:
      - exhausted (data < 100 returned or after >= end_epoch)
      - max_pages reached
      - wall-clock deadline exceeded

    On HTTP 429 (rate limit) the loop sleeps 5 seconds and retries the same
    page once; on a second 429 we bail out for this (sub, query) cleanly so
    the wider fetch doesn't grind to a halt.
    """
    rows: list[dict] = []
    after = start_epoch
    page = 0
    while after < end_epoch and page < max_pages:
        if deadline is not None and time.time() >= deadline:
            break
        params = {
            "subreddit": sub,
            field: query,
            "limit": 100,
            "after": after,
            "sort": "asc",
        }
        data = None
        for attempt in (1, 2):
            try:
                r = requests.get(
                    ARCTIC_BASE,
                    params=params,
                    headers={"User-Agent": USER_AGENT},
                    timeout=30,
                )
                if r.status_code == 429:
                    if attempt == 1:
                        time.sleep(5.0)
                        continue
                    print(f"  [warn] r/{sub} q={query!r} p{page}: 429 after retry — skipping")
                    break
                r.raise_for_status()
                data = r.json().get("data", [])
                break
            except requests.RequestException as exc:
                print(f"  [warn] r/{sub} q={query!r} p{page}: {exc}")
                data = None
                break
        if data is None:
            break
        if not data:
            break
        newest_ts = after
        for row in data:
            ts = int(row.get("created_utc") or row.get("created", 0))
            if ts >= end_epoch:
                continue
            rows.append({
                "item_id": row.get("id") or f"{sub}_{ts}",
                "created_utc": ts,
                "subreddit": row.get("subreddit", sub),
                "query": query,
            })
            newest_ts = max(newest_ts, ts)
        if len(data) < 100 or newest_ts <= after:
            break
        after = newest_ts + 1
        page += 1
        time.sleep(page_sleep)
    return rows


def weekly_counts(rows: list[dict]) -> pd.DataFrame:
    """Roll the row-level list into (week, subreddit, query, post_count)."""
    if not rows:
        return pd.DataFrame(columns=["week", "subreddit", "query", "post_count"])
    df = pd.DataFrame(rows).drop_duplicates(subset=["subreddit", "item_id"])
    df["dt"] = pd.to_datetime(df["created_utc"], unit="s", utc=True)
    df["week"] = df["dt"].dt.to_period("W-SUN").dt.end_time.dt.strftime("%Y-%m-%d")
    weekly = (
        df.groupby(["week", "subreddit", "query"])
        .size()
        .reset_index(name="post_count")
    )
    return weekly.sort_values(["week", "subreddit", "query"]).reset_index(drop=True)
