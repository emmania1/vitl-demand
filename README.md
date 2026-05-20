# Vital Farms (VITL) Recovery Dashboard

A self-updating demand-intelligence dashboard for VITL (NASDAQ: VITL), focused
on whether the company is **recovering** from the February 26, 2026 FY25 print
miss and the ERP-transition-driven shelf gap (class period May 8, 2025 →
Feb 26, 2026). Single Python generator → static `index.html` → hosted on
GitHub Pages.

**Live dashboard:** https://emmania1.github.io/vitl-demand/

## What it tracks

- **Recovery Scorecard** (Section 00) — ERP timeline, VITL stock vs class-period
  anchor, days-since-print + days-to-lead-plaintiff-deadline KPI cards
- **Community signal** — 15 food/health/value subreddits, title-only Reddit
  mention volume for `"vital farms"`, with 90d totals + YoY %
- **Brand share of voice** — six-brand pasture-raised egg set (Vital Farms,
  Handsome Brook, Alexandre, Pete & Gerry's, Happy Egg, Organic Valley),
  weekly Reddit mentions, stacked-area, with Feb 26 reference line
- **News coverage** — 24-month article cadence + topic mix from GDELT
  (primary) / Google News RSS (fallback). Topics: `erp_lawsuit / supply /
  launch / health / financial / culture`
- **Demand vs Stock** — 3-year VITL daily close + z-scored composite consumer
  demand (weekly Reddit + monthly YouTube views forward-filled) + event
  markers from financial / erp_lawsuit news

## Data pipeline

Each fetcher is a standalone, idempotent Python script in `scripts/`.
All outputs land in `data/` as CSVs.

| Fetcher                            | Source                                | Auth                | Output                                |
|------------------------------------|---------------------------------------|---------------------|---------------------------------------|
| `fetch_stock_price.py`             | yfinance (curl_cffi Chrome session)   | none                | `data/vitl_stock.csv`                 |
| `fetch_reddit_arctic.py`           | Arctic Shift public archive           | none                | `data/reddit_mentions_weekly.csv`     |
| `fetch_competitor_mentions.py`     | Arctic Shift (one query per brand)    | none                | `data/competitor_mentions_weekly.csv` |
| `fetch_google_news.py`             | GDELT ArtList → Google News RSS       | none                | `data/news_articles.csv`              |
| `fetch_youtube.py`                 | YouTube Data API v3                   | `YOUTUBE_API_KEY`   | `data/youtube_monthly.csv`            |

All Reddit fetchers honor a **45-second wall-clock deadline** (partial data
on timeout is fine — same pattern as `social_intel_dashboard/lib/reddit.py`).
The YouTube fetcher is the only one that needs credentials; it no-ops
cleanly (exit 0) when `YOUTUBE_API_KEY` is unset, so the Makefile chain
keeps moving.

## Setup

```bash
# 1. Create venv + install deps (curl_cffi pulls in a few binaries; takes ~30s)
make install

# 2. (Optional) Populate YouTube credentials
cp .env.example .env
# edit .env, add YOUTUBE_API_KEY=...

# 3. Refresh all data + regenerate dashboard
make refresh-data        # full pipeline incl. YouTube
make refresh-fast        # everything except YouTube
make generate            # regenerate index.html from existing CSVs only
```

## Re-deploying after a refresh

GitHub Pages serves whatever is committed on `main`. After regenerating:

```bash
git add data/ index.html
git commit -m "data: refresh $(date +%Y-%m-%d)"
git push
```

The live URL (https://emmania1.github.io/vitl-demand/) updates within ~30
seconds of the push.

## Project layout

```
vitl-demand/
├── config/
│   ├── products.csv               # 10 SKUs (eggs / butter / ghee / adjacencies)
│   ├── retailers.csv              # 12 banners
│   └── reddit_subreddits.csv      # 15 subs (food / health / value / Costco)
├── scripts/
│   ├── _arctic.py                 # shared Arctic Shift pager
│   ├── fetch_stock_price.py
│   ├── fetch_reddit_arctic.py
│   ├── fetch_competitor_mentions.py
│   ├── fetch_google_news.py
│   ├── fetch_youtube.py
│   └── generate_vitl_dashboard.py # builds index.html
├── data/                          # fetcher outputs (CSVs)
├── index.html                     # the dashboard
├── Makefile
├── requirements.txt
└── .env.example
```

## Pattern parity

This repo mirrors the architecture of two sibling projects:

- `social_intel_dashboard` — `lib/stock.py` (curl_cffi pattern),
  `lib/reddit.py` (Arctic Shift pager + 45s deadline), `lib/youtube.py`,
  `lib/news.py` (GDELT timeline pattern, extended here to ArtList for
  article-level rows).
- `crocs_demand` and `warhammer_demand` — single-Python-generator pattern,
  Chart.js, GitHub Pages hosting.

## Anchor dates (FY25 print disclosure, Feb 26 2026)

- Class period: **May 8, 2025 → Feb 26, 2026**
- Pre-print close (Feb 25): **$24.79**
- Print-day close (Feb 26): **$22.11** (−10.8%)
- Lead plaintiff deadline: **May 26, 2026**

These are baked into `generate_vitl_dashboard.py` and reconciled against
fetched data when present.
