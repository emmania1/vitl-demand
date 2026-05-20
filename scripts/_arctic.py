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

ARCTIC_BASE     = "https://arctic-shift.photon-reddit.com/api/posts/search"
ARCTIC_COMMENTS = "https://arctic-shift.photon-reddit.com/api/comments/search"
USER_AGENT = os.environ.get(
    "REDDIT_USER_AGENT", "vitl-demand-dashboard/1.0 (+research)"
)

# Author allowlist filter — Arctic Shift returns `author` so we drop the
# obvious bot accounts. Lowercased comparison; substring match against
# `*bot*`/`*Bot*` would over-match real users (e.g. Robotnik), so we keep
# an explicit list of the common Reddit moderation/utility bots.
BOT_AUTHORS = {
    "automoderator", "remindmebot", "reminddebot", "savevideo",
    "videoinurl", "transcriberbot", "wikitextbot", "imagesofnetwork",
    "good_bot_bot", "haikubotinator", "removalbot", "of_patrol_bot",
    "stabbot", "user_simulator", "redditcomplaintsbot", "[deleted]",
}


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
    endpoint: str = ARCTIC_BASE,
) -> list[dict]:
    """Page through Arctic Shift /posts/search OR /comments/search.

    `endpoint` switches between posts (ARCTIC_BASE) and comments (ARCTIC_COMMENTS).
    For comments, pass field="body" instead of field="title".

    Returns rows with as much metadata as Arctic Shift returns: item_id,
    created_utc, subreddit, query, kind ("post"|"comment"), author, body.
    (body and author may be None when Arctic Shift omits them.)

    Stops paging when:
      - exhausted (data < 100 returned or after >= end_epoch)
      - max_pages reached
      - wall-clock deadline exceeded

    On HTTP 429: sleep 5s, retry once; on second 429 bail for this
    (sub, query, endpoint) so the wider fetch doesn't grind to a halt.
    """
    kind = "comment" if endpoint == ARCTIC_COMMENTS else "post"
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
                    endpoint,
                    params=params,
                    headers={"User-Agent": USER_AGENT},
                    timeout=30,
                )
                # Arctic Shift uses 422 for "server-side timeout, slow down".
                # Treat 422 + 429 identically: one retry with backoff, then skip.
                if r.status_code in (422, 429):
                    if attempt == 1:
                        time.sleep(5.0)
                        continue
                    print(f"  [warn] r/{sub} q={query!r} {kind} p{page}: {r.status_code} after retry — skipping")
                    break
                r.raise_for_status()
                data = r.json().get("data", [])
                break
            except requests.RequestException as exc:
                print(f"  [warn] r/{sub} q={query!r} {kind} p{page}: {exc}")
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
                "item_id": row.get("id") or f"{sub}_{ts}_{kind}",
                "created_utc": ts,
                "subreddit": row.get("subreddit", sub),
                "query": query,
                "kind": kind,
                "author": (row.get("author") or "").lower(),
                "body": row.get("body") if kind == "comment" else row.get("selftext"),
            })
            newest_ts = max(newest_ts, ts)
        if len(data) < 100 or newest_ts <= after:
            break
        after = newest_ts + 1
        page += 1
        time.sleep(page_sleep)
    return rows


def apply_filters(rows: list[dict], min_body_chars: int = 30,
                  word_boundary_query: str | None = None) -> list[dict]:
    """Apply the standard noise filters to a row list:
      - Drop authors in BOT_AUTHORS
      - Drop comments whose body is present AND shorter than `min_body_chars`
      - If `word_boundary_query` is given AND body is present, require a
        \\b{query}\\b match (case-insensitive).
    Rows where body is None (Arctic Shift didn't return text) pass through —
    server-side substring on the original `field` already enforced relevance.
    """
    import re as _re
    out = []
    wb_re = None
    if word_boundary_query:
        wb_re = _re.compile(rf"\b{_re.escape(word_boundary_query)}\b", _re.IGNORECASE)
    for r in rows:
        if (r.get("author") or "").lower() in BOT_AUTHORS:
            continue
        body = r.get("body")
        if body is not None:
            if len(str(body).strip()) < min_body_chars:
                continue
            if wb_re and not wb_re.search(str(body)):
                continue
        out.append(r)
    return out


def weekly_counts(rows: list[dict]) -> pd.DataFrame:
    """Roll the row-level list into (week, subreddit, query, post_count).
    Dedupe on (subreddit, item_id, kind) so a post and a comment with the
    same id (rare but possible across endpoints) don't collapse."""
    if not rows:
        return pd.DataFrame(columns=["week", "subreddit", "query", "post_count"])
    df = pd.DataFrame(rows)
    if "kind" not in df.columns:
        df["kind"] = "post"
    df = df.drop_duplicates(subset=["subreddit", "item_id", "kind"])
    df["dt"] = pd.to_datetime(df["created_utc"], unit="s", utc=True)
    df["week"] = df["dt"].dt.to_period("W-SUN").dt.end_time.dt.strftime("%Y-%m-%d")
    weekly = (
        df.groupby(["week", "subreddit", "query"])
        .size()
        .reset_index(name="post_count")
    )
    return weekly.sort_values(["week", "subreddit", "query"]).reset_index(drop=True)
