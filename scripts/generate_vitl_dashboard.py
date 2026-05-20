"""
Vital Farms Demand Intelligence Dashboard — v3 (unique-data panel restructure)

Layout (top → bottom):
  TOP    "What's Changed" callout (reads/whats_new.md)
  SEC 00 Recovery Scorecard (existing — unchanged)
  SEC 01 The Setup — Conviction vs Cash (NEW hero: cash / insider / short / buyback)
  SEC 02 News Coverage & Reactions (NEW merged: stock-with-event-dots + cadence + topics + log)
  SEC 03 Egg Market — Price Gap Tracker (NEW: conventional vs VITL premium gap + breaker + HPAI)
  SEC 04 Consumer Demand & Brand Health (existing + 6-brand SoV + linoleic decay)
  SEC 05 Did Management Tell Us The Truth (NEW: credibility scorecard table)
  ARCHIVED Sections (no nav): old Retail / SKU Heat / Pricing / Supply / Demand-vs-Stock

Editable narrative lives in /reads/ — markdown files reloaded at render time.
"""
import json
import re
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR     = PROJECT_ROOT / "data"
CONFIG_DIR   = PROJECT_ROOT / "config"
READS_DIR    = PROJECT_ROOT / "reads"
OUTPUT_HTML  = PROJECT_ROOT / "index.html"

BRAND_NAME    = "Vital Farms"
BRAND_TICKER  = "VITL"
BRAND_ACCENT  = "#2E5A3C"   # forest green
BRAND_ACCENT2 = "#F4C430"   # egg yolk
BRAND_ACCENT3 = "#A8C49B"   # pasture light
BRAND_ACCENT4 = "#C95D4A"   # warm terracotta (risk / negative)
BRAND_PURPLE  = "#8e6db4"
BRAND_BROWN   = "#B5651D"

# ── Recovery scorecard constants (Section 00) ────────────────────────────────
ERP_PRINT_DATE     = datetime(2026, 2, 26).date()
ERP_PRINT_CLOSE    = 22.11
PRE_PRINT_CLOSE    = 24.79
CLASS_PERIOD_START = "2025-05-08"
CLASS_PERIOD_END   = "2026-02-26"
LP_DEADLINE_DATE   = datetime(2026, 5, 26).date()

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
    {"date": str(datetime.today().date()), "kind": "today", "label": "Today", "sub": ""},
]

TOPIC_COLORS = {
    "erp_lawsuit": "#7d3c4a", "supply": BRAND_ACCENT4, "launch": BRAND_ACCENT,
    "health": BRAND_ACCENT3,  "financial": "#e67e22", "culture": "#e84393",
    "other": "#8b8b78",
}
TOPIC_LABELS = {
    "erp_lawsuit": "ERP / Lawsuit", "supply": "Supply / Avian Flu",
    "launch": "Launch / Distribution", "health": "Health / Ethical",
    "financial": "Financial", "culture": "Culture / Recipe", "other": "Other",
}
BRAND_SOV_COLORS = {
    "Vital Farms": BRAND_ACCENT, "Handsome Brook": BRAND_PURPLE,
    "Alexandre": "#e67e22", "Pete & Gerry's": "#6b94b1",
    "Happy Egg": BRAND_ACCENT2, "Organic Valley": BRAND_BROWN,
}
BRAND_SOV_ORDER = ["Vital Farms", "Handsome Brook", "Alexandre",
                   "Pete & Gerry's", "Happy Egg", "Organic Valley"]
REACTION_COLORS = {"negative": BRAND_ACCENT4, "flat": "#b8a04c",
                   "positive": BRAND_ACCENT}


# ─────────────────────────────────────────────────────────────────────────────
# Loading
# ─────────────────────────────────────────────────────────────────────────────
def safe_read(path: Path) -> pd.DataFrame:
    if path.exists():
        try: return pd.read_csv(path)
        except Exception as e: print(f"  [warn] {path.name}: {e}")
    return pd.DataFrame()


def file_mtime(path: Path) -> str:
    if not path.exists(): return "—"
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")


def load_all() -> dict:
    return {
        # configs
        "products":           safe_read(CONFIG_DIR / "products.csv"),
        "retailers":          safe_read(CONFIG_DIR / "retailers.csv"),
        "subs":               safe_read(CONFIG_DIR / "reddit_subreddits.csv"),
        # data (existing from pass 1 + pass 2)
        "stock":              safe_read(DATA_DIR / "vitl_stock.csv"),
        "reddit_weekly":      safe_read(DATA_DIR / "reddit_mentions_weekly.csv"),
        "competitor_weekly":  safe_read(DATA_DIR / "competitor_mentions_weekly.csv"),
        "youtube_monthly":    safe_read(DATA_DIR / "youtube_monthly.csv"),
        "news":               safe_read(DATA_DIR / "news_articles.csv"),
        # Pass-2 additions
        "events":             safe_read(DATA_DIR / "event_reactions.csv"),
        "cash":               safe_read(DATA_DIR / "cash_position.csv"),
        "insiders":           safe_read(DATA_DIR / "insider_trades.csv"),
        "short_interest":     safe_read(DATA_DIR / "short_interest.csv"),
        "egg_shell":          safe_read(DATA_DIR / "usda_eggs_weekly.csv"),
        "egg_breaker":        safe_read(DATA_DIR / "breaker_prices.csv"),
        "vitl_retail":        safe_read(DATA_DIR / "vitl_retail_price.csv"),
        "hpai":               safe_read(DATA_DIR / "hpai_cases.csv"),
        "layer_flock":        safe_read(DATA_DIR / "layer_flock.csv"),
        "linoleic":           safe_read(DATA_DIR / "linoleic_decay_weekly.csv"),
        "guidance":           safe_read(DATA_DIR / "guidance_vs_actual.csv"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Markdown helper — minimal, no external dep
# ─────────────────────────────────────────────────────────────────────────────
_INLINE_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_INLINE_ITAL = re.compile(r"(?<![*\w])\*([^*\n]+)\*(?![*\w])")
_HEADER1 = re.compile(r"^#\s+(.*)$")

def _inline(s: str) -> str:
    s = _INLINE_BOLD.sub(r"<strong>\1</strong>", s)
    s = _INLINE_ITAL.sub(r"<em>\1</em>", s)
    return s


def load_markdown(path: Path) -> dict:
    """Return {title, datestamp, html}. The first line is parsed as
    `# Title · YYYY-MM-DD` (datestamp optional). Body becomes HTML."""
    if not path.exists():
        return {"title": "—", "datestamp": "", "html": "<p class='muted-cell'>missing: " + path.name + "</p>"}

    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return {"title": "—", "datestamp": "", "html": ""}
    lines = text.splitlines()
    title, datestamp = "", ""
    body_lines = lines
    m = _HEADER1.match(lines[0])
    if m:
        header_text = m.group(1).strip()
        if "·" in header_text:
            t, d = header_text.rsplit("·", 1)
            title = t.strip(); datestamp = d.strip()
        else:
            title = header_text
        body_lines = lines[1:]

    # paragraph segmentation
    paragraphs: list[str] = []
    current: list[str] = []
    list_items: list[str] = []
    in_list = False

    def flush_paragraph():
        if current:
            joined = " ".join(_inline(l.strip()) for l in current if l.strip())
            if joined:
                paragraphs.append(f"<p>{joined}</p>")
            current.clear()

    def flush_list():
        nonlocal in_list
        if list_items:
            paragraphs.append("<ul>" + "".join(f"<li>{_inline(li)}</li>" for li in list_items) + "</ul>")
            list_items.clear()
        in_list = False

    for ln in body_lines:
        stripped = ln.strip()
        if not stripped:
            flush_paragraph(); flush_list(); continue
        if stripped.startswith(("- ", "* ")):
            flush_paragraph()
            in_list = True
            list_items.append(stripped[2:].strip())
            continue
        if in_list:
            flush_list()
        current.append(stripped)
    flush_paragraph(); flush_list()

    return {"title": title, "datestamp": datestamp, "html": "\n".join(paragraphs)}


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
    """Section 00 — unchanged from pass 1."""
    stock = d["stock"].copy()
    today = datetime.today().date()
    days_since_print = (today - ERP_PRINT_DATE).days
    days_to_deadline = (LP_DEADLINE_DATE - today).days

    if stock.empty:
        return {
            "events": ERP_EVENTS, "today_iso": str(today),
            "class_period_start": CLASS_PERIOD_START, "class_period_end": CLASS_PERIOD_END,
            "stock_series": {"dates": [], "close": []},
            "kpis": {
                "days_since_print": days_since_print, "days_to_deadline": days_to_deadline,
                "current_price": None, "feb25_close": PRE_PRINT_CLOSE, "feb26_close": ERP_PRINT_CLOSE,
                "vs_feb25_pct": None, "vs_feb26_pct": None,
            },
        }

    stock["date"] = pd.to_datetime(stock["date"]).dt.strftime("%Y-%m-%d")
    stock = stock.sort_values("date").reset_index(drop=True)
    chart = stock[stock["date"] >= "2025-01-01"]
    feb25 = _close_on(stock, "2026-02-25") or PRE_PRINT_CLOSE
    feb26 = _close_on(stock, "2026-02-26") or ERP_PRINT_CLOSE
    current = float(stock.iloc[-1]["close"])

    return {
        "events": ERP_EVENTS, "today_iso": str(today),
        "class_period_start": CLASS_PERIOD_START, "class_period_end": CLASS_PERIOD_END,
        "stock_series": {
            "dates": chart["date"].tolist(),
            "close": chart["close"].astype(float).round(2).tolist(),
        },
        "kpis": {
            "days_since_print": days_since_print, "days_to_deadline": days_to_deadline,
            "current_price": round(current, 2),
            "feb25_close": round(feb25, 2), "feb26_close": round(feb26, 2),
            "vs_feb25_pct": round((current / feb25 - 1) * 100, 1) if feb25 else None,
            "vs_feb26_pct": round((current / feb26 - 1) * 100, 1) if feb26 else None,
        },
    }


def compute_setup(d: dict) -> dict:
    """Section 01 — cash position bars, insider table, short interest series, buyback."""
    # Cash
    cash_rows = []
    if not d["cash"].empty:
        for _, r in d["cash"].iterrows():
            val = r.get("cash_and_equivalents_m")
            tbd = (val is None) or (isinstance(val, float) and pd.isna(val))
            cash_rows.append({
                "label": r["quarter_label"], "value": (None if tbd else float(val)),
                "tbd": bool(tbd), "note": r.get("note", "") or "",
            })
    cash_change = None
    if len(cash_rows) >= 2 and not cash_rows[0]["tbd"] and not cash_rows[1]["tbd"]:
        cash_change = cash_rows[1]["value"] - cash_rows[0]["value"]

    # Insiders
    insiders_table = []
    cluster_summary = None
    if not d["insiders"].empty:
        idf = d["insiders"].copy()
        idf["date"] = pd.to_datetime(idf["date"], errors="coerce")
        idf = idf.dropna(subset=["date"]).sort_values("date", ascending=False)
        # Focus the displayed table on the May 13-15 cluster + any newer buys
        recent_cutoff = pd.Timestamp("2026-05-01")
        recent = idf[idf["date"] >= recent_cutoff].copy()
        for _, r in recent.iterrows():
            insiders_table.append({
                "date": r["date"].strftime("%Y-%m-%d"),
                "name": r["name"], "title": r["title"], "kind": r["kind"],
                "shares": int(r["shares"]),
                "price": float(r["price"]),
                "total_value": float(r["total_value"]),
            })
        # Cluster (May 13-15 specifically)
        cluster = recent[(recent["date"] >= "2026-05-13") & (recent["date"] <= "2026-05-15")]
        if not cluster.empty:
            cluster_summary = {
                "insiders": int(cluster["name"].nunique()),
                "total_value": float(cluster["total_value"].sum()),
                "start": cluster["date"].min().strftime("%Y-%m-%d"),
                "end": cluster["date"].max().strftime("%Y-%m-%d"),
            }

    # Short interest
    short_series = {"dates": [], "pct": [], "shares": []}
    short_current = None
    if not d["short_interest"].empty:
        sdf = d["short_interest"].copy().sort_values("date")
        short_series = {
            "dates": sdf["date"].astype(str).tolist(),
            "pct":   sdf["short_pct_of_float"].astype(float).round(1).tolist(),
            "shares": sdf["short_interest_shares"].astype(float).fillna(0).astype(int).tolist(),
        }
        latest = sdf.iloc[-1]
        short_current = {
            "date": str(latest["date"]),
            "pct": float(latest["short_pct_of_float"]),
            "shares": int(latest["short_interest_shares"]),
            "days_to_cover": (None if pd.isna(latest.get("days_to_cover")) else float(latest["days_to_cover"])),
        }

    return {
        "cash_rows": cash_rows,
        "cash_change": cash_change,
        "insiders": insiders_table,
        "cluster": cluster_summary,
        "short_series": short_series,
        "short_current": short_current,
    }


def compute_events(d: dict) -> dict:
    """Section 02 hero — 18mo stock + event reaction dots."""
    stock = d["stock"]
    events = d["events"]
    if stock.empty:
        return {"dates": [], "close": [], "events": []}

    s = stock.copy()
    s["date"] = pd.to_datetime(s["date"]).dt.strftime("%Y-%m-%d")
    s = s.sort_values("date").reset_index(drop=True)
    cutoff = (datetime.today() - timedelta(days=540)).strftime("%Y-%m-%d")
    s = s[s["date"] >= cutoff]

    ev_list = []
    if not events.empty:
        for _, r in events.iterrows():
            d_str = str(r["date"])
            close = _close_on(s, d_str)
            if close is None:
                # fallback: nearest preceding trading day in range
                prior = s[s["date"] <= d_str]
                if not prior.empty:
                    close = float(prior.iloc[-1]["close"])
            ev_list.append({
                "date": d_str,
                "headline": str(r.get("headline", ""))[:120],
                "summary":  str(r.get("summary", ""))[:280],
                "reaction_pct": (None if pd.isna(r.get("reaction_pct")) else float(r["reaction_pct"])),
                "reaction_kind": str(r.get("reaction_kind", "flat")),
                "close": (None if close is None else round(close, 2)),
            })

    return {
        "dates": s["date"].tolist(),
        "close": s["close"].astype(float).round(2).tolist(),
        "events": ev_list,
        "class_period_start": CLASS_PERIOD_START,
        "class_period_end": CLASS_PERIOD_END,
    }


def compute_news(d: dict) -> dict:
    """Section 02 panels 2+3 — moved from old render_news."""
    news = d["news"]
    if news.empty:
        return {"cadence": {"weeks": [], "counts": []}, "topics": {}, "publishers": [],
                "total": 0, "articles": []}
    n = news.copy()
    n["date"] = pd.to_datetime(n["date"], errors="coerce")
    n = n.dropna(subset=["date"]).copy()
    n["week"] = n["date"].dt.to_period("W-SUN").dt.end_time.dt.strftime("%Y-%m-%d")

    cad = n.groupby("week").size().reset_index(name="count").sort_values("week")
    topics = {k: int(v) for k, v in n["topic"].value_counts().items()}
    pubs = n["source"].fillna("").astype(str).value_counts().head(12)
    publishers = [{"source": k, "count": int(v)} for k, v in pubs.items() if k]

    # Article log: most recent 50 (collapsed by default)
    log = n.sort_values("date", ascending=False).head(50)
    articles = []
    for _, r in log.iterrows():
        articles.append({
            "date": r["date"].strftime("%Y-%m-%d"),
            "headline": str(r.get("headline", ""))[:200],
            "source": str(r.get("source", "")),
            "topic": str(r.get("topic", "")),
            "url": str(r.get("url", "")),
        })
    return {
        "cadence": {"weeks": cad["week"].tolist(), "counts": cad["count"].astype(int).tolist()},
        "topics": topics, "publishers": publishers,
        "total": int(len(n)), "articles": articles,
    }


def _resample_monthly_to_weekly(monthly_df: pd.DataFrame, month_col: str, val_col: str,
                                target_weeks: list[str]) -> dict[str, float]:
    """Forward-fill a monthly series to target weekly dates."""
    if monthly_df.empty:
        return {}
    m = monthly_df.copy()
    m["dt"] = pd.to_datetime(m[month_col], format="%Y-%m")
    m = m.sort_values("dt")
    out = {}
    for wk in target_weeks:
        wk_dt = pd.to_datetime(wk)
        prior = m[m["dt"] <= wk_dt]
        if not prior.empty:
            out[wk] = float(prior.iloc[-1][val_col])
    return out


def compute_egg_market(d: dict) -> dict:
    """Section 03 — premium gap chart + breaker + HPAI inline notes."""
    shell = d["egg_shell"]
    breaker = d["egg_breaker"]
    retail = d["vitl_retail"]
    hpai = d["hpai"]
    flock = d["layer_flock"]

    # Premium gap: align weekly shell egg + weekly VITL retail (resampled from monthly)
    gap_weeks, conv_prices, vitl_prices, gap_pcts = [], [], [], []
    if not shell.empty:
        s = shell.copy().sort_values("week")
        gap_weeks = s["week"].astype(str).tolist()
        conv_prices = s["price_per_dozen"].astype(float).round(3).tolist()
        # Forward-fill VITL retail to weekly
        vitl_map = _resample_monthly_to_weekly(retail, "month", "retail_price_per_dozen", gap_weeks)
        for wk, conv in zip(gap_weeks, conv_prices):
            v = vitl_map.get(wk)
            vitl_prices.append((None if v is None else round(v, 2)))
            if v is None or conv <= 0:
                gap_pcts.append(None)
            else:
                gap_pcts.append(round((v / conv - 1) * 100, 1))
    peak_gap = max([g for g in gap_pcts if g is not None], default=None)
    latest_gap = next((g for g in reversed(gap_pcts) if g is not None), None)

    # Breaker chart
    breaker_data = {"weeks": [], "prices": []}
    if not breaker.empty:
        b = breaker.copy().sort_values("week")
        breaker_data = {
            "weeks":  b["week"].astype(str).tolist(),
            "prices": b["price_per_dozen"].astype(float).round(3).tolist(),
        }

    # HPAI latest week
    hpai_latest = None
    if not hpai.empty:
        h = hpai.copy().sort_values("week")
        latest = h.iloc[-1]
        hpai_latest = {
            "week": str(latest["week"]),
            "cases": int(latest["commercial_layer_cases"]),
        }

    # Layer flock latest month
    flock_latest = None
    if not flock.empty:
        f = flock.copy().sort_values("month")
        latest = f.iloc[-1]
        flock_latest = {
            "month": str(latest["month"]),
            "millions": float(latest["layer_flock_millions"]),
        }

    return {
        "gap_weeks": gap_weeks, "conv_prices": conv_prices,
        "vitl_prices": vitl_prices, "gap_pcts": gap_pcts,
        "peak_gap": peak_gap, "latest_gap": latest_gap,
        "breaker": breaker_data, "hpai_latest": hpai_latest, "flock_latest": flock_latest,
    }


def compute_community(d: dict) -> dict:
    """Section 04 — Reddit table + 6-brand SoV (zeros guaranteed) + linoleic decay."""
    subs = d["subs"]; reddit_weekly = d["reddit_weekly"]; competitor_weekly = d["competitor_weekly"]
    linoleic = d["linoleic"]

    if subs.empty:
        sub_rows, brand_sov, totals = [], {"weeks": [], "brands": {}}, {}
    else:
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
                "subreddit": sub_name, "topic": r["topic"], "priority": r["priority"],
                "mentions_90d": mentions_90d, "yoy_pct": yoy_pct,
            })

        # SoV with ALL 6 brands guaranteed in the series (zeros where absent)
        brand_sov = {"weeks": [], "brands": {}}; totals = {}
        if not competitor_weekly.empty:
            cw = competitor_weekly.copy(); cw["week"] = cw["week"].astype(str)
            weeks = sorted(cw["week"].unique().tolist())
            brand_sov["weeks"] = weeks
            present_brands = set(cw["brand"].unique().tolist())
            for brand in BRAND_SOV_ORDER:
                if brand in present_brands:
                    b = cw[cw["brand"] == brand].set_index("week")["post_count"].reindex(weeks, fill_value=0)
                    brand_sov["brands"][brand] = b.astype(int).tolist()
                else:
                    brand_sov["brands"][brand] = [0] * len(weeks)
                totals[brand] = int(sum(brand_sov["brands"][brand]))

    # Linoleic decay
    lin_series = {"weeks": [], "counts": []}
    if not linoleic.empty:
        L = linoleic.copy().sort_values("week")
        lin_series = {
            "weeks":  L["week"].astype(str).tolist(),
            "counts": L["post_count"].astype(int).tolist(),
        }

    return {"sub_rows": sub_rows, "brand_sov": brand_sov, "totals": totals,
            "linoleic": lin_series}


def compute_credibility(d: dict) -> dict:
    """Section 05 — guidance scorecard."""
    g = d["guidance"]
    if g.empty: return {"rows": []}
    rows = []
    for _, r in g.iterrows():
        rows.append({
            "period": str(r["period"]), "metric": str(r["metric"]),
            "management_said": str(r["management_said"]),
            "actual": str(r["actual"]),
            "delta": str(r["delta"]),
            "delta_kind": str(r.get("delta_kind", "")).lower(),
        })
    return {"rows": rows}


def compute_summary(d, recovery, setup, news, egg, cred) -> dict:
    kpis = recovery["kpis"]
    vs_print = kpis.get("vs_feb26_pct")
    bullets = [
        f"Days since FY25 ERP print: <strong>{kpis['days_since_print']}</strong> (Feb 26, 2026).",
        (f"VITL vs Feb 26 close (${kpis['feb26_close']:.2f}): "
         f"<strong>{vs_print:+.1f}%</strong>" if vs_print is not None else "VITL vs Feb 26: —"),
        (f"Cash burn last quarter: <strong>${abs(setup['cash_change']):.0f}M</strong>"
         if setup.get("cash_change") is not None else "Cash burn: —"),
        (f"Insider cluster (May 13–15): <strong>{setup['cluster']['insiders']} insiders</strong>, "
         f"${setup['cluster']['total_value']:,.0f}" if setup.get("cluster")
         else "Insider cluster: —"),
        (f"Short interest current: <strong>{setup['short_current']['pct']:.1f}%</strong> of float"
         if setup.get("short_current") else "Short interest: —"),
        (f"VITL-to-conventional egg gap: <strong>{egg['latest_gap']:.0f}%</strong> "
         f"(peak <strong>{egg['peak_gap']:.0f}%</strong>)" if egg.get("latest_gap") is not None
         else "Egg price gap: —"),
        f"News articles tracked: <strong>{news.get('total', 0)}</strong>",
        f"Credibility scorecard rows: <strong>{len(cred['rows'])}</strong>",
    ]
    return {
        "headline": f"{BRAND_NAME} ({BRAND_TICKER}) — Recovery Signal Dashboard",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "bullets": bullets,
        "to_do_next": [
            "Wire USDA MARS API for live shell + breaker egg prices (key registration required).",
            "Wire FINRA bulk short-interest files for full historical series (currently seeded).",
            "TikTok scrape for hashtag-volume cross-check on the linoleic decay signal.",
            "LWAY / MAMA / SMPL comp page (small premium grocery comp set).",
            "Quarterly snapshot mechanism for new <code>guidance_vs_actual.csv</code> rows post-print.",
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


def fmt_money(v, default="—"):
    if v is None or (isinstance(v, float) and pd.isna(v)): return default
    return f"${v:,.0f}"


def source_caption(text: str) -> str:
    return f'<div class="source-caption">{text}</div>'


def refresh_footer(path: Path) -> str:
    return f'<div class="refresh-tag">Last data refresh: <code>{path.name}</code> · {file_mtime(path)}</div>'


def datestamp_chip(ds: str) -> str:
    if not ds: return ""
    return f'<span class="datestamp">· {ds}</span>'


# Top callout (whats_new.md) ──────────────────────────────────────────────────
def render_top_callout() -> str:
    md = load_markdown(READS_DIR / "whats_new.md")
    return f"""
<div class="container">
<div class="whats-new-card">
  <div class="wn-header">
    <span class="wn-eyebrow">WHAT'S CHANGED</span>
    {datestamp_chip(md['datestamp'])}
  </div>
  <div class="wn-body">{md['html']}</div>
</div>
</div>
"""


# Section 00 (existing, unchanged) ───────────────────────────────────────────
def render_recovery(rec: dict) -> str:
    kpis = rec["kpis"]
    events = rec["events"]
    dates = [datetime.strptime(e["date"], "%Y-%m-%d") for e in events]
    start, end = dates[0], dates[-1]
    span = max((end - start).total_seconds(), 1)
    dots_html = ""; labels_html = ""
    for e, dt in zip(events, dates):
        pct = ((dt - start).total_seconds() / span) * 100
        kind_class = {"phase": "tp-phase", "anchor": "tp-anchor", "today": "tp-today"}.get(e["kind"], "tp-phase")
        dots_html += f'<div class="tp-dot {kind_class}" style="left:{pct:.2f}%" title="{e["date"]} — {e["label"]}"></div>\n'
        side = "tp-above" if events.index(e) % 2 == 0 else "tp-below"
        sub_html = f'<div class="tp-sub">{e["sub"]}</div>' if e["sub"] else ""
        labels_html += (
            f'<div class="tp-label {side}" style="left:{pct:.2f}%">'
            f'<div class="tp-date">{e["date"]}</div>'
            f'<div class="tp-name">{e["label"]}</div>'
            f'{sub_html}</div>\n'
        )
    vs25 = kpis.get("vs_feb25_pct"); vs26 = kpis.get("vs_feb26_pct")
    vs25_cls = "neg" if (vs25 is not None and vs25 < 0) else "pos"
    vs26_cls = "neg" if (vs26 is not None and vs26 < 0) else "pos"
    curr_str = f"${kpis['current_price']:.2f}" if kpis.get("current_price") is not None else "—"

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
    <div class="tp-track"></div>{dots_html}{labels_html}
  </div>
  {source_caption("Anchor dates from FY25 print + class-action filings; today's marker auto-updates.")}
</div>
<div class="chart-card">
  <h3>VITL Daily Close · Jan 1 2025 → Today · Class Period Shaded</h3>
  <div class="chart-wrap big"><canvas id="recoveryStockChart"></canvas></div>
  {source_caption("yfinance via <code>fetch_stock_price.py</code>. Red vertical = Feb 26 print; shaded band = class period.")}
  {refresh_footer(DATA_DIR / "vitl_stock.csv")}
</div>
<div class="hero-row">
  <div class="hero-tile">
    <div class="hero-label">Days since FY25 ERP print</div>
    <div class="hero-val">{kpis['days_since_print']}</div>
    <div class="hero-sub">Feb 26, 2026 → today</div>
  </div>
  <div class="hero-tile">
    <div class="hero-label">vs Feb 25 close (${kpis['feb25_close']:.2f})</div>
    <div class="hero-val {vs25_cls}">{fmt_pct(vs25)}</div>
    <div class="hero-sub">current: {curr_str}</div>
  </div>
  <div class="hero-tile">
    <div class="hero-label">vs Print close (${kpis['feb26_close']:.2f})</div>
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


# Section 01 — The Setup ─────────────────────────────────────────────────────
def render_setup(setup: dict) -> str:
    cluster = setup.get("cluster")
    cluster_kpi = (f"{cluster['insiders']} insiders, "
                   f"${cluster['total_value']:,.0f} cluster buy {cluster['start']}→{cluster['end']}"
                   if cluster else "no cluster detected")
    cash_change = setup.get("cash_change")
    cash_kpi = (f"${abs(cash_change):.0f}M burned in Q1" if cash_change is not None else "—")

    # Insider table rows
    insider_rows_html = ""
    for r in setup["insiders"]:
        kind_cls = "badge-pos" if r["kind"] == "buy" else "badge-neg"
        insider_rows_html += f"""
<tr>
  <td>{r['date']}</td>
  <td><strong>{r['name']}</strong><div class="muted-cell">{r['title']}</div></td>
  <td><span class="badge {kind_cls}">{r['kind']}</span></td>
  <td class="num">{int(r['shares']):,}</td>
  <td class="num">${r['price']:.2f}</td>
  <td class="num">${r['total_value']:,.0f}</td>
</tr>"""
    insider_table_html = ""
    if insider_rows_html:
        insider_table_html = f"""
<div class="table-card">
<table>
<thead><tr>
  <th>Date</th><th>Insider</th><th>Kind</th>
  <th class="num">Shares</th><th class="num">Price</th><th class="num">Value</th>
</tr></thead>
<tbody>{insider_rows_html}</tbody>
</table>
</div>"""
    else:
        insider_table_html = '<div class="placeholder">No insider transactions in window.</div>'

    short_current = setup.get("short_current")
    short_kpi = (f"{short_current['pct']:.1f}% of float · {short_current['shares']:,} shares"
                 if short_current else "—")

    # Buyback md
    buyback_md = load_markdown(READS_DIR / "buyback_status.md")
    setup_synth_md = load_markdown(READS_DIR / "setup_synthesis.md")

    return f"""
<div class="section-header" id="setup">
  <div class="section-num">SECTION 01</div>
  <div class="section-title">The Setup — Conviction vs Cash</div>
  <div class="section-subtitle">Cash position, insider buying, short interest, and buyback authorization on one panel.</div>
</div>

<div class="setup-grid">
  <div class="setup-card">
    <div class="setup-card-header">
      <div class="setup-card-title">Cash Position</div>
      <div class="setup-kpi">{cash_kpi}</div>
    </div>
    <div class="chart-wrap" style="height:220px"><canvas id="cashChart"></canvas></div>
    <div class="setup-foot">Undrawn revolver provides cushion. JPM covenant talks ongoing per Q1 call.</div>
    {refresh_footer(DATA_DIR / "cash_position.csv")}
  </div>

  <div class="setup-card">
    <div class="setup-card-header">
      <div class="setup-card-title">Recent Insider Buying</div>
      <div class="setup-kpi">{cluster_kpi}</div>
    </div>
    {insider_table_html}
    <div class="setup-foot">Strongest insider signal pattern — multiple directors and named officers buying within days of each other.</div>
    {refresh_footer(DATA_DIR / "insider_trades.csv")}
  </div>

  <div class="setup-card">
    <div class="setup-card-header">
      <div class="setup-card-title">Short Interest Trend</div>
      <div class="setup-kpi">{short_kpi}</div>
    </div>
    <div class="chart-wrap" style="height:220px"><canvas id="shortChart"></canvas></div>
    <div class="setup-foot">Short interest &gt;30% is significant; 40% is extreme. Sets up squeeze risk for shorts if recovery signals confirm.</div>
    {refresh_footer(DATA_DIR / "short_interest.csv")}
  </div>

  <div class="setup-card setup-buyback">
    <div class="setup-card-header">
      <div class="setup-card-title">Buyback Authorization {datestamp_chip(buyback_md['datestamp'])}</div>
    </div>
    <div class="buyback-body">{buyback_md['html']}</div>
    {refresh_footer(READS_DIR / "buyback_status.md")}
  </div>
</div>

<div class="setup-synthesis">
  <div class="setup-synth-eyebrow">SYNTHESIS {datestamp_chip(setup_synth_md['datestamp'])}</div>
  {setup_synth_md['html']}
</div>
"""


# Section 02 — News Coverage & Reactions ─────────────────────────────────────
def render_news_section(news: dict, events: dict) -> str:
    pubs = news.get("publishers") or []
    pub_chips = ""
    if pubs:
        pub_chips = '<div class="pub-row">' + "".join(
            f'<span class="pub-chip">{p["source"]} <span class="pub-count">{p["count"]}</span></span>'
            for p in pubs
        ) + "</div>"

    article_rows = ""
    for a in news.get("articles", []):
        topic_color = TOPIC_COLORS.get(a["topic"], "#999")
        url_html = f'<a href="{a["url"]}" target="_blank" rel="noopener">{a["headline"]}</a>' if a["url"] else a["headline"]
        article_rows += f"""
<tr>
  <td class="muted-cell">{a['date']}</td>
  <td>{url_html}</td>
  <td class="muted-cell">{a['source']}</td>
  <td><span class="topic-chip" style="background:{topic_color}22;color:{topic_color}">{TOPIC_LABELS.get(a['topic'], a['topic'])}</span></td>
</tr>"""

    return f"""
<div class="section-header" id="news">
  <div class="section-num">SECTION 02</div>
  <div class="section-title">News Coverage &amp; Reactions <span class="muted-cell" style="font-size:11.5px;font-weight:500">· {news.get('total', 0)} articles tracked</span></div>
  <div class="section-blurb">
    The hero chart overlays meaningful news events on the stock line — every red downgrade, the
    +3.6% Apr-2 first-positive reaction, the May 7 cycle-low. Below: classic cadence + topic mix
    and an expandable full article log.
  </div>
</div>

<div class="chart-card">
  <h3>VITL Daily Close (18 months) · Event Reactions Overlaid</h3>
  <div class="chart-wrap tall"><canvas id="eventsChart"></canvas></div>
  <div class="event-legend">
    <span class="legend-dot" style="background:{REACTION_COLORS['negative']}"></span> Negative reaction
    <span class="legend-dot" style="background:{REACTION_COLORS['flat']};margin-left:14px"></span> Flat
    <span class="legend-dot" style="background:{REACTION_COLORS['positive']};margin-left:14px"></span> Positive
  </div>
  {source_caption("Stock = <code>vitl_stock.csv</code>; events = <code>event_reactions.csv</code> (purpose-built for this chart). Hover any dot for headline + summary + reaction %.")}
  {refresh_footer(DATA_DIR / "event_reactions.csv")}
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

<details class="article-log">
  <summary>Full article log · {len(news.get('articles', []))} most recent</summary>
  <div class="table-card" style="margin-top:8px">
  <table>
    <thead><tr><th>Date</th><th>Headline</th><th>Source</th><th>Topic</th></tr></thead>
    <tbody>{article_rows}</tbody>
  </table>
  </div>
</details>
{source_caption("Articles: GDELT ArtList primary, Google News RSS fallback. Topics classified by keyword dict in <code>fetch_google_news.py</code>.")}
{refresh_footer(DATA_DIR / "news_articles.csv")}
"""


# Section 03 — Egg Market Price Gap ──────────────────────────────────────────
def render_egg_market(egg: dict) -> str:
    md = load_markdown(READS_DIR / "egg_market_take.md")
    hpai_text = "—"
    if egg.get("hpai_latest"):
        hl = egg["hpai_latest"]
        hpai_text = f"<strong>{hl['cases']}</strong> commercial-layer cases (week of {hl['week']})"
    flock_text = "—"
    if egg.get("flock_latest"):
        fl = egg["flock_latest"]
        flock_text = f"<strong>{fl['millions']:.1f}M</strong> hens (as of {fl['month']})"

    peak_str = f"{egg['peak_gap']:.0f}%" if egg.get("peak_gap") is not None else "—"
    latest_str = f"{egg['latest_gap']:.0f}%" if egg.get("latest_gap") is not None else "—"

    return f"""
<div class="section-header" id="egg-market">
  <div class="section-num">SECTION 03</div>
  <div class="section-title">The Egg Market — Price Gap Tracker</div>
  <div class="section-subtitle">VITL retail vs conventional wholesale. The single most analytically unique panel — nobody publishes this gap anywhere.</div>
</div>

<div class="hero-row">
  <div class="hero-tile">
    <div class="hero-label">Latest VITL-to-Conventional Gap</div>
    <div class="hero-val">{latest_str}</div>
    <div class="hero-sub">historical norm 150-200%</div>
  </div>
  <div class="hero-tile">
    <div class="hero-label">Peak Gap (this cycle)</div>
    <div class="hero-val neg">{peak_str}</div>
    <div class="hero-sub">widest since 2023</div>
  </div>
  <div class="hero-tile">
    <div class="hero-label">HPAI Commercial Cases</div>
    <div class="hero-val" style="font-size:18px;line-height:1.5">{hpai_text}</div>
  </div>
  <div class="hero-tile">
    <div class="hero-label">USDA Layer Flock</div>
    <div class="hero-val" style="font-size:18px;line-height:1.5">{flock_text}</div>
  </div>
</div>

<div class="chart-card">
  <h3>The Premium Gap — Conventional Wholesale vs VITL Retail vs Gap %</h3>
  <div class="chart-wrap tall"><canvas id="eggGapChart"></canvas></div>
  {source_caption("Conventional shell egg = USDA AMS weekly (seeded; MARS API fetcher TBD). VITL retail = manual snapshots from in-store checks + earnings-call commentary, monthly forward-filled to weekly. Gap % = (VITL/Conv − 1) × 100.")}
  {refresh_footer(DATA_DIR / "usda_eggs_weekly.csv")}
</div>

<div class="chart-card">
  <h3>Breaker Egg Market (USDA AMS, 2-yr weekly)</h3>
  <div class="chart-wrap"><canvas id="breakerChart"></canvas></div>
  <div class="callout-strip">
    Crashed from $1.00/dz (Q1 25) to ~$0.10/dz (Q1 26). Drove $32M of supply-management costs
    in 2026. Eggs VITL can't sell branded go here at spot — every dime higher = direct margin tailwind.
  </div>
  {refresh_footer(DATA_DIR / "breaker_prices.csv")}
</div>

<div class="egg-take">
  <div class="take-eyebrow">EGG MARKET TAKE {datestamp_chip(md['datestamp'])}</div>
  {md['html']}
</div>
"""


# Section 04 — Consumer Demand & Brand Health ─────────────────────────────────
def render_community(comm: dict) -> str:
    md = load_markdown(READS_DIR / "brand_health_take.md")
    if not comm["sub_rows"]:
        body = '<div class="placeholder">No subreddits in <code>config/reddit_subreddits.csv</code> yet.</div>'
    else:
        rows_html = ""
        for r in comm["sub_rows"]:
            yoy = r["yoy_pct"]
            yoy_cls = ""
            if yoy is not None:
                yoy_cls = "badge-pos" if yoy >= 0 else "badge-neg"
            yoy_html = (f'<span class="badge {yoy_cls}">{fmt_pct(yoy)}</span>'
                        if yoy is not None else '<span class="muted-cell">—</span>')
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
            f'<div class="stat-lbl">{k}</div></div>' for k, v in top
        ) + "</div>"

    return f"""
<div class="section-header" id="community">
  <div class="section-num">SECTION 04</div>
  <div class="section-title">Consumer Demand &amp; Brand Health</div>
  <div class="section-blurb">
    Reddit mention volume across 15 food/health/value subs + 6-brand share of voice + linoleic-acid
    controversy decay. Tests whether competitors took mindshare during the ERP shelf-gap, and whether
    the January 2026 seed-oil narrative actually moved purchase intent.
  </div>
</div>
{body}
{source_caption("Reddit data from Arctic Shift archive (<code>fetch_reddit_arctic.py</code>), title-only match on \"vital farms\".")}
{refresh_footer(DATA_DIR / "reddit_mentions_weekly.csv")}

<div class="chart-card">
  <h3>Brand Share of Voice — Pasture-Raised Egg Set (Weekly Reddit Mentions, 36mo)</h3>
  <div class="chart-wrap big"><canvas id="brandSovChart"></canvas></div>
  {source_caption("Six-brand stacked area from <code>fetch_competitor_mentions.py</code>. Brands with 0 hits shown as flat lines so the universe is always visible. Red vertical = Feb 26 2026 print.")}
  {refresh_footer(DATA_DIR / "competitor_mentions_weekly.csv")}
</div>
{brand_totals_html}

<div class="chart-card">
  <h3>Linoleic-Acid / Seed-Oil Controversy Decay (Weekly, 12mo)</h3>
  <div class="chart-wrap"><canvas id="linoleicChart"></canvas></div>
  <div class="callout-strip">
    January 2026 spike, then decay. Management says "negligible purchase impact" — chart tests
    that claim weekly. Source subs: r/seedoilfree, r/Carnivore, r/nutrition.
  </div>
  {refresh_footer(DATA_DIR / "linoleic_decay_weekly.csv")}
</div>

<div class="egg-take">
  <div class="take-eyebrow">BRAND HEALTH TAKE {datestamp_chip(md['datestamp'])}</div>
  {md['html']}
</div>
"""


# Section 05 — Credibility Scorecard ──────────────────────────────────────────
def render_credibility(cred: dict) -> str:
    md = load_markdown(READS_DIR / "credibility_take.md")
    if not cred["rows"]:
        body = '<div class="placeholder">No rows in <code>data/guidance_vs_actual.csv</code> yet.</div>'
    else:
        rows_html = ""
        for r in cred["rows"]:
            dk = r["delta_kind"]
            badge = {"miss": "badge-neg", "beat": "badge-pos", "cut": "badge-neg"}.get(dk, "badge-na")
            rows_html += f"""
<tr>
  <td><strong>{r['period']}</strong></td>
  <td>{r['metric']}</td>
  <td>{r['management_said']}</td>
  <td>{r['actual']}</td>
  <td><span class="badge {badge}">{r['delta']}</span></td>
</tr>"""
        body = f"""
<div class="table-card">
<table>
<thead><tr>
  <th>Period</th><th>Metric</th><th>Management Said</th><th>Actual</th><th>Delta</th>
</tr></thead>
<tbody>{rows_html}</tbody>
</table>
</div>"""

    return f"""
<div class="section-header" id="credibility">
  <div class="section-num">SECTION 05</div>
  <div class="section-title">Did Management Tell Us The Truth?</div>
  <div class="section-subtitle">Credibility scorecard — guidance accuracy over time. The trajectory matters more than any single line.</div>
</div>
{body}
{refresh_footer(DATA_DIR / "guidance_vs_actual.csv")}

<div class="egg-take">
  <div class="take-eyebrow">CREDIBILITY TAKE {datestamp_chip(md['datestamp'])}</div>
  {md['html']}
</div>
"""


# Archived sections ──────────────────────────────────────────────────────────
def render_archived() -> str:
    return f"""
<div class="section-header archived-header" id="archived">
  <div class="section-num">ARCHIVED</div>
  <div class="section-title">Placeholders · archived from nav</div>
  <div class="section-subtitle">
    Old Retail Distribution, SKU Heat Map, Pricing Power, Supply Risk, and Demand-vs-Stock placeholders.
    Their content was either never sourced or has been folded into the new sections above. Kept on
    page for completeness; dropped from top nav.
  </div>
</div>

<details class="archived-block">
  <summary>Retail Distribution (was Section 02) <span class="placeholder-tag">PLACEHOLDER · ARCHIVED</span></summary>
  <p class="muted-cell">Pending Instacart cross-banner proxy. The new Egg Market section (03) is the active replacement for retail-shelf signal.</p>
</details>

<details class="archived-block">
  <summary>SKU Heat Map (was Section 03) <span class="placeholder-tag">PLACEHOLDER · ARCHIVED</span></summary>
  <p class="muted-cell">Per-SKU Reddit/YouTube/Search splits pending. Bypassed for this pass — Section 04 (Brand Share of Voice + linoleic decay) covers the consumer-mindshare question more directly.</p>
</details>

<details class="archived-block">
  <summary>Pricing Power (was Section 06) <span class="placeholder-tag">PLACEHOLDER · ARCHIVED</span></summary>
  <p class="muted-cell">Subsumed by Section 03 (Egg Market Price Gap), which renders the same conventional-vs-premium juxtaposition with USDA weekly + manual VITL retail snapshots.</p>
</details>

<details class="archived-block">
  <summary>Supply Risk / Avian Flu (was Section 07) <span class="placeholder-tag">PLACEHOLDER · ARCHIVED</span></summary>
  <p class="muted-cell">Subsumed by Section 03 inline notes (HPAI cases this week + USDA layer flock). Same data, more useful context next to the price-gap chart.</p>
</details>

<details class="archived-block">
  <summary>Demand vs Stock (was Section 08) <span class="placeholder-tag">PLACEHOLDER · ARCHIVED</span></summary>
  <p class="muted-cell">Replaced by Section 02 (News Coverage &amp; Reactions) hero chart, which overlays event dots with reaction tooltips — much more informative than an abstract demand z-score.</p>
</details>
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
      <div class="modal-section-title">Current state</div>
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
    setup    = compute_setup(d)
    events   = compute_events(d)
    news     = compute_news(d)
    egg      = compute_egg_market(d)
    comm     = compute_community(d)
    cred     = compute_credibility(d)
    summary  = compute_summary(d, recovery, setup, news, egg, cred)

    chart_blob = json.dumps({
        "recovery":     recovery,
        "setup":        setup,
        "events":       events,
        "news":         news,
        "egg":          egg,
        "comm":         comm,
        "topic_colors": TOPIC_COLORS,
        "topic_labels": TOPIC_LABELS,
        "brand_colors": BRAND_SOV_COLORS,
        "brand_order":  BRAND_SOV_ORDER,
        "reaction_colors": REACTION_COLORS,
        "accent":     BRAND_ACCENT, "accent2": BRAND_ACCENT2,
        "accent3":    BRAND_ACCENT3, "accent_neg": BRAND_ACCENT4,
        "purple":     BRAND_PURPLE,
    })

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

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
    --bg:#fbf8ef; --surface:#ffffff; --surface2:#f7f3e6;
    --border:#e4dccd; --border-strong:#d4c8ad;
    --text:#2b2f25; --text-soft:#4a4f3f; --muted:#8b8b78;
    --accent:{BRAND_ACCENT}; --accent2:{BRAND_ACCENT2}; --accent3:{BRAND_ACCENT3};
    --pos:{BRAND_ACCENT}; --neg:{BRAND_ACCENT4};
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
  .topbar h1 {{ font-size: 16px; font-weight: 700; letter-spacing: -0.3px; }}
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
                  border-radius: 999px; padding: 7px 16px; font-size: 12px;
                  font-weight: 700; letter-spacing: 0.3px; cursor: pointer; white-space: nowrap; }}
  .summary-btn:hover {{ background: #24482f; transform: translateY(-1px); }}

  .container {{ max-width: 1280px; margin: 0 auto; padding: 24px 32px; }}

  .section-header {{ margin: 44px 0 14px; padding-bottom: 10px; border-bottom: 1px solid var(--border); }}
  .section-header:first-of-type {{ margin-top: 0; }}
  .section-header.archived-header {{ opacity: 0.7; }}
  .section-num {{ font-size: 10px; font-weight: 700; color: var(--accent); letter-spacing: 1.8px; }}
  .section-title {{ font-size: 21px; font-weight: 700; margin-top: 4px; letter-spacing: -0.4px; }}
  .section-subtitle {{ font-size: 13px; color: var(--text-soft); margin-top: 6px; font-style: italic; }}
  .section-blurb {{ font-size: 13px; color: var(--text-soft); line-height: 1.6;
                    margin-top: 12px; padding: 12px 16px; max-width: 880px;
                    background: #fef9ec; border: 1px solid #f2e4b6;
                    border-left: 4px solid var(--accent2); border-radius: 6px; }}
  .section-blurb strong {{ color: var(--text); font-weight: 700; }}

  .placeholder-tag {{ display: inline-block; margin-left: 8px; font-size: 9.5px;
                      font-weight: 700; padding: 2px 8px; border-radius: 999px;
                      background: #eee7d6; color: #8a6b10; letter-spacing: 0.5px;
                      text-transform: uppercase; }}
  .datestamp {{ display: inline-block; font-size: 11px; color: var(--muted); font-weight: 500;
                margin-left: 8px; }}
  .refresh-tag {{ font-size: 10.5px; color: var(--muted); margin-top: 8px; }}
  .refresh-tag code {{ color: var(--accent); font-family: 'SF Mono', Menlo, Consolas, monospace; font-size: 10.5px; }}

  /* What's Changed callout */
  .whats-new-card {{ background: linear-gradient(180deg, #fffdf2, #fef7d8);
                     border: 1px solid #ecd47c; border-left: 5px solid {BRAND_ACCENT2};
                     border-radius: 10px; padding: 18px 24px; margin: 14px 0 26px; }}
  .wn-header {{ display: flex; align-items: center; margin-bottom: 10px; }}
  .wn-eyebrow {{ font-size: 10.5px; font-weight: 700; color: #8a6b10;
                 letter-spacing: 1.6px; }}
  .wn-body p {{ font-size: 13.5px; color: var(--text-soft); margin-bottom: 8px; line-height: 1.65; }}
  .wn-body p:last-child {{ margin-bottom: 0; }}
  .wn-body strong {{ color: var(--text); font-weight: 700; }}

  .hero-row {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 14px; }}
  @media (max-width: 1024px) {{ .hero-row {{ grid-template-columns: 1fr 1fr; }} }}
  .hero-tile {{ background: var(--surface); border: 1px solid var(--border);
                border-radius: 10px; padding: 20px 22px; box-shadow: 0 1px 3px rgba(45,47,37,0.04); }}
  .hero-label {{ font-size: 10px; color: var(--muted); text-transform: uppercase;
                 letter-spacing: 0.8px; margin-bottom: 10px; font-weight: 700; }}
  .hero-val {{ font-size: 30px; font-weight: 700; letter-spacing: -0.6px; }}
  .hero-val.pos {{ color: var(--accent); }}
  .hero-val.neg {{ color: var(--neg); }}
  .hero-val-suffix {{ font-size: 12px; color: var(--muted); font-weight: 500; margin-left: 8px; }}
  .hero-sub {{ font-size: 11.5px; color: var(--muted); margin-top: 6px; }}

  .chart-card {{ background: var(--surface); border: 1px solid var(--border);
                 border-radius: 10px; padding: 20px 22px; margin-bottom: 14px;
                 box-shadow: 0 1px 3px rgba(45,47,37,0.04); }}
  .chart-card h3 {{ font-size: 14px; font-weight: 700; margin-bottom: 14px; }}
  .chart-wrap {{ position: relative; height: 300px; }}
  .chart-wrap.big {{ height: 380px; }}
  .chart-wrap.tall {{ height: 460px; }}

  .source-caption {{ font-size: 10.5px; color: var(--muted); line-height: 1.55;
                     margin-top: 12px; padding-top: 10px;
                     border-top: 1px dashed var(--border); font-style: italic; }}
  .source-caption code {{ color: var(--accent); font-family: 'SF Mono', Menlo, Consolas, monospace;
                          font-size: 10.5px; font-style: normal;
                          background: rgba(46,90,60,0.08); padding: 1px 5px; border-radius: 3px; }}
  .callout-strip {{ background: rgba(46,90,60,0.05); border-left: 3px solid var(--accent);
                    padding: 10px 14px; font-size: 12.5px; color: var(--text-soft);
                    border-radius: 4px; margin-top: 12px; line-height: 1.5; }}

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
  td {{ padding: 10px 12px; border-bottom: 1px solid var(--border); font-size: 12.5px; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: rgba(46,90,60,0.04); }}
  td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  th.num {{ text-align: right; }}
  td.muted-cell, .muted-cell {{ color: var(--muted); }}

  .badge {{ display: inline-block; padding: 3px 8px; border-radius: 999px;
            font-size: 10px; font-weight: 700; letter-spacing: 0.3px; white-space: nowrap; }}
  .badge-pos {{ background: #e1f0dc; color: #2a5a30; }}
  .badge-neg {{ background: #f8e2dc; color: #b34738; }}
  .badge-na  {{ background: #eee7d6; color: #8b8271; }}
  .badge-mid {{ background: #fdefc9; color: #8a6b10; }}

  .placeholder {{ background: var(--surface2); border: 1px dashed var(--border-strong);
                  border-radius: 8px; padding: 22px 18px; text-align: center;
                  color: var(--muted); font-size: 12.5px; }}

  /* ERP timeline (Section 00) */
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

  /* Section 01 — The Setup grid */
  .setup-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 8px; }}
  @media (max-width: 1024px) {{ .setup-grid {{ grid-template-columns: 1fr; }} }}
  .setup-card {{ background: var(--surface); border: 1px solid var(--border);
                 border-radius: 10px; padding: 18px 20px;
                 box-shadow: 0 1px 3px rgba(45,47,37,0.04);
                 display: flex; flex-direction: column; }}
  .setup-card-header {{ margin-bottom: 12px; }}
  .setup-card-title {{ font-size: 14px; font-weight: 700; }}
  .setup-kpi {{ font-size: 12px; color: var(--accent); font-weight: 700;
                margin-top: 4px; letter-spacing: 0.3px; }}
  .setup-foot {{ font-size: 11.5px; color: var(--muted); margin-top: 10px;
                 padding-top: 10px; border-top: 1px dashed var(--border);
                 line-height: 1.55; font-style: italic; }}
  .setup-buyback .buyback-body {{ font-size: 13px; color: var(--text-soft);
                                  line-height: 1.7; padding: 8px 0; }}
  .setup-buyback .buyback-body p:first-child {{ font-size: 28px; font-weight: 700;
                                                color: var(--accent); margin-bottom: 8px;
                                                letter-spacing: -0.4px; }}
  .setup-buyback .buyback-body p:first-child strong {{ color: var(--accent); }}
  .setup-buyback .buyback-body p {{ margin-bottom: 10px; }}
  .setup-buyback .buyback-body strong {{ color: var(--text); }}
  .setup-synthesis {{ background: linear-gradient(180deg, #f8f9f5, #fdf3d3);
                      border: 1px solid #e6d28c; border-radius: 10px;
                      padding: 16px 22px; margin-top: 16px; }}
  .setup-synth-eyebrow {{ font-size: 10.5px; font-weight: 700; color: #8a6b10;
                          letter-spacing: 1.5px; margin-bottom: 8px; }}
  .setup-synthesis p {{ font-size: 13px; color: var(--text-soft); line-height: 1.65; }}

  /* Section 02 — event chart legend */
  .event-legend {{ display: flex; align-items: center; font-size: 11.5px;
                   color: var(--muted); margin-top: 8px; gap: 4px; }}
  .legend-dot {{ display: inline-block; width: 9px; height: 9px; border-radius: 50%;
                 margin-right: 5px; }}
  .article-log {{ margin-top: 14px; }}
  .article-log summary {{ font-size: 12.5px; font-weight: 600; color: var(--accent);
                          cursor: pointer; padding: 8px 12px; border: 1px solid var(--border);
                          border-radius: 6px; background: var(--surface); }}
  .article-log summary:hover {{ background: rgba(46,90,60,0.04); }}
  .article-log[open] summary {{ background: rgba(46,90,60,0.04); border-bottom-left-radius: 0;
                                border-bottom-right-radius: 0; border-bottom: none; }}
  .topic-chip {{ display: inline-block; font-size: 10px; font-weight: 600;
                 padding: 3px 8px; border-radius: 999px; }}

  /* Section 03 — egg market take callout */
  .egg-take {{ background: linear-gradient(180deg, #f8f9f5, #f0f4eb);
               border: 1px solid #cfdbb9; border-left: 4px solid var(--accent);
               border-radius: 10px; padding: 16px 22px; margin-top: 16px; }}
  .take-eyebrow {{ font-size: 10.5px; font-weight: 700; color: var(--accent);
                   letter-spacing: 1.5px; margin-bottom: 8px; }}
  .egg-take p {{ font-size: 13px; color: var(--text-soft); line-height: 1.65; margin-bottom: 10px; }}
  .egg-take p:last-child {{ margin-bottom: 0; }}

  /* Stat row */
  .stat-row {{ display: flex; gap: 12px; margin-top: 10px; flex-wrap: wrap; }}
  .stat-card {{ background: var(--surface); border: 1px solid var(--border);
                border-radius: 10px; padding: 12px 18px; min-width: 130px; flex: 1 1 130px;
                box-shadow: 0 1px 3px rgba(45,47,37,0.04); }}
  .stat-val {{ font-size: 22px; font-weight: 700; letter-spacing: -0.4px; }}
  .stat-lbl {{ font-size: 10px; color: var(--muted); text-transform: uppercase;
               letter-spacing: 0.7px; margin-top: 4px; font-weight: 600; }}

  .pub-row {{ display: flex; flex-wrap: wrap; gap: 6px; margin: 4px 0 0; }}
  .pub-chip {{ background: var(--surface2); border: 1px solid var(--border);
               border-radius: 999px; padding: 4px 12px; font-size: 11.5px; color: var(--text-soft); }}
  .pub-count {{ color: var(--muted); margin-left: 6px; font-variant-numeric: tabular-nums; }}

  /* Archived */
  .archived-block {{ margin-bottom: 8px; opacity: 0.8; }}
  .archived-block summary {{ font-size: 12.5px; font-weight: 600; color: var(--text-soft);
                             cursor: pointer; padding: 10px 14px; border: 1px solid var(--border);
                             border-radius: 6px; background: var(--surface2); }}
  .archived-block summary:hover {{ background: #efe9d5; }}
  .archived-block p {{ font-size: 12.5px; color: var(--muted); line-height: 1.6;
                       padding: 12px 14px; }}

  /* Modal */
  .modal-backdrop {{ display: none; position: fixed; inset: 0;
                     background: rgba(20,22,15,0.5); z-index: 200;
                     align-items: flex-start; justify-content: center; padding: 60px 20px; }}
  .modal {{ background: var(--surface); border: 1px solid var(--border);
            border-radius: 12px; max-width: 720px; width: 100%;
            box-shadow: 0 8px 32px rgba(0,0,0,0.18); overflow: hidden; }}
  .modal-header {{ display: flex; justify-content: space-between; align-items: flex-start;
                   padding: 22px 26px 14px; border-bottom: 1px solid var(--border); }}
  .modal-title {{ font-size: 17px; font-weight: 700; }}
  .modal-sub {{ font-size: 11px; color: var(--muted); margin-top: 3px; }}
  .modal-close {{ background: transparent; border: none; font-size: 24px; color: var(--muted);
                  cursor: pointer; line-height: 1; padding: 0 4px; }}
  .modal-body {{ padding: 18px 26px 26px; max-height: 70vh; overflow-y: auto; }}
  .modal-section-title {{ font-size: 10.5px; text-transform: uppercase; letter-spacing: 1.2px;
                          color: var(--accent); font-weight: 700; margin: 14px 0 8px; }}
  .modal-list {{ list-style: none; padding-left: 0; font-size: 13px; color: var(--text-soft); line-height: 1.7; }}
  .modal-list li {{ padding: 5px 0 5px 16px; border-bottom: 1px dashed var(--border); position: relative; }}
  .modal-list li:before {{ content: "›"; position: absolute; left: 0; color: var(--accent); font-weight: 700; }}
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
    <a class="nav-btn" href="#setup">The Setup</a>
    <a class="nav-btn" href="#news">News</a>
    <a class="nav-btn" href="#egg-market">Egg Market</a>
    <a class="nav-btn" href="#community">Demand</a>
    <a class="nav-btn" href="#credibility">Credibility</a>
  </div>
  <button class="summary-btn" onclick="document.getElementById('summaryModal').style.display='flex'">
    Generate Summary
  </button>
</div>

{render_top_callout()}

<div class="container">
  {render_recovery(recovery)}
  {render_setup(setup)}
  {render_news_section(news, events)}
  {render_egg_market(egg)}
  {render_community(comm)}
  {render_credibility(cred)}
  {render_archived()}
</div>

<footer>
  {BRAND_NAME} ({BRAND_TICKER}) Recovery Dashboard · generated {generated_at}
</footer>

{render_summary_modal(summary)}

<script>
  window.__vitl = {chart_blob};

  // Vertical-line + band plugin (used by Sections 00, 02, 04)
  const refLinePlugin = {{
    id: 'refLine',
    beforeDraw(chart, args, opts) {{
      const refs = opts.refs || []; const bands = opts.bands || [];
      const {{ ctx, chartArea, scales }} = chart;
      if (!scales.x || !chartArea) return;
      ctx.save();
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
        ctx.lineWidth = r.width || 2; ctx.setLineDash(r.dash || [4, 4]);
        ctx.beginPath(); ctx.moveTo(x, chartArea.top); ctx.lineTo(x, chartArea.bottom); ctx.stroke();
        if (r.label) {{
          ctx.setLineDash([]); ctx.fillStyle = r.color || '#C95D4A';
          ctx.font = '10.5px Inter, system-ui, sans-serif'; ctx.textAlign = 'center';
          ctx.fillText(r.label, x, chartArea.top + 12);
        }}
      }}
      ctx.restore();
    }},
  }};
  Chart.register(refLinePlugin);

  document.addEventListener('DOMContentLoaded', () => {{
    const d = window.__vitl;
    const A = d.accent, A2 = d.accent2, A3 = d.accent3, NEG = d.accent_neg;

    // ─── Section 00 — Recovery stock chart ────────────────────────────────
    const rec = d.recovery;
    new Chart(document.getElementById('recoveryStockChart'), {{
      type: 'line',
      data: {{
        labels: rec.stock_series.dates,
        datasets: [{{ label: 'VITL Close', data: rec.stock_series.close,
                      borderColor: A, backgroundColor: 'rgba(46,90,60,0.08)',
                      borderWidth: 2, tension: 0.15, pointRadius: 0, fill: true }}],
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{
          legend: {{ display: false }},
          refLine: {{
            bands: [{{ start: rec.class_period_start, end: rec.class_period_end, color: 'rgba(201,93,74,0.08)' }}],
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

    // ─── Section 01 — Cash position bar chart ─────────────────────────────
    const setup = d.setup;
    const cashLabels = setup.cash_rows.map(r => r.label);
    const cashVals   = setup.cash_rows.map(r => r.tbd ? null : r.value);
    const cashColors = setup.cash_rows.map(r => r.tbd ? 'rgba(46,90,60,0.18)' : (r.value < 80 ? NEG : A));
    new Chart(document.getElementById('cashChart'), {{
      type: 'bar',
      data: {{
        labels: cashLabels,
        datasets: [{{ label: 'Cash ($M)', data: cashVals, backgroundColor: cashColors,
                      borderColor: setup.cash_rows.map(r => r.tbd ? A : 'transparent'),
                      borderWidth: 2, borderRadius: 4,
                      borderDash: setup.cash_rows.map(r => r.tbd ? [5,3] : []) }}],
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{
          legend: {{ display: false }},
          tooltip: {{ callbacks: {{
            label: ctx => ctx.raw == null ? 'TBD (Q2 print pending)' : '$' + ctx.raw.toFixed(1) + 'M',
            afterBody: ctx => {{
              const row = setup.cash_rows[ctx[0].dataIndex];
              return row && row.note ? row.note : '';
            }},
          }} }},
        }},
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }} }} }},
          y: {{ grid: {{ color: 'rgba(0,0,0,0.05)' }}, ticks: {{ font: {{ size: 10 }}, callback: v => '$' + v + 'M' }} }},
        }},
      }},
    }});

    // ─── Section 01 — Short interest line chart ───────────────────────────
    const sh = setup.short_series;
    new Chart(document.getElementById('shortChart'), {{
      type: 'line',
      data: {{
        labels: sh.dates,
        datasets: [{{ label: '% of Float Short', data: sh.pct, borderColor: NEG,
                      backgroundColor: 'rgba(201,93,74,0.08)', borderWidth: 2, tension: 0.25,
                      pointRadius: (ctx) => ctx.dataIndex === sh.pct.length - 1 ? 5 : 0,
                      pointBackgroundColor: NEG, fill: true }}],
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{
          legend: {{ display: false }},
          tooltip: {{ callbacks: {{ label: ctx => ctx.raw.toFixed(1) + '%' }} }},
        }},
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }}, maxTicksLimit: 6, autoSkip: true }} }},
          y: {{ grid: {{ color: 'rgba(0,0,0,0.05)' }}, ticks: {{ font: {{ size: 10 }}, callback: v => v + '%' }} }},
        }},
      }},
    }});

    // ─── Section 02 — Stock with event dots ───────────────────────────────
    const ev = d.events;
    const eventDots = ev.events.map(e => ({{x: e.date, y: e.close}}));
    new Chart(document.getElementById('eventsChart'), {{
      type: 'line',
      data: {{
        labels: ev.dates,
        datasets: [
          {{ label: 'VITL Close', data: ev.close, borderColor: A,
             backgroundColor: 'rgba(46,90,60,0.06)', borderWidth: 2, pointRadius: 0,
             tension: 0.15, fill: true, order: 2 }},
          {{ label: 'News Events', data: eventDots, showLine: false,
             pointRadius: 8, pointHoverRadius: 11,
             pointBackgroundColor: ev.events.map(e => d.reaction_colors[e.reaction_kind] || '#999'),
             pointBorderColor: '#fff', pointBorderWidth: 2,
             order: 1, parsing: false }},
        ],
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{
          legend: {{ display: false }},
          refLine: {{
            bands: [{{ start: ev.class_period_start, end: ev.class_period_end, color: 'rgba(201,93,74,0.06)' }}],
          }},
          tooltip: {{ mode: 'nearest', intersect: true, callbacks: {{
            title: ctx => {{
              if (ctx[0].datasetIndex === 1) {{
                const e = ev.events[ctx[0].dataIndex];
                return e ? `${{e.date}} · ${{e.reaction_pct == null ? '—' : (e.reaction_pct > 0 ? '+' : '') + e.reaction_pct.toFixed(1) + '%'}}` : '';
              }}
              return ctx[0].label;
            }},
            label: ctx => {{
              if (ctx.datasetIndex === 1) {{
                const e = ev.events[ctx.dataIndex];
                if (!e) return '';
                return [e.headline, e.summary].filter(Boolean);
              }}
              return '$' + Number(ctx.raw).toFixed(2);
            }},
          }} }},
        }},
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }}, maxTicksLimit: 10, autoSkip: true }} }},
          y: {{ grid: {{ color: 'rgba(0,0,0,0.05)' }}, ticks: {{ font: {{ size: 10 }}, callback: v => '$' + v }} }},
        }},
      }},
    }});

    // ─── Section 02 — Cadence + Topic Mix (existing) ──────────────────────
    const cadence = d.news.cadence || {{ weeks: [], counts: [] }};
    new Chart(document.getElementById('newsCadenceChart'), {{
      type: 'bar',
      data: {{ labels: cadence.weeks,
               datasets: [{{ label: 'Articles', data: cadence.counts, backgroundColor: A, borderRadius: 3 }}] }},
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
      data: {{ labels: topicKeys.map(k => d.topic_labels[k] || k),
               datasets: [{{ data: topicKeys.map(k => topics[k]),
                             backgroundColor: topicKeys.map(k => d.topic_colors[k] || '#999'),
                             borderWidth: 0 }}] }},
      options: {{ responsive: true, maintainAspectRatio: false,
                  plugins: {{ legend: {{ position: 'right', labels: {{ font: {{ size: 11 }} }} }} }} }},
    }});

    // ─── Section 03 — Egg market premium gap ──────────────────────────────
    const egg = d.egg;
    new Chart(document.getElementById('eggGapChart'), {{
      type: 'line',
      data: {{
        labels: egg.gap_weeks,
        datasets: [
          {{ label: 'Conventional Wholesale ($/dz)', data: egg.conv_prices, borderColor: '#6b94b1',
             backgroundColor: 'transparent', borderWidth: 2, tension: 0.25, pointRadius: 0,
             yAxisID: 'yPrice', order: 2 }},
          {{ label: 'VITL Retail ($/dz, est.)', data: egg.vitl_prices, borderColor: A,
             backgroundColor: 'transparent', borderWidth: 2, borderDash: [5,3], tension: 0.1, pointRadius: 0,
             yAxisID: 'yPrice', order: 2, spanGaps: true }},
          {{ label: 'Premium Gap (%)', data: egg.gap_pcts, borderColor: A2,
             backgroundColor: 'rgba(244,196,48,0.18)', borderWidth: 1, tension: 0.2,
             pointRadius: 0, fill: true, yAxisID: 'yGap', order: 3, spanGaps: true }},
        ],
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{
          legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }} }} }},
          tooltip: {{ mode: 'index', intersect: false }},
        }},
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }}, maxTicksLimit: 12, autoSkip: true }} }},
          yPrice: {{ position: 'left', title: {{ display: true, text: '$ / dozen', font: {{ size: 10 }} }},
                     grid: {{ color: 'rgba(0,0,0,0.04)' }}, ticks: {{ font: {{ size: 10 }}, callback: v => '$' + v }} }},
          yGap:   {{ position: 'right', title: {{ display: true, text: 'Gap %', font: {{ size: 10 }} }},
                     grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }}, callback: v => v + '%' }} }},
        }},
      }},
    }});

    // ─── Section 03 — Breaker market ──────────────────────────────────────
    new Chart(document.getElementById('breakerChart'), {{
      type: 'line',
      data: {{
        labels: egg.breaker.weeks,
        datasets: [{{ label: 'Breaker price ($/dz)', data: egg.breaker.prices, borderColor: NEG,
                      backgroundColor: 'rgba(201,93,74,0.10)', borderWidth: 2, tension: 0.25,
                      pointRadius: 0, fill: true }}],
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{ legend: {{ display: false }} }},
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }}, maxTicksLimit: 10, autoSkip: true }} }},
          y: {{ grid: {{ color: 'rgba(0,0,0,0.04)' }}, ticks: {{ font: {{ size: 10 }}, callback: v => '$' + v }} }},
        }},
      }},
    }});

    // ─── Section 04 — Brand Share of Voice ────────────────────────────────
    const sov = d.comm.brand_sov;
    const sovDatasets = d.brand_order
      .filter(b => sov.brands && sov.brands[b])
      .map(b => ({{
        label: b, data: sov.brands[b],
        borderColor: d.brand_colors[b] || '#999',
        backgroundColor: (d.brand_colors[b] || '#999') + '55',
        borderWidth: 1.5, fill: true, tension: 0.2, pointRadius: 0,
      }}));
    if (sovDatasets.length > 0 && sov.weeks.length > 0) {{
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

    // ─── Section 04 — Linoleic decay ──────────────────────────────────────
    const lin = d.comm.linoleic;
    new Chart(document.getElementById('linoleicChart'), {{
      type: 'line',
      data: {{
        labels: lin.weeks,
        datasets: [{{ label: 'Posts (weekly)', data: lin.counts, borderColor: d.purple,
                      backgroundColor: 'rgba(142,109,180,0.12)', borderWidth: 2, tension: 0.3,
                      pointRadius: 0, fill: true }}],
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{ legend: {{ display: false }} }},
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }}, maxTicksLimit: 8, autoSkip: true }} }},
          y: {{ grid: {{ color: 'rgba(0,0,0,0.04)' }}, ticks: {{ font: {{ size: 10 }} }} }},
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
    print(f"── {BRAND_NAME} ({BRAND_TICKER}) Recovery Dashboard v3 ──")
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
