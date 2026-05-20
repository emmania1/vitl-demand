"""
Vital Farms Demand Intelligence Dashboard — v2 (ERP recovery anchor + wired fetchers)

Sections (rendered top → bottom, most → least substantial):
  00. RECOVERY SCORECARD   — ERP-print anchor: timeline, stock chart, KPI cards
  01. OVERVIEW             — hero tiles + 24-month composite demand trajectory
  02. RETAIL DISTRIBUTION  — store count, % ACV, SKU breadth, OOS (placeholder)
  03. PRODUCT LINE HEAT    — per-SKU signal (placeholder)
  04. COMMUNITY & SOCIAL   — Reddit table (real) + Brand Share of Voice (real)
  05. NEWS COVERAGE        — cadence + topic mix + publishers (real, GDELT/RSS)
  06. PRICING POWER        — placeholder (Instacart scrape pending)
  07. SUPPLY RISK MONITOR  — placeholder (USDA + APHIS pending)
  08. DEMAND vs STOCK      — VITL close + composite demand + event markers (real)

Reads (all optional — missing files degrade gracefully):
  config/products.csv, config/retailers.csv, config/reddit_subreddits.csv
  data/vitl_stock.csv                         ← fetch_stock_price.py
  data/reddit_mentions_weekly.csv             ← fetch_reddit_arctic.py
  data/competitor_mentions_weekly.csv         ← fetch_competitor_mentions.py
  data/youtube_monthly.csv                    ← fetch_youtube.py
  data/news_articles.csv                      ← fetch_google_news.py
"""
import json
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR     = PROJECT_ROOT / "data"
CONFIG_DIR   = PROJECT_ROOT / "config"
OUTPUT_HTML  = PROJECT_ROOT / "index.html"

BRAND_NAME    = "Vital Farms"
BRAND_TICKER  = "VITL"
BRAND_ACCENT  = "#2E5A3C"   # Vital Farms forest green
BRAND_ACCENT2 = "#F4C430"   # egg-yolk yellow
BRAND_ACCENT3 = "#A8C49B"   # pasture light green
BRAND_ACCENT4 = "#C95D4A"   # warm terracotta (negative / risk)

# Anchor dates baked from the Feb 26, 2026 print disclosure
ERP_PRINT_DATE    = datetime(2026, 2, 26).date()
ERP_PRINT_CLOSE   = 22.11  # close on print day; verified against fetched data if available
PRE_PRINT_CLOSE   = 24.79  # close 2026-02-25
CLASS_PERIOD_START = "2025-05-08"
CLASS_PERIOD_END   = "2026-02-26"
LP_DEADLINE_DATE  = datetime(2026, 5, 26).date()

# Markers for the Section 00 ERP timeline strip. `kind` controls colour:
#   phase  → grey dot;   anchor → red dot;   today → green dot
ERP_EVENTS = [
    {"date": "2025-05-08", "kind": "phase",  "label": "Class period begins",
     "sub": "Q1 '25 call: ERP delay disclosed"},
    {"date": "2025-07-15", "kind": "phase",  "label": "Summer ERP go-live target",
     "sub": "Original timeline"},
    {"date": "2025-10-15", "kind": "phase",  "label": "Revised ERP go-live",
     "sub": "Early-fall target per Q1 call"},
    {"date": "2025-11-13", "kind": "phase",  "label": "Q3 call: guidance ≥$775M",
     "sub": "Set up the Feb 26 miss"},
    {"date": "2026-02-26", "kind": "anchor", "label": "FY25 print misses",
     "sub": "$759.4M vs ≥$775M · EPS $0.35 vs $0.39 · stock −10.8% · class period ends"},
    {"date": "2026-04-15", "kind": "phase",  "label": "Class actions filed",
     "sub": "Lead plaintiff deadline May 26, 2026"},
    {"date": str(datetime.today().date()), "kind": "today", "label": "Today",
     "sub": ""},
]

LINE_COLORS = {
    "eggs":   BRAND_ACCENT,
    "butter": BRAND_ACCENT2,
    "ghee":   "#B5651D",
    "new":    "#8e6db4",
}
LINE_LABELS = {
    "eggs":   "Eggs",
    "butter": "Butter",
    "ghee":   "Ghee",
    "new":    "New / Adjacent",
}
CHANNEL_COLORS = {
    "natural": BRAND_ACCENT,
    "grocery": "#6b94b1",
    "mass":    BRAND_ACCENT2,
    "club":    "#8e6db4",
    "ecom":    "#e67e22",
}
TOPIC_COLORS = {
    "erp_lawsuit": "#7d3c4a",
    "supply":      BRAND_ACCENT4,
    "launch":      BRAND_ACCENT,
    "health":      BRAND_ACCENT3,
    "financial":   "#e67e22",
    "culture":     "#e84393",
    "other":       "#8b8b78",
}
TOPIC_LABELS = {
    "erp_lawsuit": "ERP / Lawsuit",
    "supply":      "Supply / Avian Flu",
    "launch":      "Launch / Distribution",
    "health":      "Health / Ethical",
    "financial":   "Financial",
    "culture":     "Culture / Recipe",
    "other":       "Other",
}
# Brand colors for the share-of-voice stacked area chart in Section 04
BRAND_SOV_COLORS = {
    "Vital Farms":    BRAND_ACCENT,
    "Handsome Brook": "#8e6db4",
    "Alexandre":      "#e67e22",
    "Pete & Gerry's": "#6b94b1",
    "Happy Egg":      BRAND_ACCENT2,
    "Organic Valley": "#B5651D",
}


# ─────────────────────────────────────────────────────────────────────────────
# Loading
# ─────────────────────────────────────────────────────────────────────────────
def safe_read(path: Path) -> pd.DataFrame:
    if path.exists():
        try: return pd.read_csv(path)
        except Exception as e: print(f"  [warn] {path.name}: {e}")
    return pd.DataFrame()


def load_all() -> dict:
    return {
        "products":           safe_read(CONFIG_DIR / "products.csv"),
        "retailers":          safe_read(CONFIG_DIR / "retailers.csv"),
        "subs":               safe_read(CONFIG_DIR / "reddit_subreddits.csv"),
        "stock":              safe_read(DATA_DIR / "vitl_stock.csv"),
        "reddit_weekly":      safe_read(DATA_DIR / "reddit_mentions_weekly.csv"),
        "competitor_weekly":  safe_read(DATA_DIR / "competitor_mentions_weekly.csv"),
        "youtube_monthly":    safe_read(DATA_DIR / "youtube_monthly.csv"),
        "news":               safe_read(DATA_DIR / "news_articles.csv"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Compute layer
# ─────────────────────────────────────────────────────────────────────────────
def _close_on(stock: pd.DataFrame, date_str: str) -> float | None:
    if stock.empty: return None
    m = stock[stock["date"].astype(str) == date_str]
    if m.empty: return None
    try: return float(m.iloc[0]["close"])
    except (KeyError, ValueError): return None


def compute_recovery(d: dict) -> dict:
    """Section 00 data: ERP timeline + stock series for the post-2025-01 window
    + four KPI cards. Real values where stock CSV exists; fallback constants
    from the print disclosure when not."""
    stock = d["stock"].copy()
    today = datetime.today().date()
    days_since_print = (today - ERP_PRINT_DATE).days
    days_to_deadline = (LP_DEADLINE_DATE - today).days

    if stock.empty:
        return {
            "events": ERP_EVENTS,
            "today_iso": str(today),
            "class_period_start": CLASS_PERIOD_START,
            "class_period_end": CLASS_PERIOD_END,
            "stock_series": {"dates": [], "close": []},
            "kpis": {
                "days_since_print": days_since_print,
                "days_to_deadline": days_to_deadline,
                "current_price": None,
                "feb25_close": PRE_PRINT_CLOSE,
                "feb26_close": ERP_PRINT_CLOSE,
                "vs_feb25_pct": None,
                "vs_feb26_pct": None,
            },
        }

    stock["date"] = pd.to_datetime(stock["date"]).dt.strftime("%Y-%m-%d")
    stock = stock.sort_values("date").reset_index(drop=True)
    chart = stock[stock["date"] >= "2025-01-01"]

    feb25 = _close_on(stock, "2026-02-25") or PRE_PRINT_CLOSE
    feb26 = _close_on(stock, "2026-02-26") or ERP_PRINT_CLOSE
    current = float(stock.iloc[-1]["close"])

    return {
        "events": ERP_EVENTS,
        "today_iso": str(today),
        "class_period_start": CLASS_PERIOD_START,
        "class_period_end": CLASS_PERIOD_END,
        "stock_series": {
            "dates": chart["date"].tolist(),
            "close": chart["close"].astype(float).round(2).tolist(),
        },
        "kpis": {
            "days_since_print": days_since_print,
            "days_to_deadline": days_to_deadline,
            "current_price": round(current, 2),
            "feb25_close": round(feb25, 2),
            "feb26_close": round(feb26, 2),
            "vs_feb25_pct": round((current / feb25 - 1) * 100, 1) if feb25 else None,
            "vs_feb26_pct": round((current / feb26 - 1) * 100, 1) if feb26 else None,
        },
    }


def compute_trajectory(d: dict) -> dict:
    """Section 01 (Overview) 24-month chart — still placeholder. Replaced once
    the per-line breakdown is split out of the unified Reddit mention pull."""
    months = pd.date_range(end=datetime.today(), periods=24, freq="MS").strftime("%Y-%m").tolist()
    eggs   = [100 + i * 1.8 + (12 if i in (10, 11, 12) else 0) for i in range(24)]
    butter = [40 + i * 1.2 for i in range(24)]
    ghee   = [15 + i * 0.6 for i in range(24)]
    return {
        "months": months,
        "eggs":   [round(x, 1) for x in eggs],
        "butter": [round(x, 1) for x in butter],
        "ghee":   [round(x, 1) for x in ghee],
    }


def compute_hero(d: dict, traj: dict) -> dict:
    products = d["products"]
    retailers = d["retailers"]
    sku_count = len(products) if not products.empty else 0
    retail_targets = len(retailers) if not retailers.empty else 0
    yoy_eggs = round((traj["eggs"][-1] / traj["eggs"][-13] - 1) * 100, 1) if traj["eggs"][-13] else 0
    return {
        "sku_count": sku_count,
        "retail_targets": retail_targets,
        "yoy_composite": yoy_eggs,
        "data_lag_days": 1,
    }


def compute_retail(d: dict) -> dict:
    """Section 02 — unchanged placeholder per task spec (Instacart proxy pending)."""
    retailers = d["retailers"]
    if retailers.empty: return {"rows": []}
    placeholder_acv = {
        "whole_foods": 100, "sprouts": 100, "target": 78, "kroger": 62,
        "walmart": 41, "costco": 18, "publix": 55, "trader_joes": 0,
        "heb": 47, "wegmans": 82, "amazon_fresh": 90, "instacart": 95,
    }
    placeholder_skus = {
        "whole_foods": 9, "sprouts": 8, "target": 5, "kroger": 6,
        "walmart": 3, "costco": 2, "publix": 4, "trader_joes": 0,
        "heb": 4, "wegmans": 7, "amazon_fresh": 8, "instacart": 9,
    }
    rows = []
    for _, r in retailers.iterrows():
        rows.append({
            "key": r["key"], "name": r["display_name"],
            "channel": r["channel"], "priority": r["priority"],
            "pct_acv": placeholder_acv.get(r["key"], 0),
            "skus":    placeholder_skus.get(r["key"], 0),
            "oos_pct": 0,
            "notes":   r.get("notes", "") if "notes" in r else "",
        })
    return {"rows": rows}


def compute_product_heat(d: dict) -> dict:
    """Section 03 — unchanged placeholder per task spec."""
    products = d["products"]
    if products.empty: return {"rows": []}
    rows = []
    for _, p in products.iterrows():
        rows.append({
            "key": p["key"], "name": p["display_name"], "line": p["line"],
            "priority": p["priority"], "launch_year": p["launch_year"],
            "reddit_yoy": None, "youtube_yoy": None, "search_yoy": None,
            "notes": p.get("notes", "") if "notes" in p else "",
        })
    return {"rows": rows}


def compute_community(d: dict) -> dict:
    """Section 04 — real Reddit data + brand share of voice."""
    subs = d["subs"]
    reddit_weekly = d["reddit_weekly"]
    competitor_weekly = d["competitor_weekly"]

    if subs.empty:
        return {"sub_rows": [], "brand_sov": {"weeks": [], "brands": {}}, "totals": {}}

    today = datetime.today()
    d90  = (today - timedelta(days=90)).strftime("%Y-%m-%d")
    d365 = (today - timedelta(days=365)).strftime("%Y-%m-%d")
    d455 = (today - timedelta(days=455)).strftime("%Y-%m-%d")

    sub_rows = []
    for _, r in subs.iterrows():
        sub_name = str(r["subreddit"])
        mentions_90d, yoy_pct = None, None
        if not reddit_weekly.empty:
            sub_data = reddit_weekly[reddit_weekly["subreddit"].astype(str).str.lower() == sub_name.lower()]
            if not sub_data.empty:
                week_col = sub_data["week"].astype(str)
                curr = int(sub_data.loc[week_col >= d90, "post_count"].sum())
                prev = int(sub_data.loc[(week_col >= d455) & (week_col < d365), "post_count"].sum())
                mentions_90d = curr
                yoy_pct = round((curr / prev - 1) * 100, 1) if prev > 0 else None
        sub_rows.append({
            "subreddit": sub_name,
            "topic": r["topic"],
            "priority": r["priority"],
            "mentions_90d": mentions_90d,
            "yoy_pct": yoy_pct,
        })

    # Brand share of voice — weekly stacked
    brand_sov = {"weeks": [], "brands": {}}
    totals = {}
    if not competitor_weekly.empty:
        cw = competitor_weekly.copy()
        cw["week"] = cw["week"].astype(str)
        weeks = sorted(cw["week"].unique().tolist())
        brand_sov["weeks"] = weeks
        for brand in cw["brand"].unique():
            b = cw[cw["brand"] == brand].set_index("week")["post_count"].reindex(weeks, fill_value=0)
            brand_sov["brands"][str(brand)] = b.astype(int).tolist()
            totals[str(brand)] = int(b.sum())

    return {"sub_rows": sub_rows, "brand_sov": brand_sov, "totals": totals}


def compute_news(d: dict) -> dict:
    """Section 05 — real news articles → weekly cadence + topic mix + publishers."""
    news = d["news"]
    if news.empty:
        return {"cadence": {"weeks": [], "counts": []}, "topics": {}, "publishers": [], "total": 0}

    n = news.copy()
    n["date"] = pd.to_datetime(n["date"], errors="coerce")
    n = n.dropna(subset=["date"]).copy()
    n["week"] = n["date"].dt.to_period("W-SUN").dt.end_time.dt.strftime("%Y-%m-%d")

    cadence_df = n.groupby("week").size().reset_index(name="count").sort_values("week")
    cadence = {
        "weeks":  cadence_df["week"].tolist(),
        "counts": cadence_df["count"].astype(int).tolist(),
    }

    topics = {k: int(v) for k, v in n["topic"].value_counts().items()}
    pubs = n["source"].fillna("").astype(str).value_counts().head(12)
    publishers = [{"source": k, "count": int(v)} for k, v in pubs.items() if k]

    return {"cadence": cadence, "topics": topics, "publishers": publishers, "total": int(len(n))}


def compute_stock_panel(d: dict) -> dict:
    """Section 08 — VITL daily close + composite demand z-score + event markers."""
    stock = d["stock"]
    reddit_weekly = d["reddit_weekly"]
    youtube_monthly = d["youtube_monthly"]
    news = d["news"]

    if stock.empty:
        return {
            "dates": [], "close": [],
            "demand_dates": [], "demand_z": [],
            "events": [],
            "class_period_start": CLASS_PERIOD_START,
            "class_period_end": CLASS_PERIOD_END,
        }

    s = stock.copy()
    s["date"] = pd.to_datetime(s["date"]).dt.strftime("%Y-%m-%d")
    s = s.sort_values("date").reset_index(drop=True)
    cutoff = (datetime.today() - timedelta(days=365 * 3)).strftime("%Y-%m-%d")
    s = s[s["date"] >= cutoff]

    # Composite demand: weekly Reddit (all subs) + monthly YouTube views resampled to weekly
    weekly = pd.DataFrame()
    if not reddit_weekly.empty:
        r = reddit_weekly.groupby("week")["post_count"].sum().reset_index()
        r["week"] = r["week"].astype(str)
        weekly = r.rename(columns={"post_count": "reddit"})

    if not youtube_monthly.empty:
        ym = youtube_monthly.groupby("month")["view_sum"].sum().reset_index()
        try:
            ym["month_start"] = pd.to_datetime(ym["month"], format="%Y-%m")
            expanded = []
            for _, row in ym.iterrows():
                # spread monthly views over 4 weeks ending in that month
                for i in range(4):
                    wk_dt = (row["month_start"] + pd.Timedelta(days=i * 7))
                    wk_str = wk_dt.to_period("W-SUN").end_time.strftime("%Y-%m-%d")
                    expanded.append({"week": wk_str, "youtube": row["view_sum"] / 4.0})
            ym_df = pd.DataFrame(expanded).groupby("week")["youtube"].sum().reset_index()
            if weekly.empty:
                weekly = ym_df
            else:
                weekly = weekly.merge(ym_df, on="week", how="outer").fillna(0)
        except Exception as exc:  # noqa: BLE001
            print(f"  [warn] youtube monthly→weekly expansion failed: {exc}")

    demand_dates, demand_z = [], []
    if not weekly.empty and len(weekly) > 5:
        weekly = weekly.sort_values("week").reset_index(drop=True)
        z_total = pd.Series(0.0, index=weekly.index)
        for col in ("reddit", "youtube"):
            if col in weekly.columns:
                v = weekly[col].astype(float)
                std = v.std()
                if std > 0:
                    z_total = z_total + (v - v.mean()) / std
        weekly["z"] = z_total
        demand_dates = weekly["week"].tolist()
        demand_z = weekly["z"].round(3).tolist()

    # Event markers — financial + erp_lawsuit news, dedup by (date, headline), limit recent 40
    events = []
    if not news.empty:
        e = news[news["topic"].isin(["financial", "erp_lawsuit"])].copy()
        if not e.empty:
            e["date"] = pd.to_datetime(e["date"], errors="coerce").dt.strftime("%Y-%m-%d")
            e = e.drop_duplicates(subset=["date", "headline"]).sort_values("date").tail(40)
            for _, row in e.iterrows():
                events.append({
                    "date": row["date"],
                    "headline": str(row.get("headline", ""))[:120],
                    "topic": row.get("topic", "other"),
                    "url": str(row.get("url", "")),
                })

    return {
        "dates": s["date"].tolist(),
        "close": s["close"].astype(float).round(2).tolist(),
        "demand_dates": demand_dates,
        "demand_z": demand_z,
        "events": events,
        "class_period_start": CLASS_PERIOD_START,
        "class_period_end": CLASS_PERIOD_END,
    }


def compute_summary(d, hero, news, recovery) -> dict:
    """Auto-narrative for the modal. Reads computed metrics; degrades when missing."""
    kpis = recovery["kpis"]
    vs_print = kpis.get("vs_feb26_pct")
    bullets = [
        (f"Days since FY25 ERP-print miss: <strong>{kpis['days_since_print']}</strong> "
         f"(Feb 26, 2026)."),
        (f"VITL vs Feb 26 close: <strong>{vs_print:+.1f}%</strong>." if vs_print is not None
         else "VITL vs Feb 26 close: <strong>—</strong> (stock fetcher not yet run)."),
        f"Days to lead-plaintiff deadline (May 26, 2026): <strong>{kpis['days_to_deadline']}</strong>.",
        f"News articles tracked: <strong>{news.get('total', 0)}</strong> (GDELT + Google News RSS).",
        f"SKU universe: <strong>{hero['sku_count']}</strong>; retail banners monitored: <strong>{hero['retail_targets']}</strong>.",
    ]
    return {
        "headline": f"{BRAND_NAME} ({BRAND_TICKER}) — Recovery Signal Dashboard",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "bullets": bullets,
        "to_do_next": [
            "Instacart proxy for retail % ACV (Section 02) — unblocks the shelf-recovery test.",
            "USDA AMS wholesale-egg + APHIS HPAI feed (Section 07).",
            "Per-SKU Reddit/YouTube split for Section 03 SKU Heat Map.",
            "Pete &amp; Gerry's organic-only price spread at Whole Foods + Sprouts (Section 06).",
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Render helpers
# ─────────────────────────────────────────────────────────────────────────────
def fmt_num(v, default="—"):
    if v is None or (isinstance(v, float) and pd.isna(v)): return default
    if isinstance(v, (int, float)) and abs(v) >= 1000: return f"{int(v):,}"
    return str(v)


def fmt_pct(v, default="—"):
    if v is None or (isinstance(v, float) and pd.isna(v)): return default
    return f"{v:+.1f}%"


def source_caption(text: str) -> str:
    return f'<div class="source-caption">{text}</div>'


# Section 00 ─────────────────────────────────────────────────────────────────
def render_recovery(rec: dict) -> str:
    kpis = rec["kpis"]
    events = rec["events"]

    # ERP timeline strip — dots positioned by time-fraction across the strip
    dates = [datetime.strptime(e["date"], "%Y-%m-%d") for e in events]
    start, end = dates[0], dates[-1]
    span = max((end - start).total_seconds(), 1)
    dots_html = ""
    labels_html = ""
    for e, dt in zip(events, dates):
        pct = ((dt - start).total_seconds() / span) * 100
        kind_class = {"phase": "tp-phase", "anchor": "tp-anchor", "today": "tp-today"}.get(e["kind"], "tp-phase")
        dots_html += f'<div class="tp-dot {kind_class}" style="left:{pct:.2f}%" title="{e["date"]} — {e["label"]}"></div>\n'
        # alternate above/below to reduce label collision
        side = "tp-above" if events.index(e) % 2 == 0 else "tp-below"
        sub_html = f'<div class="tp-sub">{e["sub"]}</div>' if e["sub"] else ""
        labels_html += (
            f'<div class="tp-label {side}" style="left:{pct:.2f}%">'
            f'<div class="tp-date">{e["date"]}</div>'
            f'<div class="tp-name">{e["label"]}</div>'
            f'{sub_html}'
            f'</div>\n'
        )

    # KPI cards
    vs25 = kpis.get("vs_feb25_pct")
    vs26 = kpis.get("vs_feb26_pct")
    vs25_cls = "neg" if (vs25 is not None and vs25 < 0) else "pos"
    vs26_cls = "neg" if (vs26 is not None and vs26 < 0) else "pos"
    curr_str = f"${kpis['current_price']:.2f}" if kpis.get("current_price") is not None else "—"
    feb25_str = f"${kpis['feb25_close']:.2f}"
    feb26_str = f"${kpis['feb26_close']:.2f}"

    return f"""
<div class="section-header" id="recovery">
  <div class="section-num">SECTION 00</div>
  <div class="section-title">Recovery Scorecard</div>
  <div class="section-blurb">
    The panels below test whether shelf, consumer demand, and pricing power are recovering or
    permanently impaired. Reddit and YouTube signal whether mindshare survived the ERP shelf-gap;
    brand share-of-voice flags any competitor migration; the stock + demand overlay surfaces
    whether the consumer trajectory has <strong>decoupled</strong> from the price.
  </div>
</div>

<div class="chart-card">
  <h3>ERP Timeline — Class Period &amp; Print</h3>
  <div class="erp-timeline">
    <div class="tp-track"></div>
    {dots_html}
    {labels_html}
  </div>
  {source_caption("Anchor dates from FY25 print (Feb 26, 2026) + class-action filings. Dates are baked constants in <code>scripts/generate_vitl_dashboard.py</code>; today's marker auto-updates.")}
</div>

<div class="chart-card">
  <h3>VITL Daily Close · Jan 1 2025 → Today · Class Period Shaded</h3>
  <div class="chart-wrap big"><canvas id="recoveryStockChart"></canvas></div>
  {source_caption("yfinance via <code>fetch_stock_price.py</code> (curl_cffi Chrome impersonation). Red vertical = Feb 26 print; shaded band = class period (May 8 2025 → Feb 26 2026).")}
</div>

<div class="hero-row">
  <div class="hero-tile">
    <div class="hero-label">Days since FY25 ERP print</div>
    <div class="hero-val">{kpis['days_since_print']}</div>
    <div class="hero-sub">Feb 26, 2026 → today</div>
  </div>
  <div class="hero-tile">
    <div class="hero-label">vs Feb 25 close ({feb25_str})</div>
    <div class="hero-val {vs25_cls}">{fmt_pct(vs25)}</div>
    <div class="hero-sub">current: {curr_str}</div>
  </div>
  <div class="hero-tile">
    <div class="hero-label">vs Print close ({feb26_str})</div>
    <div class="hero-val {vs26_cls}">{fmt_pct(vs26)}</div>
    <div class="hero-sub">−10.8% print-day drop included</div>
  </div>
  <div class="hero-tile">
    <div class="hero-label">Days to lead-plaintiff deadline</div>
    <div class="hero-val">{kpis['days_to_deadline']}</div>
    <div class="hero-sub">May 26, 2026</div>
  </div>
</div>
"""


# Section 01 ─────────────────────────────────────────────────────────────────
def render_overview(hero: dict, traj: dict) -> str:
    return f"""
<div class="section-header" id="overview">
  <div class="section-num">SECTION 01</div>
  <div class="section-title">Overview</div>
</div>

<div class="hero-row">
  <div class="hero-tile">
    <div class="hero-label">SKU Universe</div>
    <div class="hero-val">{hero['sku_count']}</div>
    <div class="hero-sub">eggs, butter, ghee, adjacencies</div>
  </div>
  <div class="hero-tile">
    <div class="hero-label">Retail Banners Monitored</div>
    <div class="hero-val">{hero['retail_targets']}</div>
    <div class="hero-sub">natural / grocery / mass / club / ecom</div>
  </div>
  <div class="hero-tile">
    <div class="hero-label">Composite Demand YoY (placeholder)</div>
    <div class="hero-val">{hero['yoy_composite']:+.1f}<span class="hero-val-suffix">%</span></div>
    <div class="hero-sub">per-line Reddit/YouTube split pending</div>
  </div>
</div>

<div class="chart-card">
  <h3>24-Month Composite Demand Trajectory by Line</h3>
  <div class="chart-wrap big"><canvas id="trajChart"></canvas></div>
  {source_caption("Placeholder series — split into per-line Reddit/YouTube once SKU-level fetchers are added.")}
</div>
"""


# Section 02 ─────────────────────────────────────────────────────────────────
def render_retail(retail: dict) -> str:
    if not retail["rows"]:
        body = '<div class="placeholder">No retailers in <code>config/retailers.csv</code> yet.</div>'
    else:
        rows_html = ""
        for r in retail["rows"]:
            channel_color = CHANNEL_COLORS.get(r["channel"], "#999")
            badge = "badge-pos" if r["pct_acv"] >= 80 else ("badge-mid" if r["pct_acv"] >= 40 else "badge-na")
            rows_html += f"""
<tr>
  <td><strong>{r['name']}</strong></td>
  <td><span class="dot" style="background:{channel_color}"></span>{r['channel']}</td>
  <td class="num">{r['pct_acv']}%</td>
  <td class="num">{r['skus']}</td>
  <td class="num"><span class="badge {badge}">{r['oos_pct']}%</span></td>
  <td class="muted-cell">{r['notes']}</td>
</tr>"""
        body = f"""
<div class="table-card">
  <table>
    <thead><tr>
      <th>Retailer</th><th>Channel</th><th class="num">% ACV</th>
      <th class="num">SKUs Stocked</th><th class="num">OOS %</th><th>Notes</th>
    </tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
</div>
"""
    return f"""
<div class="section-header" id="retail">
  <div class="section-num">SECTION 02</div>
  <div class="section-title">Retail Distribution &amp; Shelf <span class="placeholder-tag">placeholder · pending Instacart proxy</span></div>
  <div class="section-blurb">
    The <strong>shelf-recovery</strong> test — does premium-egg ACV claw back the points lost
    during the ERP gap? Currently placeholder; an Instacart cross-banner search will replace these
    cell values with a directional proxy until a licensed scan-data feed is wired in.
  </div>
</div>
{body}
{source_caption("Placeholder distribution snapshot.")}
"""


# Section 03 ─────────────────────────────────────────────────────────────────
def render_product_heat(heat: dict) -> str:
    if not heat["rows"]:
        body = '<div class="placeholder">No products in <code>config/products.csv</code> yet.</div>'
    else:
        rows_html = ""
        for r in heat["rows"]:
            line_color = LINE_COLORS.get(r["line"], "#999")
            line_label = LINE_LABELS.get(r["line"], r["line"])
            rows_html += f"""
<tr>
  <td><strong>{r['name']}</strong></td>
  <td><span class="dot" style="background:{line_color}"></span>{line_label}</td>
  <td>{r['launch_year']}</td>
  <td><span class="badge badge-na">{r['priority']}</span></td>
  <td class="num muted-cell">{fmt_num(r['reddit_yoy'])}</td>
  <td class="num muted-cell">{fmt_num(r['youtube_yoy'])}</td>
  <td class="num muted-cell">{fmt_num(r['search_yoy'])}</td>
  <td class="muted-cell">{r['notes']}</td>
</tr>"""
        body = f"""
<div class="table-card">
  <table>
    <thead><tr>
      <th>SKU</th><th>Line</th><th>Launched</th><th>Priority</th>
      <th class="num">Reddit YoY</th><th class="num">YouTube YoY</th><th class="num">Search YoY</th>
      <th>Notes</th>
    </tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
</div>
"""
    return f"""
<div class="section-header" id="heat">
  <div class="section-num">SECTION 03</div>
  <div class="section-title">Product Line Heat Map <span class="placeholder-tag">placeholder</span></div>
  <div class="section-blurb">
    Per-SKU signal. YoY columns light up once per-SKU Reddit/YouTube/Search fetchers are split out.
  </div>
</div>
{body}
"""


# Section 04 ─────────────────────────────────────────────────────────────────
def render_community(comm: dict) -> str:
    if not comm["sub_rows"]:
        body = '<div class="placeholder">No subreddits in <code>config/reddit_subreddits.csv</code> yet.</div>'
    else:
        rows_html = ""
        for r in comm["sub_rows"]:
            yoy = r["yoy_pct"]
            yoy_cls = ""
            if yoy is not None:
                yoy_cls = "badge-pos" if yoy >= 0 else "badge-neg"
            yoy_html = f'<span class="badge {yoy_cls}">{fmt_pct(yoy)}</span>' if yoy is not None else '<span class="muted-cell">—</span>'
            rows_html += f"""
<tr>
  <td><strong>r/{r['subreddit']}</strong></td>
  <td>{r['topic']}</td>
  <td><span class="badge badge-na">{r['priority']}</span></td>
  <td class="num">{fmt_num(r['mentions_90d'])}</td>
  <td class="num">{yoy_html}</td>
</tr>"""
        body = f"""
<div class="table-card">
  <table>
    <thead><tr>
      <th>Subreddit</th><th>Topic</th><th>Priority</th>
      <th class="num">Mentions (90d)</th><th class="num">YoY %</th>
    </tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
</div>
"""

    totals = comm.get("totals") or {}
    brand_totals_html = ""
    if totals:
        top = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
        brand_totals_html = "<div class=\"stat-row\">" + "".join(
            f'<div class="stat-card"><div class="stat-val">{fmt_num(v)}</div>'
            f'<div class="stat-lbl">{k}</div></div>'
            for k, v in top
        ) + "</div>"

    return f"""
<div class="section-header" id="community">
  <div class="section-num">SECTION 04</div>
  <div class="section-title">Community &amp; Social Signal</div>
  <div class="section-blurb">
    Reddit mention volume across 15 food / health / value subs. The <strong>Brand Share of Voice</strong>
    chart below tests whether the ERP shelf-gap (May 2025 → Feb 2026) let competitors (Handsome Brook,
    Alexandre, Pete &amp; Gerry's, Happy Egg, Organic Valley) take consumer mindshare.
  </div>
</div>
{body}
{source_caption("Reddit data from Arctic Shift archive (<code>fetch_reddit_arctic.py</code>), title-only match on \"vital farms\". Latest = past 90 days; YoY compares to the same 90-day window 12 months ago.")}

<div class="chart-card">
  <h3>Brand Share of Voice — Pasture-Raised Egg Set (Weekly Reddit Mentions, 36mo)</h3>
  <div class="chart-wrap big"><canvas id="brandSovChart"></canvas></div>
  {source_caption("Six-brand stacked area from <code>fetch_competitor_mentions.py</code> (title-only Reddit match per brand). Red vertical line = Feb 26 2026 FY25 print.")}
</div>
{brand_totals_html}
"""


# Section 05 ─────────────────────────────────────────────────────────────────
def render_news(news: dict) -> str:
    total = news.get("total", 0)
    pubs = news.get("publishers") or []
    pub_chips = ""
    if pubs:
        pub_chips = '<div class="pub-row">' + "".join(
            f'<span class="pub-chip">{p["source"]} <span class="pub-count">{p["count"]}</span></span>'
            for p in pubs
        ) + "</div>"

    return f"""
<div class="section-header" id="news">
  <div class="section-num">SECTION 05</div>
  <div class="section-title">News Coverage <span class="muted-cell" style="font-size:11.5px;font-weight:500">· {total} articles tracked</span></div>
  <div class="section-blurb">
    Article cadence + topic mix. Topics include <strong>erp_lawsuit</strong> (class action filings, ERP
    coverage), supply (avian flu), launch / distribution, health / ethical, financial, culture / recipe.
    Surfaces non-quarterly news flow — especially supply / lawsuit coverage that moves the stock between prints.
  </div>
</div>
<div class="dual-col">
  <div class="chart-card">
    <h3>Article Cadence (weekly)</h3>
    <div class="chart-wrap"><canvas id="newsCadenceChart"></canvas></div>
  </div>
  <div class="chart-card">
    <h3>Topic Mix</h3>
    <div class="chart-wrap"><canvas id="newsTopicChart"></canvas></div>
  </div>
</div>
{('<div class="chart-card"><h3>Top Publishers</h3>' + pub_chips + '</div>') if pub_chips else ''}
{source_caption("GDELT ArtList primary (article-level metadata), Google News RSS fallback. Topics classified by keyword dictionary in <code>fetch_google_news.py</code>; <code>erp_lawsuit</code> checked first so securities-fraud articles tag correctly.")}
"""


# Section 06 ─────────────────────────────────────────────────────────────────
def render_pricing() -> str:
    return f"""
<div class="section-header" id="pricing">
  <div class="section-num">SECTION 06</div>
  <div class="section-title">Pricing Power Monitor <span class="placeholder-tag">placeholder</span></div>
  <div class="section-blurb">
    VITL retail price vs (a) conventional Grade-A eggs (USDA / BLS) and (b) premium peers
    (Pete &amp; Gerry's, Happy Egg, Handsome Brook, Organic Valley). The signal: does the
    pasture-raised premium <strong>compress</strong> when conventional egg prices spike, or
    does VITL hold absolute pricing? Pending Instacart scrape.
  </div>
</div>
<div class="chart-card">
  <h3>VITL vs Conventional — Retail Price History (placeholder)</h3>
  <div class="chart-wrap big"><canvas id="pricingChart"></canvas></div>
  {source_caption("To be wired from Instacart cross-banner price scrape + USDA wholesale + BLS CPI eggs.")}
</div>
"""


# Section 07 ─────────────────────────────────────────────────────────────────
def render_supply() -> str:
    return f"""
<div class="section-header" id="supply">
  <div class="section-num">SECTION 07</div>
  <div class="section-title">Supply Risk Monitor — Avian Flu &amp; Egg Wholesale <span class="placeholder-tag">placeholder</span></div>
  <div class="section-blurb">
    H5N1 / HPAI news flow + USDA egg wholesale prices + flock data. Pasture-raised flocks have
    <strong>lower density</strong> than caged operations, so VITL is structurally less exposed than
    CALM-style conventional producers — but not immune. This panel isolates supply-side risk
    separately from demand.
  </div>
</div>
<div class="chart-card">
  <h3>Wholesale Egg Price (USDA, cents/dozen) — placeholder</h3>
  <div class="chart-wrap big"><canvas id="supplyChart"></canvas></div>
  {source_caption("To be wired from USDA AMS daily egg market reports + USDA APHIS HPAI confirmed cases.")}
</div>
"""


# Section 08 ─────────────────────────────────────────────────────────────────
def render_stock_section() -> str:
    return f"""
<div class="section-header" id="stock">
  <div class="section-num">SECTION 08</div>
  <div class="section-title">Demand vs Stock</div>
  <div class="section-blurb">
    VITL close (3-year) overlaid with z-scored composite consumer demand (weekly Reddit + monthly
    YouTube views forward-filled) and event markers from news classified as <strong>financial</strong>
    or <strong>erp_lawsuit</strong>. Shaded band = class period (May 8 2025 → Feb 26 2026).
    Looking for: does the demand line <em>lead</em>, <em>lag</em>, or <em>decouple</em> from price?
  </div>
</div>
<div class="chart-card">
  <h3>VITL Close + Composite Demand + Event Markers</h3>
  <div class="chart-wrap tall"><canvas id="stockChart"></canvas></div>
  {source_caption("Stock = <code>data/vitl_stock.csv</code>. Demand z-score = standardized sum of weekly Reddit mentions + (monthly YouTube views resampled to weekly). Events = news articles classified financial / erp_lawsuit.")}
</div>
"""


# Modal ──────────────────────────────────────────────────────────────────────
def render_summary_modal(s: dict) -> str:
    bullets_html = "".join(f"<li>{b}</li>" for b in s["bullets"])
    todo_html = "".join(f"<li>{t}</li>" for t in s["to_do_next"])
    return f"""
<div id="summaryModal" class="modal-backdrop" onclick="if(event.target===this) this.style.display='none'">
  <div class="modal">
    <div class="modal-header">
      <div>
        <div class="modal-title">{s['headline']}</div>
        <div class="modal-sub">Generated {s['generated_at']}</div>
      </div>
      <button class="modal-close" onclick="document.getElementById('summaryModal').style.display='none'">×</button>
    </div>
    <div class="modal-body">
      <div class="modal-section-title">What this dashboard shows</div>
      <ul class="modal-list">{bullets_html}</ul>
      <div class="modal-section-title">Pipeline to wire next</div>
      <ul class="modal-list">{todo_html}</ul>
    </div>
  </div>
</div>
"""


# ─────────────────────────────────────────────────────────────────────────────
# HTML build
# ─────────────────────────────────────────────────────────────────────────────
def build_html(d: dict) -> str:
    recovery = compute_recovery(d)
    traj     = compute_trajectory(d)
    hero     = compute_hero(d, traj)
    retail   = compute_retail(d)
    heat     = compute_product_heat(d)
    comm     = compute_community(d)
    news     = compute_news(d)
    stockp   = compute_stock_panel(d)
    summary  = compute_summary(d, hero, news, recovery)

    chart_blob = json.dumps({
        "recovery":   recovery,
        "traj":       traj,
        "comm":       comm,
        "news":       news,
        "stockp":     stockp,
        "topic_colors": TOPIC_COLORS,
        "topic_labels": TOPIC_LABELS,
        "brand_colors": BRAND_SOV_COLORS,
        "accent":     BRAND_ACCENT,
        "accent2":    BRAND_ACCENT2,
        "accent_neg": BRAND_ACCENT4,
    })

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    summary_html = render_summary_modal(summary)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{BRAND_NAME} ({BRAND_TICKER}) Recovery Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
<style>
  :root {{
    --bg:       #fbf8ef;
    --surface:  #ffffff;
    --surface2: #f7f3e6;
    --border:   #e4dccd;
    --border-strong: #d4c8ad;
    --text:     #2b2f25;
    --text-soft:#4a4f3f;
    --muted:    #8b8b78;
    --accent:   {BRAND_ACCENT};
    --accent2:  {BRAND_ACCENT2};
    --accent3:  {BRAND_ACCENT3};
    --pos:      {BRAND_ACCENT};
    --neg:      {BRAND_ACCENT4};
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html {{ scroll-behavior: smooth; }}
  body {{ background: var(--bg); color: var(--text);
         font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
         font-size: 14px; line-height: 1.6; }}
  a {{ color: var(--text); text-decoration: none; }}
  a:hover {{ color: var(--accent); }}

  .topbar {{ background: var(--surface); border-bottom: 1px solid var(--border);
             padding: 12px 32px; display: flex; align-items: center;
             justify-content: space-between; gap: 20px;
             position: sticky; top: 0; z-index: 100;
             box-shadow: 0 1px 0 rgba(45,47,37,0.03); }}
  .topbar h1 {{ font-size: 16px; font-weight: 700; letter-spacing: -0.3px; color: var(--text); }}
  .topbar .meta {{ color: var(--muted); font-size: 11px; }}
  .topbar-nav {{ display: flex; gap: 4px; flex-wrap: nowrap; }}
  .nav-btn {{ font-size: 11px; font-weight: 600; letter-spacing: 0.3px;
              color: var(--muted); background: transparent;
              border: 1px solid var(--border); border-radius: 999px;
              padding: 5px 12px; white-space: nowrap; cursor: pointer;
              transition: color .15s, border-color .15s, background .15s; }}
  .nav-btn:hover {{ color: var(--accent); border-color: var(--accent); background: rgba(46,90,60,0.06); }}
  .nav-btn.recovery {{ background: var(--accent); color: #fff; border-color: var(--accent); }}
  .nav-btn.recovery:hover {{ background: #24482f; }}
  .summary-btn {{ background: var(--accent); color: #fff; border: none;
                  border-radius: 999px; padding: 7px 16px;
                  font-size: 12px; font-weight: 700; letter-spacing: 0.3px;
                  cursor: pointer; white-space: nowrap;
                  transition: background .15s, transform .1s; }}
  .summary-btn:hover {{ background: #24482f; transform: translateY(-1px); }}

  .container {{ max-width: 1280px; margin: 0 auto; padding: 24px 32px; }}

  .section-header {{ margin: 44px 0 14px; padding-bottom: 10px; border-bottom: 1px solid var(--border); }}
  .section-header:first-of-type {{ margin-top: 0; }}
  .section-num {{ font-size: 10px; font-weight: 700; color: var(--accent); letter-spacing: 1.8px; }}
  .section-title {{ font-size: 21px; font-weight: 700; margin-top: 4px; letter-spacing: -0.4px; color: var(--text); }}
  .placeholder-tag {{ display: inline-block; margin-left: 8px; font-size: 10px;
                      font-weight: 600; padding: 2px 8px; border-radius: 999px;
                      background: #eee7d6; color: #8a6b10; letter-spacing: 0.4px;
                      text-transform: uppercase; vertical-align: middle; }}
  .section-blurb {{ font-size: 13px; color: var(--text-soft); line-height: 1.6;
                    margin-top: 12px; padding: 12px 16px; max-width: 880px;
                    background: #fef9ec; border: 1px solid #f2e4b6;
                    border-left: 4px solid var(--accent2); border-radius: 6px; }}
  .section-blurb strong {{ color: var(--text); font-weight: 700; }}

  .hero-row {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 14px; }}
  @media (max-width: 1024px) {{ .hero-row {{ grid-template-columns: 1fr 1fr; }} }}
  .hero-tile {{ background: var(--surface); border: 1px solid var(--border);
                border-radius: 10px; padding: 20px 22px;
                box-shadow: 0 1px 3px rgba(45,47,37,0.04); }}
  .hero-label {{ font-size: 10px; color: var(--muted); text-transform: uppercase;
                 letter-spacing: 0.8px; margin-bottom: 10px; font-weight: 700; }}
  .hero-val {{ font-size: 30px; font-weight: 700; letter-spacing: -0.6px; color: var(--text); }}
  .hero-val.pos {{ color: var(--accent); }}
  .hero-val.neg {{ color: var(--neg); }}
  .hero-val-suffix {{ font-size: 12px; color: var(--muted); font-weight: 500; margin-left: 8px; }}
  .hero-sub {{ font-size: 11.5px; color: var(--muted); margin-top: 6px; }}

  .chart-card {{ background: var(--surface); border: 1px solid var(--border);
                 border-radius: 10px; padding: 20px 22px; margin-bottom: 14px;
                 box-shadow: 0 1px 3px rgba(45,47,37,0.04); }}
  .chart-card h3 {{ font-size: 14px; font-weight: 700; margin-bottom: 14px;
                    letter-spacing: -0.2px; color: var(--text); }}
  .chart-wrap {{ position: relative; height: 300px; }}
  .chart-wrap.big {{ height: 380px; }}
  .chart-wrap.tall {{ height: 460px; }}

  .source-caption {{ font-size: 10.5px; color: var(--muted);
                     line-height: 1.55; margin-top: 12px;
                     padding-top: 10px; border-top: 1px dashed var(--border);
                     font-style: italic; }}
  .source-caption code {{ color: var(--accent); font-family: 'SF Mono', Menlo, Consolas, monospace;
                          font-size: 10.5px; font-style: normal;
                          background: rgba(46,90,60,0.08); padding: 1px 5px; border-radius: 3px; }}

  .dual-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }}
  @media (max-width: 1024px) {{ .dual-col {{ grid-template-columns: 1fr; }} }}

  .table-card {{ background: var(--surface); border: 1px solid var(--border);
                 border-radius: 10px; overflow: auto;
                 box-shadow: 0 1px 3px rgba(45,47,37,0.04); }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{ font-size: 10px; text-transform: uppercase; letter-spacing: 0.6px;
        color: var(--muted); font-weight: 700; padding: 10px 12px;
        border-bottom: 1px solid var(--border); text-align: left;
        background: var(--surface2); white-space: nowrap; }}
  td {{ padding: 10px 12px; border-bottom: 1px solid var(--border); font-size: 12.5px; color: var(--text); }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: rgba(46,90,60,0.04); }}
  td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  th.num {{ text-align: right; }}
  td.muted-cell {{ color: var(--muted); font-size: 11.5px; }}
  td strong {{ color: var(--text); font-weight: 700; }}
  .dot {{ display: inline-block; width: 9px; height: 9px; border-radius: 50%;
          margin-right: 8px; vertical-align: middle; }}
  .muted-cell {{ color: var(--muted); }}

  .badge {{ display: inline-block; padding: 3px 8px; border-radius: 999px;
            font-size: 10px; font-weight: 700; letter-spacing: 0.3px; white-space: nowrap; }}
  .badge-pos {{ background: #e1f0dc; color: #2a5a30; }}
  .badge-neg {{ background: #f8e2dc; color: #b34738; }}
  .badge-na  {{ background: #eee7d6; color: #8b8271; }}
  .badge-mid {{ background: #fdefc9; color: #8a6b10; }}

  .placeholder {{ background: var(--surface2); border: 1px dashed var(--border-strong);
                  border-radius: 8px; padding: 22px 18px; text-align: center;
                  color: var(--muted); font-size: 12.5px; }}
  .placeholder code {{ color: var(--accent); font-family: 'SF Mono', Menlo, Consolas, monospace; }}

  /* ERP timeline strip */
  .erp-timeline {{ position: relative; height: 180px; margin: 16px 0 8px; padding: 60px 24px 60px; }}
  .tp-track {{ position: absolute; left: 24px; right: 24px; top: 50%; height: 2px;
               background: linear-gradient(90deg, var(--border) 0%, var(--accent3) 50%, var(--accent) 100%);
               border-radius: 2px; }}
  .tp-dot {{ position: absolute; top: 50%; transform: translate(-50%, -50%);
            width: 14px; height: 14px; border-radius: 50%;
            background: var(--muted); border: 3px solid var(--surface);
            box-shadow: 0 0 0 1px var(--border); }}
  .tp-dot.tp-phase  {{ background: var(--muted); }}
  .tp-dot.tp-anchor {{ background: var(--neg); width: 18px; height: 18px;
                       box-shadow: 0 0 0 1px var(--neg), 0 0 12px rgba(201,93,74,0.4); }}
  .tp-dot.tp-today  {{ background: var(--accent); width: 16px; height: 16px;
                       box-shadow: 0 0 0 1px var(--accent), 0 0 12px rgba(46,90,60,0.4); }}
  .tp-label {{ position: absolute; transform: translateX(-50%); width: 160px;
               text-align: center; font-size: 10.5px; line-height: 1.4; }}
  .tp-label.tp-above {{ top: 0; }}
  .tp-label.tp-below {{ bottom: 0; }}
  .tp-date {{ font-weight: 700; color: var(--text); font-size: 11px; }}
  .tp-name {{ color: var(--text-soft); margin-top: 2px; font-weight: 600; }}
  .tp-sub  {{ color: var(--muted); font-size: 9.5px; margin-top: 2px; font-style: italic; }}

  .pub-row {{ display: flex; flex-wrap: wrap; gap: 6px; margin: 4px 0 0; }}
  .pub-chip {{ background: var(--surface2); border: 1px solid var(--border);
               border-radius: 999px; padding: 4px 12px; font-size: 11.5px; color: var(--text-soft); }}
  .pub-count {{ color: var(--muted); margin-left: 6px; font-variant-numeric: tabular-nums; }}

  .stat-row {{ display: flex; gap: 12px; margin-top: 10px; flex-wrap: wrap; }}
  .stat-card {{ background: var(--surface); border: 1px solid var(--border);
                border-radius: 10px; padding: 12px 18px; min-width: 130px; flex: 1 1 130px;
                box-shadow: 0 1px 3px rgba(45,47,37,0.04); }}
  .stat-val {{ font-size: 22px; font-weight: 700; letter-spacing: -0.4px; color: var(--text); }}
  .stat-lbl {{ font-size: 10px; color: var(--muted); text-transform: uppercase;
               letter-spacing: 0.7px; margin-top: 4px; font-weight: 600; }}

  /* Modal */
  .modal-backdrop {{ display: none; position: fixed; inset: 0;
                     background: rgba(20,22,15,0.5); z-index: 200;
                     align-items: flex-start; justify-content: center; padding: 60px 20px; }}
  .modal-backdrop.open {{ display: flex; }}
  .modal {{ background: var(--surface); border: 1px solid var(--border);
            border-radius: 12px; max-width: 720px; width: 100%;
            box-shadow: 0 8px 32px rgba(0,0,0,0.18); overflow: hidden; }}
  .modal-header {{ display: flex; justify-content: space-between; align-items: flex-start;
                   padding: 22px 26px 14px; border-bottom: 1px solid var(--border); }}
  .modal-title {{ font-size: 17px; font-weight: 700; letter-spacing: -0.3px; }}
  .modal-sub {{ font-size: 11px; color: var(--muted); margin-top: 3px; }}
  .modal-close {{ background: transparent; border: none; font-size: 24px; color: var(--muted);
                  cursor: pointer; line-height: 1; padding: 0 4px; }}
  .modal-body {{ padding: 18px 26px 26px; max-height: 70vh; overflow-y: auto; }}
  .modal-section-title {{ font-size: 10.5px; text-transform: uppercase; letter-spacing: 1.2px;
                          color: var(--accent); font-weight: 700; margin: 14px 0 8px; }}
  .modal-list {{ list-style: none; padding-left: 0; font-size: 13px; color: var(--text-soft); line-height: 1.7; }}
  .modal-list li {{ padding: 5px 0 5px 16px; border-bottom: 1px dashed var(--border); position: relative; }}
  .modal-list li:before {{ content: "›"; position: absolute; left: 0; color: var(--accent); font-weight: 700; }}
  .modal-list li:last-child {{ border-bottom: none; }}
  .modal-list code {{ color: var(--accent); background: rgba(46,90,60,0.08);
                      padding: 1px 5px; border-radius: 3px; font-family: 'SF Mono', Menlo, Consolas, monospace;
                      font-size: 11.5px; }}

  footer {{ text-align: center; color: var(--muted); font-size: 11px;
            padding: 28px 0; border-top: 1px solid var(--border); margin-top: 40px; }}
</style>
</head>
<body>

<div class="topbar">
  <h1>{BRAND_NAME} <span style="color:var(--muted);font-weight:400">— {BRAND_TICKER} Recovery Dashboard</span></h1>
  <div class="topbar-nav">
    <a class="nav-btn recovery" href="#recovery">Recovery</a>
    <a class="nav-btn" href="#overview">Overview</a>
    <a class="nav-btn" href="#retail">Retail</a>
    <a class="nav-btn" href="#heat">SKU Heat</a>
    <a class="nav-btn" href="#community">Community</a>
    <a class="nav-btn" href="#news">News</a>
    <a class="nav-btn" href="#pricing">Pricing</a>
    <a class="nav-btn" href="#supply">Supply</a>
    <a class="nav-btn" href="#stock">Stock</a>
  </div>
  <button class="summary-btn" onclick="document.getElementById('summaryModal').classList.add('open');document.getElementById('summaryModal').style.display='flex'">
    Generate Summary
  </button>
</div>

<div class="container">
  {render_recovery(recovery)}
  {render_overview(hero, traj)}
  {render_retail(retail)}
  {render_product_heat(heat)}
  {render_community(comm)}
  {render_news(news)}
  {render_pricing()}
  {render_supply()}
  {render_stock_section()}
</div>

<footer>
  {BRAND_NAME} ({BRAND_TICKER}) Recovery Dashboard · generated {generated_at}
</footer>

{summary_html}

<script>
  window.__vitl = {chart_blob};

  // Chart.js plugin: vertical reference line + class-period band on the stock charts.
  const refLinePlugin = {{
    id: 'refLine',
    beforeDraw(chart, args, opts) {{
      const refs = opts.refs || [];
      const bands = opts.bands || [];
      const {{ ctx, chartArea, scales }} = chart;
      if (!scales.x || !chartArea) return;
      ctx.save();
      // Bands first so lines render on top
      for (const b of bands) {{
        const xs = scales.x.getPixelForValue(b.start);
        const xe = scales.x.getPixelForValue(b.end);
        if (Number.isFinite(xs) && Number.isFinite(xe)) {{
          ctx.fillStyle = b.color || 'rgba(201,93,74,0.07)';
          ctx.fillRect(xs, chartArea.top, xe - xs, chartArea.bottom - chartArea.top);
        }}
      }}
      for (const r of refs) {{
        const x = scales.x.getPixelForValue(r.date);
        if (!Number.isFinite(x)) continue;
        ctx.strokeStyle = r.color || '#C95D4A';
        ctx.lineWidth = r.width || 2;
        ctx.setLineDash(r.dash || [4, 4]);
        ctx.beginPath();
        ctx.moveTo(x, chartArea.top);
        ctx.lineTo(x, chartArea.bottom);
        ctx.stroke();
        if (r.label) {{
          ctx.setLineDash([]);
          ctx.fillStyle = r.color || '#C95D4A';
          ctx.font = '10.5px Inter, system-ui, sans-serif';
          ctx.textAlign = 'center';
          ctx.fillText(r.label, x, chartArea.top + 12);
        }}
      }}
      ctx.restore();
    }},
  }};
  Chart.register(refLinePlugin);

  document.addEventListener('DOMContentLoaded', () => {{
    const d = window.__vitl;
    const ACCENT = d.accent;
    const ACCENT2 = d.accent2;
    const NEG = d.accent_neg;

    // ── Section 00: Recovery stock chart ────────────────────────────────────
    const rec = d.recovery;
    new Chart(document.getElementById('recoveryStockChart'), {{
      type: 'line',
      data: {{
        labels: rec.stock_series.dates,
        datasets: [{{
          label: 'VITL Close',
          data: rec.stock_series.close,
          borderColor: ACCENT,
          backgroundColor: 'rgba(46,90,60,0.08)',
          borderWidth: 2,
          tension: 0.15,
          pointRadius: 0,
          fill: true,
        }}],
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{
          legend: {{ display: false }},
          refLine: {{
            bands: [{{ start: rec.class_period_start, end: rec.class_period_end,
                      color: 'rgba(201,93,74,0.08)' }}],
            refs: [{{ date: '2026-02-26', color: NEG, width: 2, dash: [], label: 'Feb 26 print' }}],
          }},
          tooltip: {{ mode: 'index', intersect: false,
                      callbacks: {{ label: ctx => '$' + Number(ctx.raw).toFixed(2) }} }},
        }},
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }}, maxTicksLimit: 10, autoSkip: true }} }},
          y: {{ grid: {{ color: 'rgba(0,0,0,0.05)' }}, ticks: {{ font: {{ size: 10 }}, callback: v => '$' + v }} }},
        }},
      }},
    }});

    // ── Section 01: trajectory ──────────────────────────────────────────────
    new Chart(document.getElementById('trajChart'), {{
      type: 'line',
      data: {{
        labels: d.traj.months,
        datasets: [
          {{ label: 'Eggs',   data: d.traj.eggs,   borderColor: ACCENT,  backgroundColor: 'rgba(46,90,60,0.08)',  borderWidth: 2.2, tension: 0.3, fill: true }},
          {{ label: 'Butter', data: d.traj.butter, borderColor: ACCENT2, backgroundColor: 'rgba(244,196,48,0.08)', borderWidth: 2, tension: 0.3, fill: false }},
          {{ label: 'Ghee',   data: d.traj.ghee,   borderColor: '#B5651D', borderWidth: 2, tension: 0.3, fill: false }},
        ]
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{ legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }} }} }} }},
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }}, maxRotation: 0, autoSkipPadding: 16 }} }},
          y: {{ grid: {{ color: 'rgba(0,0,0,0.04)' }}, ticks: {{ font: {{ size: 10 }} }} }}
        }}
      }}
    }});

    // ── Section 04: brand share-of-voice (stacked area) ─────────────────────
    const sov = d.comm.brand_sov;
    const brandOrder = ['Vital Farms','Handsome Brook','Alexandre','Pete & Gerry\\'s','Happy Egg','Organic Valley'];
    const sovDatasets = brandOrder
      .filter(b => sov.brands && sov.brands[b])
      .map(b => ({{
        label: b,
        data: sov.brands[b],
        borderColor: d.brand_colors[b] || '#999',
        backgroundColor: (d.brand_colors[b] || '#999') + '55',
        borderWidth: 1.5,
        fill: true,
        tension: 0.2,
        pointRadius: 0,
      }}));
    if (sovDatasets.length > 0) {{
      new Chart(document.getElementById('brandSovChart'), {{
        type: 'line',
        data: {{ labels: sov.weeks, datasets: sovDatasets }},
        options: {{
          responsive: true, maintainAspectRatio: false,
          plugins: {{
            legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }} }} }},
            refLine: {{
              refs: [{{ date: '2026-02-26', color: NEG, width: 2, dash: [], label: 'Feb 26 print' }}],
              bands: [{{ start: '2025-05-08', end: '2026-02-26', color: 'rgba(201,93,74,0.06)' }}],
            }},
            tooltip: {{ mode: 'index', intersect: false }},
          }},
          scales: {{
            x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }}, maxTicksLimit: 12, autoSkip: true }} }},
            y: {{ stacked: true, grid: {{ color: 'rgba(0,0,0,0.04)' }}, ticks: {{ font: {{ size: 10 }} }} }},
          }},
        }},
      }});
    }} else {{
      const el = document.getElementById('brandSovChart');
      if (el) el.parentElement.innerHTML = '<div class="placeholder">competitor_mentions_weekly.csv not present yet — run <code>make refresh-data</code></div>';
    }}

    // ── Section 05: news cadence + topic doughnut ───────────────────────────
    const cadence = d.news.cadence || {{ weeks: [], counts: [] }};
    new Chart(document.getElementById('newsCadenceChart'), {{
      type: 'bar',
      data: {{
        labels: cadence.weeks,
        datasets: [{{ label: 'Articles', data: cadence.counts, backgroundColor: ACCENT, borderRadius: 3 }}],
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{
          legend: {{ display: false }},
          refLine: {{ refs: [{{ date: '2026-02-26', color: NEG, width: 1.5, dash: [4,4] }}] }},
        }},
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 9 }}, maxTicksLimit: 10, autoSkip: true }} }},
          y: {{ grid: {{ color: 'rgba(0,0,0,0.04)' }}, ticks: {{ font: {{ size: 10 }} }} }},
        }},
      }},
    }});

    const topics = d.news.topics || {{}};
    const topicKeys = Object.keys(topics);
    new Chart(document.getElementById('newsTopicChart'), {{
      type: 'doughnut',
      data: {{
        labels: topicKeys.map(k => d.topic_labels[k] || k),
        datasets: [{{
          data: topicKeys.map(k => topics[k]),
          backgroundColor: topicKeys.map(k => d.topic_colors[k] || '#999'),
          borderWidth: 0,
        }}],
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{ legend: {{ position: 'right', labels: {{ font: {{ size: 11 }} }} }} }},
      }},
    }});

    // ── Section 06 & 07: placeholders (charts render empty but cleanly) ─────
    new Chart(document.getElementById('pricingChart'), {{
      type: 'line',
      data: {{ labels: [], datasets: [
        {{ label: 'VITL (premium)', data: [], borderColor: ACCENT, borderWidth: 2 }},
        {{ label: 'Conventional', data: [], borderColor: '#8b8b78', borderDash: [4,4], borderWidth: 2 }},
      ] }},
      options: {{ responsive: true, maintainAspectRatio: false,
                  plugins: {{ legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }} }} }} }} }},
    }});
    new Chart(document.getElementById('supplyChart'), {{
      type: 'line',
      data: {{ labels: [], datasets: [
        {{ label: 'Wholesale (¢/dz)', data: [], borderColor: NEG, borderWidth: 2 }},
      ] }},
      options: {{ responsive: true, maintainAspectRatio: false,
                  plugins: {{ legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }} }} }} }} }},
    }});

    // ── Section 08: VITL close + composite demand + events ──────────────────
    const sp = d.stockp;
    const stockDatasets = [
      {{ label: 'VITL Close ($)', data: sp.dates.map((dt,i) => ({{x: dt, y: sp.close[i]}})),
         borderColor: ACCENT, backgroundColor: 'rgba(46,90,60,0.06)', borderWidth: 2,
         pointRadius: 0, tension: 0.15, fill: true, yAxisID: 'y' }},
    ];
    if (sp.demand_dates && sp.demand_dates.length > 0) {{
      stockDatasets.push({{
        label: 'Composite Demand (z)',
        data: sp.demand_dates.map((dt,i) => ({{x: dt, y: sp.demand_z[i]}})),
        borderColor: ACCENT2, borderWidth: 1.8, borderDash: [3,3],
        pointRadius: 0, tension: 0.25, fill: false, yAxisID: 'y1',
      }});
    }}
    const eventRefs = (sp.events || []).map(ev => ({{
      date: ev.date,
      color: d.topic_colors[ev.topic] || '#999',
      width: 1,
      dash: [3,3],
    }}));
    eventRefs.push({{ date: '2026-02-26', color: NEG, width: 2, dash: [], label: 'Feb 26 print' }});

    new Chart(document.getElementById('stockChart'), {{
      type: 'line',
      data: {{ datasets: stockDatasets }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        parsing: false,
        plugins: {{
          legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }} }} }},
          refLine: {{
            refs: eventRefs,
            bands: [{{ start: sp.class_period_start, end: sp.class_period_end, color: 'rgba(201,93,74,0.06)' }}],
          }},
          tooltip: {{ mode: 'index', intersect: false }},
        }},
        scales: {{
          x: {{ type: 'time', time: {{ unit: 'month' }}, grid: {{ display: false }},
                ticks: {{ font: {{ size: 10 }}, maxTicksLimit: 12, autoSkip: true }} }},
          y:  {{ position: 'left',  title: {{ display: true, text: 'VITL ($)', font: {{ size: 10 }} }},
                 grid: {{ color: 'rgba(0,0,0,0.04)' }}, ticks: {{ font: {{ size: 10 }}, callback: v => '$' + v }} }},
          y1: {{ position: 'right', title: {{ display: true, text: 'Demand z-score', font: {{ size: 10 }} }},
                 grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }} }} }},
        }},
      }},
    }});
  }});
</script>

</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print(f"── {BRAND_NAME} ({BRAND_TICKER}) Recovery Dashboard ──")
    d = load_all()
    for k, v in d.items():
        n = len(v) if hasattr(v, "__len__") else 0
        flag = "✓" if n > 0 else "·"
        print(f"  {flag} {k:22s} rows={n}")

    html = build_html(d)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    size_kb = OUTPUT_HTML.stat().st_size / 1024
    print(f"\n  → wrote {OUTPUT_HTML}  ({size_kb:.1f} KB)")

    try:
        webbrowser.open(f"file://{OUTPUT_HTML.resolve()}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
