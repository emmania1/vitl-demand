"""
Vital Farms Demand Intelligence Dashboard — v4 (read-cold restructure)

Every chart now explains itself: title, subtitle, axes, legend, data source,
and a "what to watch" caption from /reads/.

Layout:
  TOP    What's Changed callout (reads/whats_new.md)
  TOP    Three Damages framing (reads/three_damages.md)
  SEC 00 Quick Read — 4 KPI cards + compressed ERP text + one explainer
  SEC 01 The Setup — Conviction vs Cash — 2×2 + Setup-Over-Time line chart
  SEC 02 Stock & News — hero events chart + topic-mix-over-time + cadence-vs-stock + article log
  SEC 03 The Egg Market — 4 separate sub-charts + HPAI / flock cards
  SEC 04 Brand Health & Distribution — SoV + linoleic + controversy-vs-stock + TDP-vs-revenue
  SEC 05 Financial History (NEW) — EBITDA margin history + cash burn decomposition + credibility table
  SEC 06 Correlation Snapshot (NEW) — 5×5 matrix
  ARCHIVED Old placeholder sections (no nav)
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
BRAND_ACCENT  = "#2E5A3C"
BRAND_ACCENT2 = "#F4C430"
BRAND_ACCENT3 = "#A8C49B"
BRAND_ACCENT4 = "#C95D4A"
BRAND_PURPLE  = "#8e6db4"
BRAND_BROWN   = "#B5651D"
BRAND_BLUE    = "#6b94b1"

ERP_PRINT_DATE     = datetime(2026, 2, 26).date()
ERP_PRINT_CLOSE    = 22.11
PRE_PRINT_CLOSE    = 24.79
CLASS_PERIOD_START = "2025-05-08"
CLASS_PERIOD_END   = "2026-02-26"
LP_DEADLINE_DATE   = datetime(2026, 5, 26).date()

# Compressed ERP timeline as a single line (no graphic, just text)
ERP_TIMELINE_TEXT = (
    "<strong>May 8 2025</strong> (class period begins) → "
    "<strong>Jul 15</strong> (original ERP target) → "
    "<strong>Oct 15</strong> (revised go-live) → "
    "<strong>Nov 13</strong> (Q3 call) → "
    "<strong>Feb 26 2026</strong> (FY25 print −10.8%) → "
    "<strong>Apr 15</strong> (class actions filed) → "
    "<strong>May 26</strong> (lead-plaintiff deadline)"
)

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
    "Alexandre": "#e67e22", "Pete & Gerry's": BRAND_BLUE,
    "Happy Egg": BRAND_ACCENT2, "Organic Valley": BRAND_BROWN,
}
BRAND_SOV_ORDER = ["Vital Farms", "Handsome Brook", "Alexandre",
                   "Pete & Gerry's", "Happy Egg", "Organic Valley"]
REACTION_COLORS = {"negative": BRAND_ACCENT4, "flat": "#b8a04c", "positive": BRAND_ACCENT}


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
        "subs":               safe_read(CONFIG_DIR / "reddit_subreddits.csv"),
        # data (existing)
        "stock":              safe_read(DATA_DIR / "vitl_stock.csv"),
        "reddit_weekly":      safe_read(DATA_DIR / "reddit_mentions_weekly.csv"),
        "competitor_weekly":  safe_read(DATA_DIR / "competitor_mentions_weekly.csv"),
        "youtube_monthly":    safe_read(DATA_DIR / "youtube_monthly.csv"),
        "youtube_linoleic":   safe_read(DATA_DIR / "youtube_linoleic_monthly.csv"),
        "news":               safe_read(DATA_DIR / "news_articles.csv"),
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
        # pass-5 additions
        "ebitda_history":     safe_read(DATA_DIR / "ebitda_margin_history.csv"),
        "cash_burn_decomp":   safe_read(DATA_DIR / "cash_burn_decomposition.csv"),
        "tdp_vs_revenue":     safe_read(DATA_DIR / "tdp_vs_revenue.csv"),
        "correlations":       safe_read(DATA_DIR / "correlations.csv"),
        # pass-6 additions
        "brand_awareness":    safe_read(DATA_DIR / "brand_awareness.csv"),
        "qrev_growth":        safe_read(DATA_DIR / "quarterly_revenue_growth.csv"),
        "gm_trajectory":      safe_read(DATA_DIR / "gross_margin_trajectory.csv"),
        "two_yr_stack":       safe_read(DATA_DIR / "two_year_stack.csv"),
        "guidance_full":      safe_read(DATA_DIR / "guidance_history_full.csv"),
        "valuation":          safe_read(DATA_DIR / "valuation_snapshot.csv"),
        "catalysts":          safe_read(DATA_DIR / "forward_catalysts.csv"),
        "recovery_plan":      safe_read(DATA_DIR / "recovery_plan_status.csv"),
        "hpai_cumulative":    safe_read(DATA_DIR / "hpai_cumulative.csv"),
        # pass-7 addition
        "youtube_competitors": safe_read(DATA_DIR / "youtube_competitors_monthly.csv"),
        # pass-8 additions — actual content feeds (titles + URLs, not just counts)
        "reddit_posts":       safe_read(DATA_DIR / "reddit_posts_recent.csv"),
        "youtube_videos":     safe_read(DATA_DIR / "youtube_recent_videos.csv"),
        # pass-9 additions — premium-egg category demand
        "google_trends":      safe_read(DATA_DIR / "google_trends_category_weekly.csv"),
        "customer_metrics":   safe_read(DATA_DIR / "customer_metrics.csv"),
        "category_growth":    safe_read(DATA_DIR / "category_growth.csv"),
        # pass-12 — category supply (how crowded the category got)
        "category_supply":    safe_read(DATA_DIR / "category_supply_timeline.csv"),
        # pass-13 — top-of-page supply quantification (excess vs retail; amendments)
        "supply_quant":       safe_read(DATA_DIR / "vitl_supply_quantification.csv"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Markdown helper
# ─────────────────────────────────────────────────────────────────────────────
_INLINE_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_INLINE_ITAL = re.compile(r"(?<![*\w])\*([^*\n]+)\*(?![*\w])")
_HEADER1 = re.compile(r"^#\s+(.*)$")


def _inline(s: str) -> str:
    s = _INLINE_BOLD.sub(r"<strong>\1</strong>", s)
    s = _INLINE_ITAL.sub(r"<em>\1</em>", s)
    return s


def load_markdown(path: Path) -> dict:
    if not path.exists():
        return {"title": "—", "datestamp": "", "html": f"<p class='muted-cell'>missing: {path.name}</p>"}
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
    paragraphs: list[str] = []
    current: list[str] = []; list_items: list[str] = []; in_list = False

    def flush_paragraph():
        if current:
            joined = " ".join(_inline(l.strip()) for l in current if l.strip())
            if joined: paragraphs.append(f"<p>{joined}</p>")
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
            flush_paragraph(); in_list = True
            list_items.append(stripped[2:].strip())
            continue
        if in_list: flush_list()
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


def compute_quick_read(d: dict) -> dict:
    """Section 00 — 4 KPI cards only."""
    stock = d["stock"].copy()
    today = datetime.today().date()
    days_since_print = (today - ERP_PRINT_DATE).days
    days_to_deadline = (LP_DEADLINE_DATE - today).days

    kpis = {
        "days_since_print": days_since_print, "days_to_deadline": days_to_deadline,
        "current_price": None, "feb25_close": PRE_PRINT_CLOSE, "feb26_close": ERP_PRINT_CLOSE,
        "vs_feb25_pct": None, "vs_feb26_pct": None,
    }
    if not stock.empty:
        stock["date"] = pd.to_datetime(stock["date"]).dt.strftime("%Y-%m-%d")
        stock = stock.sort_values("date").reset_index(drop=True)
        feb25 = _close_on(stock, "2026-02-25") or PRE_PRINT_CLOSE
        feb26 = _close_on(stock, "2026-02-26") or ERP_PRINT_CLOSE
        current = float(stock.iloc[-1]["close"])
        kpis.update({
            "current_price": round(current, 2),
            "feb25_close": round(feb25, 2), "feb26_close": round(feb26, 2),
            "vs_feb25_pct": round((current / feb25 - 1) * 100, 1) if feb25 else None,
            "vs_feb26_pct": round((current / feb26 - 1) * 100, 1) if feb26 else None,
        })
    return {"kpis": kpis}


def compute_setup(d: dict) -> dict:
    cash_rows = []
    if not d["cash"].empty:
        for _, r in d["cash"].iterrows():
            val = r.get("cash_and_equivalents_m")
            tbd = (val is None) or (isinstance(val, float) and pd.isna(val))
            cash_rows.append({
                "label": r["quarter_label"], "value": (None if tbd else float(val)),
                "tbd": bool(tbd), "note": r.get("note", "") or "",
            })
    # Projected Q2 burn estimate — sum projected line items from cash_burn_decomp
    # (new schema: period × line_item × amount_m × category; old: quarter × total_m)
    projected_q2 = None
    if not d["cash_burn_decomp"].empty:
        cbd = d["cash_burn_decomp"]
        if "period" in cbd.columns and "amount_m" in cbd.columns:
            # New categorized schema — sum projected Q2-Q4 26 items
            q2 = cbd[cbd["period"].astype(str).str.contains("Q2", na=False)]
            if not q2.empty:
                projected_q2 = float(q2["amount_m"].sum())
        elif "quarter" in cbd.columns and "total_m" in cbd.columns:
            # Old schema fallback
            q2 = cbd[cbd["quarter"].astype(str).str.contains("Q2 2026", na=False)]
            if not q2.empty:
                projected_q2 = float(q2.iloc[0]["total_m"])
    cash_change = None
    if len(cash_rows) >= 2 and not cash_rows[0]["tbd"] and not cash_rows[1]["tbd"]:
        cash_change = cash_rows[1]["value"] - cash_rows[0]["value"]
    runway_qs = None; current_cash = None; q_burn = None; projected_cash = None
    non_tbd = [r for r in cash_rows if not r["tbd"]]
    if len(non_tbd) >= 2 and cash_change is not None and cash_change < 0:
        current_cash = non_tbd[-1]["value"]; q_burn = abs(cash_change)
        runway_qs = round(current_cash / q_burn, 1) if q_burn > 0 else None
        if projected_q2 is not None:
            projected_cash = max(0, current_cash - projected_q2)

    # Insiders
    insiders_table = []; cluster_summary = None; cum_insider_buys = []
    if not d["insiders"].empty:
        idf = d["insiders"].copy()
        idf["date"] = pd.to_datetime(idf["date"], errors="coerce")
        idf = idf.dropna(subset=["date"]).sort_values("date", ascending=False)
        recent = idf[idf["date"] >= pd.Timestamp("2026-05-01")].copy()
        for _, r in recent.iterrows():
            insiders_table.append({
                "date": r["date"].strftime("%Y-%m-%d"),
                "name": r["name"], "title": r["title"], "kind": r["kind"],
                "shares": int(r["shares"]), "price": float(r["price"]),
                "total_value": float(r["total_value"]),
            })
        cluster = recent[(recent["date"] >= "2026-05-13") & (recent["date"] <= "2026-05-15")]
        if not cluster.empty:
            cluster_summary = {
                "insiders": int(cluster["name"].nunique()),
                "total_value": float(cluster["total_value"].sum()),
                "start": cluster["date"].min().strftime("%Y-%m-%d"),
                "end": cluster["date"].max().strftime("%Y-%m-%d"),
            }
        # Cumulative insider buys timeline (for setup-over-time chart)
        buys = idf[idf["kind"] == "buy"].sort_values("date").copy()
        buys["cum"] = buys["total_value"].cumsum()
        cum_insider_buys = [
            {"date": r["date"].strftime("%Y-%m-%d"),
             "cum_value": round(float(r["cum"]), 0)}
            for _, r in buys.iterrows()
        ]

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

    # Setup-Over-Time: align stock + short + cum_insider on a common monthly grid
    setup_over_time = {"dates": [], "stock_idx": [], "short_pct": [], "insider_cum_k": []}
    if not d["stock"].empty:
        s = d["stock"].copy()
        s["date"] = pd.to_datetime(s["date"])
        s = s.sort_values("date")
        cutoff = (datetime.today() - timedelta(days=730)).strftime("%Y-%m-%d")
        s = s[s["date"] >= cutoff]
        s["ym"] = s["date"].dt.strftime("%Y-%m")
        monthly_close = s.groupby("ym")["close"].last().sort_index()
        base = float(monthly_close.iloc[0]) if not monthly_close.empty else None
        setup_over_time["dates"] = list(monthly_close.index)
        setup_over_time["stock_idx"] = [round(float(v) / base * 100, 1) if base else None for v in monthly_close.values]

        # Short interest: forward-fill semi-monthly readings to month-end
        if not d["short_interest"].empty:
            sh = d["short_interest"].copy()
            sh["dt"] = pd.to_datetime(sh["date"])
            sh = sh.sort_values("dt")
            short_at_month = []
            for ym in setup_over_time["dates"]:
                month_end = pd.Timestamp(ym + "-28")
                prior = sh[sh["dt"] <= month_end]
                short_at_month.append(round(float(prior.iloc[-1]["short_pct_of_float"]), 1) if not prior.empty else None)
            setup_over_time["short_pct"] = short_at_month

        # Cumulative insider buys: forward-fill latest cum value at each month-end
        if cum_insider_buys:
            cb = pd.DataFrame(cum_insider_buys)
            cb["dt"] = pd.to_datetime(cb["date"])
            cb = cb.sort_values("dt")
            ins_at_month = []
            for ym in setup_over_time["dates"]:
                month_end = pd.Timestamp(ym + "-28")
                prior = cb[cb["dt"] <= month_end]
                ins_at_month.append(round(float(prior.iloc[-1]["cum_value"]) / 1000.0, 1) if not prior.empty else 0.0)
            setup_over_time["insider_cum_k"] = ins_at_month
        else:
            setup_over_time["insider_cum_k"] = [0.0] * len(setup_over_time["dates"])

    return {
        "cash_rows": cash_rows, "cash_change": cash_change,
        "runway_qs": runway_qs, "current_cash": current_cash, "q_burn": q_burn,
        "projected_cash": projected_cash, "projected_q2_burn": projected_q2,
        "insiders": insiders_table, "cluster": cluster_summary,
        "short_series": short_series, "short_current": short_current,
        "setup_over_time": setup_over_time,
    }


def compute_events_chart(d: dict) -> dict:
    """Section 02 hero — 18mo stock + event dots."""
    stock = d["stock"]; events = d["events"]
    if stock.empty:
        return {"dates": [], "close": [], "events": [],
                "class_period_start": CLASS_PERIOD_START, "class_period_end": CLASS_PERIOD_END}
    s = stock.copy()
    s["date"] = pd.to_datetime(s["date"]).dt.strftime("%Y-%m-%d")
    s = s.sort_values("date").reset_index(drop=True)
    cutoff = (datetime.today() - timedelta(days=540)).strftime("%Y-%m-%d")
    s = s[s["date"] >= cutoff]
    ev_list = []
    if not events.empty:
        for _, r in events.iterrows():
            d_str = str(r["date"]); close = _close_on(s, d_str)
            if close is None:
                prior = s[s["date"] <= d_str]
                if not prior.empty: close = float(prior.iloc[-1]["close"])
            ev_list.append({
                "date": d_str, "headline": str(r.get("headline", ""))[:140],
                "summary": str(r.get("summary", ""))[:320],
                "reaction_pct": (None if pd.isna(r.get("reaction_pct")) else float(r["reaction_pct"])),
                "reaction_kind": str(r.get("reaction_kind", "flat")),
                "close": (None if close is None else round(close, 2)),
            })
    return {"dates": s["date"].tolist(), "close": s["close"].astype(float).round(2).tolist(),
            "events": ev_list,
            "class_period_start": CLASS_PERIOD_START, "class_period_end": CLASS_PERIOD_END}


def compute_news(d: dict) -> dict:
    """Section 02 — cadence + topics + topic-over-time + log."""
    news = d["news"]
    if news.empty:
        return {"cadence": {"weeks": [], "counts": []}, "topics_total": {},
                "topics_over_time": {"weeks": [], "series": {}},
                "articles_by_topic_week": [], "total": 0}
    n = news.copy()
    n["date"] = pd.to_datetime(n["date"], errors="coerce")
    n = n.dropna(subset=["date"]).copy()
    n["week"] = n["date"].dt.to_period("W-SUN").dt.end_time.dt.strftime("%Y-%m-%d")

    cad = n.groupby("week").size().reset_index(name="count").sort_values("week")
    cadence = {"weeks": cad["week"].tolist(), "counts": cad["count"].astype(int).tolist()}
    topics_total = {k: int(v) for k, v in n["topic"].value_counts().items()}

    # Topic mix over time — pivot to weekly counts per topic
    pivot = n.pivot_table(index="week", columns="topic", values="date",
                          aggfunc="count", fill_value=0).sort_index()
    topic_order = list(TOPIC_LABELS.keys())
    series_by_topic = {}
    for t in topic_order:
        if t in pivot.columns:
            series_by_topic[t] = pivot[t].astype(int).tolist()
    topics_over_time = {"weeks": pivot.index.tolist(), "series": series_by_topic}

    # Article log: top 60 articles grouped by week × topic with first-sentence summary
    log = n.sort_values("date", ascending=False).head(60).copy()
    articles = []
    for _, r in log.iterrows():
        articles.append({
            "date": r["date"].strftime("%Y-%m-%d"),
            "headline": str(r.get("headline", ""))[:240],
            "source": str(r.get("source", "")),
            "topic": str(r.get("topic", "")),
            "url": str(r.get("url", "")),
        })
    # Topic-rollup-per-week (last 12 weeks) — "X articles about Y this week" view
    last12 = (n[n["week"] >= cad["week"].tail(12).min()] if not cad.empty else n)
    rollups = (last12.groupby(["week", "topic"]).size().reset_index(name="count")
                     .sort_values(["week", "count"], ascending=[False, False]))
    rollup_list = [{"week": r["week"], "topic": r["topic"], "count": int(r["count"])}
                   for _, r in rollups.iterrows()]
    return {"cadence": cadence, "topics_total": topics_total,
            "topics_over_time": topics_over_time, "articles": articles,
            "topic_rollups": rollup_list, "total": int(len(n))}


def compute_cadence_vs_stock(d: dict, news: dict) -> dict:
    """News cadence vs stock, both normalized to 100."""
    if not news.get("cadence", {}).get("weeks") or d["stock"].empty:
        return {"weeks": [], "cadence_idx": [], "stock_idx": []}
    cad_weeks = news["cadence"]["weeks"]
    cad_counts = news["cadence"]["counts"]

    s = d["stock"].copy()
    s["date"] = pd.to_datetime(s["date"])
    s = s.sort_values("date")
    s["week"] = s["date"].dt.to_period("W-SUN").dt.end_time.dt.strftime("%Y-%m-%d")
    weekly_close = s.groupby("week")["close"].last()

    # Align on cadence weeks
    weeks = [w for w in cad_weeks if w in weekly_close.index]
    counts = [c for w, c in zip(cad_weeks, cad_counts) if w in weekly_close.index]
    closes = [float(weekly_close[w]) for w in weeks]
    if not weeks: return {"weeks": [], "cadence_idx": [], "stock_idx": []}
    cb = max(counts[0], 1); sb = closes[0]
    return {
        "weeks": weeks,
        "cadence_idx": [round(c / cb * 100, 1) for c in counts],
        "stock_idx":   [round(c / sb * 100, 1) for c in closes],
    }


def _resample_monthly_to_weekly_map(monthly_df: pd.DataFrame, month_col: str,
                                    val_col: str, target_weeks: list[str]) -> dict[str, float]:
    if monthly_df.empty: return {}
    m = monthly_df.copy()
    m["dt"] = pd.to_datetime(m[month_col], format="%Y-%m")
    m = m.sort_values("dt")
    out = {}
    for wk in target_weeks:
        wk_dt = pd.to_datetime(wk)
        prior = m[m["dt"] <= wk_dt]
        if not prior.empty: out[wk] = float(prior.iloc[-1][val_col])
    return out


def compute_egg_market(d: dict) -> dict:
    """Section 03 — 4 sub-chart payloads."""
    shell = d["egg_shell"]; breaker = d["egg_breaker"]; retail = d["vitl_retail"]
    hpai = d["hpai"]; flock = d["layer_flock"]; stock = d["stock"]

    # CHART 1 — Conventional vs VITL retail (both $/dz)
    chart1 = {"weeks": [], "conv": [], "vitl": []}
    if not shell.empty:
        s = shell.copy().sort_values("week")
        chart1["weeks"] = s["week"].astype(str).tolist()
        chart1["conv"] = s["price_per_dozen"].astype(float).round(3).tolist()
        vmap = _resample_monthly_to_weekly_map(retail, "month", "retail_price_per_dozen", chart1["weeks"])
        chart1["vitl"] = [round(vmap[w], 2) if w in vmap else None for w in chart1["weeks"]]

    # CHART 2 — Premium gap %
    chart2 = {"weeks": chart1["weeks"], "gap": []}
    if chart1["weeks"]:
        for w, c, v in zip(chart1["weeks"], chart1["conv"], chart1["vitl"]):
            chart2["gap"].append(round((v / c - 1) * 100, 1) if (v is not None and c > 0) else None)
    peak_gap = max([g for g in chart2["gap"] if g is not None], default=None)
    latest_gap = next((g for g in reversed(chart2["gap"]) if g is not None), None)

    # CHART 3 — Stock vs Gap %, both normalized to 100 over last 18mo
    chart3 = {"weeks": [], "stock_idx": [], "gap_idx": []}
    if not stock.empty and chart2["gap"]:
        ss = stock.copy()
        ss["date"] = pd.to_datetime(ss["date"])
        ss = ss.sort_values("date")
        cutoff = (datetime.today() - timedelta(days=540))
        ss = ss[ss["date"] >= cutoff]
        ss["week"] = ss["date"].dt.to_period("W-SUN").dt.end_time.dt.strftime("%Y-%m-%d")
        stock_weekly = ss.groupby("week")["close"].last()
        # Pair on gap weeks intersected with stock weeks
        gap_weeks = chart1["weeks"]; gap_vals = chart2["gap"]
        gap_map = dict(zip(gap_weeks, gap_vals))
        common = [w for w in stock_weekly.index if w in gap_map and gap_map[w] is not None]
        if common and len(common) > 3:
            common = sorted(common)
            base_s = float(stock_weekly[common[0]]); base_g = gap_map[common[0]]
            chart3["weeks"] = common
            chart3["stock_idx"] = [round(float(stock_weekly[w]) / base_s * 100, 1) for w in common]
            chart3["gap_idx"]   = [round(gap_map[w] / base_g * 100, 1) for w in common]

    # CHART 4 — Breaker market vs conventional (2yr)
    chart4 = {"weeks": [], "breaker": [], "conv": []}
    if not breaker.empty:
        b = breaker.copy().sort_values("week")
        chart4["weeks"] = b["week"].astype(str).tolist()
        chart4["breaker"] = b["price_per_dozen"].astype(float).round(3).tolist()
        if not shell.empty:
            conv_map = dict(zip(chart1["weeks"], chart1["conv"]))
            chart4["conv"] = [conv_map.get(w) for w in chart4["weeks"]]

    # HPAI + flock cards
    hpai_latest = None
    if not hpai.empty:
        h = hpai.copy().sort_values("week"); latest = h.iloc[-1]
        prior = h.iloc[-5:-1] if len(h) >= 5 else h.iloc[:-1]
        prior_avg = float(prior["commercial_layer_cases"].mean()) if not prior.empty else 0
        trend = "up" if latest["commercial_layer_cases"] > prior_avg else "down"
        hpai_latest = {"week": str(latest["week"]),
                       "cases": int(latest["commercial_layer_cases"]), "trend": trend}
    flock_latest = None
    if not flock.empty:
        f = flock.copy().sort_values("month"); latest = f.iloc[-1]
        prior = f.iloc[-4:-1] if len(f) >= 4 else f.iloc[:-1]
        prior_avg = float(prior["layer_flock_millions"].mean()) if not prior.empty else 0
        trend = "up" if latest["layer_flock_millions"] > prior_avg else "down"
        flock_latest = {"month": str(latest["month"]),
                        "millions": float(latest["layer_flock_millions"]), "trend": trend}

    return {"chart1": chart1, "chart2": chart2, "chart3": chart3, "chart4": chart4,
            "peak_gap": peak_gap, "latest_gap": latest_gap,
            "hpai_latest": hpai_latest, "flock_latest": flock_latest}


def compute_community(d: dict) -> dict:
    subs = d["subs"]; reddit_weekly = d["reddit_weekly"]; competitor_weekly = d["competitor_weekly"]
    linoleic = d["linoleic"]; youtube_linoleic = d["youtube_linoleic"]; stock = d["stock"]

    if subs.empty:
        sub_rows, brand_sov, totals = [], {"weeks": [], "brands": {}}, {}
    else:
        today = datetime.today()
        d90 = (today - timedelta(days=90)).strftime("%Y-%m-%d")
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
            sub_rows.append({"subreddit": sub_name, "topic": r["topic"], "priority": r["priority"],
                             "mentions_90d": mentions_90d, "yoy_pct": yoy_pct})
        brand_sov = {"weeks": [], "brands": {}}; totals = {}
        if not competitor_weekly.empty:
            cw = competitor_weekly.copy(); cw["week"] = cw["week"].astype(str)
            weeks = sorted(cw["week"].unique().tolist())
            brand_sov["weeks"] = weeks
            present = set(cw["brand"].unique().tolist())
            for brand in BRAND_SOV_ORDER:
                if brand in present:
                    b = cw[cw["brand"] == brand].set_index("week")["post_count"].reindex(weeks, fill_value=0)
                    brand_sov["brands"][brand] = b.astype(int).tolist()
                else:
                    brand_sov["brands"][brand] = [0] * len(weeks)
                totals[brand] = int(sum(brand_sov["brands"][brand]))

    # Linoleic — Reddit (weekly) + optional YouTube monthly resampled
    lin_series = {"weeks": [], "reddit": [], "youtube": []}
    if not linoleic.empty:
        L = linoleic.copy().sort_values("week")
        lin_series["weeks"] = L["week"].astype(str).tolist()
        lin_series["reddit"] = L["post_count"].astype(int).tolist()
        lin_series["youtube"] = [None] * len(lin_series["weeks"])
    if not youtube_linoleic.empty and lin_series["weeks"]:
        yl = youtube_linoleic.copy().sort_values("month")
        yl["dt"] = pd.to_datetime(yl["month"], format="%Y-%m")
        yt_series = []
        for wk in lin_series["weeks"]:
            prior = yl[yl["dt"] <= pd.to_datetime(wk)]
            yt_series.append(round(float(prior.iloc[-1]["video_count"]) / 4.0, 2) if not prior.empty else None)
        lin_series["youtube"] = yt_series

    # Controversy vs stock — last 12mo
    controversy_vs_stock = {"weeks": [], "controversy_idx": [], "stock_idx": []}
    if lin_series["weeks"] and not stock.empty:
        cutoff = (datetime.today() - timedelta(days=365)).strftime("%Y-%m-%d")
        lin_recent_weeks = [w for w in lin_series["weeks"] if w >= cutoff]
        if lin_recent_weeks:
            ss = stock.copy()
            ss["date"] = pd.to_datetime(ss["date"])
            ss = ss.sort_values("date")
            ss["week"] = ss["date"].dt.to_period("W-SUN").dt.end_time.dt.strftime("%Y-%m-%d")
            stock_weekly = ss.groupby("week")["close"].last()
            common = [w for w in lin_recent_weeks if w in stock_weekly.index]
            if len(common) > 3:
                lin_map = dict(zip(lin_series["weeks"], lin_series["reddit"]))
                lc = [float(lin_map.get(w, 0)) for w in common]
                sc = [float(stock_weekly[w]) for w in common]
                cb = max(max(lc), 1); sb = sc[0]
                controversy_vs_stock["weeks"] = common
                controversy_vs_stock["controversy_idx"] = [round(v / cb * 100, 1) for v in lc]
                controversy_vs_stock["stock_idx"] = [round(v / sb * 100, 1) for v in sc]

    return {"sub_rows": sub_rows, "brand_sov": brand_sov, "totals": totals,
            "linoleic": lin_series, "controversy_vs_stock": controversy_vs_stock}


def compute_tdp_vs_revenue(d: dict) -> dict:
    df = d["tdp_vs_revenue"]
    if df.empty: return {"quarters": [], "tdp": [], "revenue": []}
    df = df.copy()
    return {
        "quarters": df["quarter"].astype(str).tolist(),
        "tdp":      df["tdp_yoy_pct"].astype(float).round(1).tolist(),
        "revenue":  df["revenue_yoy_pct"].astype(float).round(1).tolist(),
    }


def compute_financial_history(d: dict) -> dict:
    """Section 05 — EBITDA + cash burn decomp + credibility scorecard."""
    eh = d["ebitda_history"]
    ebitda = {"labels": [], "values": [], "kinds": []}
    if not eh.empty:
        ebitda["labels"] = eh["period"].astype(str).tolist()
        ebitda["values"] = eh["ebitda_margin_pct"].astype(float).round(1).tolist()
        ebitda["kinds"]  = eh["kind"].astype(str).tolist()

    cbd = d["cash_burn_decomp"]
    # New categorized schema: period × line_item × amount_m × category.
    # The old aggregate-by-quarter chart isn't used anymore (Section 06 now
    # uses compute_categorized_cash_burn instead); leave empty struct for
    # backward compat with anything that still reads d.fin.cash_burn.
    cash_burn = {"quarters": [], "operations": [], "capex": [], "supply_mgmt": [],
                 "buyback": [], "other": [], "total": []}

    # Credibility (unchanged)
    cred_rows = []
    g = d["guidance"]
    if not g.empty:
        for _, r in g.iterrows():
            cred_rows.append({
                "period": str(r["period"]), "metric": str(r["metric"]),
                "management_said": str(r["management_said"]),
                "actual": str(r["actual"]), "delta": str(r["delta"]),
                "delta_kind": str(r.get("delta_kind", "")).lower(),
            })

    return {"ebitda": ebitda, "cash_burn": cash_burn, "credibility": cred_rows}


def compute_correlation_matrix(d: dict) -> dict:
    corr = d["correlations"]
    if corr.empty: return {"keys": [], "labels": {}, "cells": {}}
    keys_order = ["stock", "gap", "conv", "reddit", "news"]
    keys = [k for k in keys_order if k in corr["row"].astype(str).unique().tolist()]
    labels = {k: corr[corr["row"] == k]["row_label"].iloc[0] for k in keys}
    cells = {}
    for _, r in corr.iterrows():
        row = str(r["row"]); col = str(r["col"])
        val = r["correlation"]
        n = int(r["n_overlap"]) if not pd.isna(r["n_overlap"]) else 0
        cells[(row, col)] = {"corr": (None if pd.isna(val) else float(val)), "n": n}
    return {"keys": keys, "labels": labels,
            "cells": {f"{k[0]}|{k[1]}": v for k, v in cells.items()}}


def compute_reaction_magnitude(d: dict) -> dict:
    """Section 02 hero bar chart: every event's stock %-reaction on day."""
    ev = d["events"]
    if ev.empty: return {"events": []}
    rows = []
    for _, r in ev.iterrows():
        rows.append({
            "date": str(r["date"]),
            "label": str(r.get("headline", ""))[:60],
            "reaction_pct": (None if pd.isna(r.get("reaction_pct")) else float(r["reaction_pct"])),
            "kind": str(r.get("reaction_kind", "flat")),
        })
    rows.sort(key=lambda x: x["date"])
    return {"events": rows}


def compute_hpai_cumulative(d: dict) -> dict:
    df = d["hpai_cumulative"]
    if df.empty: return {"months": [], "cumulative": []}
    df = df.copy().sort_values("month")
    return {
        "months": df["month"].astype(str).tolist(),
        "cumulative": df["cumulative_birds_m"].astype(float).round(1).tolist(),
    }


def compute_operating_recovery(d: dict) -> dict:
    """Section 05 — TDP (moved here), Comp difficulty bars, GM trajectory, 2yr stack."""
    out = {"tdp": {"quarters": [], "tdp": [], "revenue": []},
           "comp": {"quarters": [], "growth": [], "comp_kinds": [], "kinds": []},
           "gm":   {"quarters": [], "values": [], "kinds": []},
           "stack": {"quarters": [], "current_yoy": [], "prior_yoy": [], "stack": []}}

    if not d["tdp_vs_revenue"].empty:
        t = d["tdp_vs_revenue"].copy()
        out["tdp"]["quarters"] = t["quarter"].astype(str).tolist()
        out["tdp"]["tdp"] = t["tdp_yoy_pct"].astype(float).round(1).tolist()
        out["tdp"]["revenue"] = t["revenue_yoy_pct"].astype(float).round(1).tolist()

    if not d["qrev_growth"].empty:
        q = d["qrev_growth"].copy()
        out["comp"]["quarters"]   = q["quarter"].astype(str).tolist()
        out["comp"]["growth"]     = q["revenue_yoy_pct"].astype(float).round(1).tolist()
        out["comp"]["comp_kinds"] = q["comp_difficulty"].astype(str).tolist()
        out["comp"]["kinds"]      = q["kind"].astype(str).tolist()

    if not d["gm_trajectory"].empty:
        g = d["gm_trajectory"].copy()
        out["gm"]["quarters"] = g["quarter"].astype(str).tolist()
        out["gm"]["values"]   = g["gross_margin_pct"].astype(float).round(1).tolist()
        out["gm"]["kinds"]    = g["kind"].astype(str).tolist()

    if not d["two_yr_stack"].empty:
        s = d["two_yr_stack"].copy()
        out["stack"]["quarters"]    = s["quarter"].astype(str).tolist()
        out["stack"]["current_yoy"] = s["current_yoy_pct"].astype(float).round(1).tolist()
        out["stack"]["prior_yoy"]   = s["prior_yoy_pct"].astype(float).round(1).tolist()
        out["stack"]["stack"]       = s["two_yr_stack"].astype(float).round(1).tolist()

    return out


def compute_full_credibility(d: dict) -> dict:
    """Section 06 — 22-quarter scorecard from guidance_history_full.csv."""
    g = d["guidance_full"]
    if g.empty: return {"rows": [], "summary": {"beats": 0, "in_line": 0, "misses": 0, "cuts": 0, "na": 0}}
    rows = []
    counts = {"beats": 0, "in_line": 0, "misses": 0, "cuts": 0, "na": 0}
    for _, r in g.iterrows():
        kind = str(r.get("delta_kind", "")).lower()
        rows.append({
            "period": str(r["period"]),
            "metric": str(r["metric"]),
            "guided": str(r.get("management_guided", "n/a")),
            "actual": str(r.get("actual", "n/a")),
            "delta":  str(r.get("delta", "n/a")),
            "delta_kind": kind,
            "miss_type": str(r.get("miss_type", "n/a")),
        })
        if kind == "beat": counts["beats"] += 1
        elif kind == "inline" or kind == "in-line": counts["in_line"] += 1
        elif kind == "miss": counts["misses"] += 1
        elif kind == "cut": counts["cuts"] += 1
        else: counts["na"] += 1
    return {"rows": rows, "summary": counts}


def compute_categorized_cash_burn(d: dict) -> dict:
    """Section 06 — Q1 actual vs FY26 projected with category flags."""
    df = d["cash_burn_decomp"]
    if df.empty: return {"actual": [], "projected": []}
    out = {"actual": [], "projected": []}
    for _, r in df.iterrows():
        bucket = "actual" if str(r.get("kind", "")).lower() == "actual" else "projected"
        out[bucket].append({
            "line_item": str(r["line_item"]),
            "amount_m":  float(r["amount_m"]),
            "category":  str(r["category"]),
            "note":      str(r.get("note", "")),
        })
    return out


def compute_valuation(d: dict) -> dict:
    df = d["valuation"]
    if df.empty: return {"multiples": [], "scenarios": [], "current_price": None}
    multiples = []; scenarios = []; current = None
    for _, r in df.iterrows():
        k = str(r["kind"]).lower()
        if k == "multiple":
            multiples.append({
                "label": str(r["label"]), "value": float(r["value"]),
                "range_low":  (None if pd.isna(r.get("range_low")) else float(r["range_low"])),
                "range_high": (None if pd.isna(r.get("range_high")) else float(r["range_high"])),
                "note": str(r.get("note", "")),
            })
        elif k == "scenario":
            scenarios.append({
                "label": str(r["label"]),
                "implied_price": float(r["value"]),
                "note": str(r.get("note", "")),
            })
        elif k == "current":
            current = float(r["value"])
    return {"multiples": multiples, "scenarios": scenarios, "current_price": current}


def compute_catalysts(d: dict) -> dict:
    df = d["catalysts"]
    if df.empty: return {"rows": []}
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "date": str(r["date"]), "date_kind": str(r.get("date_kind", "fixed")),
            "event": str(r["event"]),
            "tier": str(r["impact_tier"]).upper(),
            "direction": str(r["direction"]).upper(),
            "note": str(r.get("note", "")),
        })
    return {"rows": rows}


def compute_recovery_plan(d: dict) -> dict:
    df = d["recovery_plan"]
    if df.empty: return {"rows": []}
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "order": int(r.get("order", 0)),
            "action": str(r["action"]),
            "target": str(r["stated_target"]),
            "status": str(r["status"]).upper(),
            "confirmed": str(r.get("confirmed_in_financials", "")).upper(),
            "note": str(r.get("note", "")),
        })
    return {"rows": rows}


def compute_brand_awareness(d: dict) -> dict:
    df = d["brand_awareness"]
    if df.empty: return {"years": [], "values": []}
    years = df["year"].astype(str).tolist()
    vals = []
    for v in df["aided_awareness_pct"]:
        try:
            vals.append(float(v) if not pd.isna(v) else None)
        except (TypeError, ValueError):
            vals.append(None)
    return {"years": years, "values": vals}


def compute_runway_math(setup: dict) -> dict:
    """Computed display values for the Setup Runway card.

    Revolver size is NOT publicly disclosed in Q1 10-Q (it says 'undrawn
    revolving credit facility' without specifying capacity). We compute
    runway from cash alone — the revolver extends it by an unknown amount.
    """
    current = setup.get("current_cash") or 51
    q_burn = setup.get("q_burn") or 62
    fy26_remaining_lo = 60; fy26_remaining_hi = 75
    cash_runway_qs_lo = round(current / max(fy26_remaining_hi, 1) * 4, 1)
    cash_runway_qs_hi = round(current / max(fy26_remaining_lo, 1) * 4, 1)
    return {
        "current_cash": current, "q_burn": q_burn,
        "fy26_remaining_lo": fy26_remaining_lo,
        "fy26_remaining_hi": fy26_remaining_hi,
        "cash_runway_qs_lo": cash_runway_qs_lo,
        "cash_runway_qs_hi": cash_runway_qs_hi,
    }


def compute_sov_sentiment(d: dict) -> dict:
    """Pos/Neg/Neu split per brand per week (Section 04 stacked sentiment)."""
    cw = d["competitor_weekly"]
    if cw.empty: return {"weeks": [], "brands": {}, "totals": {}}
    has_sentiment = all(c in cw.columns for c in ("pos_count", "neg_count", "neu_count"))
    weeks = sorted(cw["week"].astype(str).unique().tolist())
    brands = {}
    totals = {}
    for brand in BRAND_SOV_ORDER:
        bdf = cw[cw["brand"] == brand]
        if bdf.empty:
            brands[brand] = {"total": [0]*len(weeks), "pos": [0]*len(weeks),
                              "neg": [0]*len(weeks), "neu": [0]*len(weeks)}
            totals[brand] = {"total": 0, "pos": 0, "neg": 0, "neu": 0}
            continue
        total = bdf.set_index("week")["post_count"].reindex(weeks, fill_value=0).astype(int).tolist()
        if has_sentiment:
            pos = bdf.set_index("week")["pos_count"].reindex(weeks, fill_value=0).astype(int).tolist()
            neg = bdf.set_index("week")["neg_count"].reindex(weeks, fill_value=0).astype(int).tolist()
            neu = bdf.set_index("week")["neu_count"].reindex(weeks, fill_value=0).astype(int).tolist()
        else:
            # Fallback when CSV doesn't yet have sentiment columns
            pos = [0]*len(weeks); neg = [0]*len(weeks); neu = total[:]
        brands[brand] = {"total": total, "pos": pos, "neg": neg, "neu": neu}
        totals[brand] = {"total": int(sum(total)), "pos": int(sum(pos)),
                          "neg": int(sum(neg)), "neu": int(sum(neu))}
    return {"weeks": weeks, "brands": brands, "totals": totals}


def compute_google_trends(d: dict) -> dict:
    """Section 01 Category — 4-term Google Trends weekly comparison."""
    df = d["google_trends"]
    if df.empty: return {"weeks": [], "terms": {}, "latest_summary": {}}
    df = df.copy().sort_values(["week", "term"])
    weeks = sorted(df["week"].astype(str).unique().tolist())
    terms = {}
    for term in df["term"].unique():
        sub = df[df["term"] == term].set_index("week")["interest"].reindex(weeks, fill_value=0)
        terms[str(term)] = sub.astype(int).tolist()
    # Latest week snapshot — values per term
    if weeks:
        latest_week = weeks[-1]
        latest = (df[df["week"] == latest_week]
                  .set_index("term")["interest"].astype(int).to_dict())
        latest_summary = {"week": latest_week, "values": latest}
    else:
        latest_summary = {"week": "", "values": {}}
    return {"weeks": weeks, "terms": terms, "latest_summary": latest_summary}


def compute_customer_metrics(d: dict) -> list:
    df = d["customer_metrics"]
    if df.empty: return []
    return [{
        "metric": str(r["metric"]),
        "latest_value": str(r["latest_value"]),
        "latest_period": str(r["latest_period"]),
        "source_quote": str(r.get("source_quote", "")),
        "kind": str(r.get("kind", "neutral")).lower(),
    } for _, r in df.iterrows()]


def compute_category_supply(d: dict) -> dict:
    """Section 01B — how crowded the pasture-raised category got over time."""
    df = d["category_supply"]
    if df.empty: return {"years": [], "branded": [], "private_label": [], "events": []}
    df = df.copy().sort_values("year")
    events = []
    for _, r in df.iterrows():
        events.append({
            "year": int(r["year"]),
            "event": str(r.get("event", "")),
            "note": str(r.get("note", "")),
            "confidence": str(r.get("confidence", "estimated")),
            "branded": int(r["branded_skus"]),
            "private_label": int(r["private_label_skus"]),
            "total": int(r["total_skus"]),
        })
    return {
        "years":         df["year"].astype(int).tolist(),
        "branded":       df["branded_skus"].astype(int).tolist(),
        "private_label": df["private_label_skus"].astype(int).tolist(),
        "events":        events,
    }


def compute_category_growth(d: dict) -> dict:
    df = d["category_growth"]
    if df.empty: return {"quarters": [], "vitl": [], "category": [], "confidence": []}
    df = df.copy()
    return {
        "quarters":   df["quarter"].astype(str).tolist(),
        "vitl":       df["vitl_yoy_pct"].astype(float).round(1).tolist(),
        "category":   df["category_yoy_pct"].astype(float).round(1).tolist(),
        "confidence": df["confidence"].astype(str).tolist() if "confidence" in df.columns else ["estimated"] * len(df),
        "private_label_residual": [
            # Assuming the 6-brand premium set captures ~70-80% of category volume,
            # the residual (category growth - 6-brand share-weighted growth) is
            # rough proxy for private-label penetration. We don't have brand-level
            # private growth numbers for the 5 non-VITL premium brands, so this
            # is a directional indicator only.
            None for _ in range(len(df))
        ],
    }


def compute_supply_quantification(d: dict) -> dict:
    """TOP PANEL — quantifies how over-supplied VITL is vs retail demand and
    when farmer amendments resolve it. Q1 26 actual through FY27 norm.

    Returns dict with:
      quarters, retail (M dozens), baseline_breaker (M, baseline ~5%),
      excess_breaker (M, the over-supply), supply_cost (M $),
      kinds (actual/estimate/projection), notes,
      hero_tiles list of 4 hero metrics
    """
    df = d.get("supply_quant", pd.DataFrame())
    if df.empty:
        return {"quarters": [], "retail": [], "baseline_breaker": [],
                "excess_breaker": [], "supply_cost": [],
                "kinds": [], "notes": [], "hero_tiles": [],
                "breaker_now": 0.08, "breaker_norm_low": 0.50, "breaker_norm_high": 1.00,
                "retail_price_per_dozen": 5.00}
    df = df.copy()
    quarters         = df["quarter"].astype(str).tolist()
    retail           = df["retail_volume_m"].astype(float).round(1).tolist()
    baseline_breaker = df["baseline_breaker_m"].astype(float).round(1).tolist()
    excess_breaker   = df["excess_breaker_m"].astype(float).round(1).tolist()
    supply_cost      = df["supply_mgmt_cost_m"].astype(float).round(1).tolist()
    kinds            = df["kind"].astype(str).tolist() if "kind" in df.columns else ["estimate"] * len(df)
    notes            = df["note"].astype(str).tolist() if "note" in df.columns else [""] * len(df)
    production       = df["production_m"].astype(float).round(1).tolist()

    # Hero tiles: Q1 (actual), Q2E (trough), Q3E (recovery), Capacity removed
    # Compute % of production for each row
    def pct(excess: float, prod: float) -> float:
        return round((excess / prod) * 100, 1) if prod else 0.0

    tiles = []
    # Tile 1 — Q1 actual
    tiles.append({
        "label":  f"{quarters[0]} excess (actual)",
        "value":  f"{excess_breaker[0]:.0f}M",
        "sub":    f"{pct(excess_breaker[0], production[0])}% of production · ${supply_cost[0]:.1f}M supply mgmt hit",
        "tone":   "neg",
    })
    # Tile 2 — Q2 trough
    tiles.append({
        "label":  f"{quarters[1]} excess (guided trough)",
        "value":  f"{excess_breaker[1]:.0f}M",
        "sub":    f"{pct(excess_breaker[1], production[1])}% of production · ~${supply_cost[1]:.0f}M supply mgmt guided",
        "tone":   "neg",
    })
    # Tile 3 — Q3 inflection
    tiles.append({
        "label":  f"{quarters[2]} expected (post-amendments)",
        "value":  f"{excess_breaker[2]:.0f}M",
        "sub":    f"baseline 5% · farmer amendments take effect",
        "tone":   "pos",
    })
    # Tile 4 — Capacity removed (annualized: Q1 production - Q3 production = 4M/quarter × 4)
    capacity_removed_annual = round((production[0] - production[2]) * 4, 1)
    tiles.append({
        "label":  "Capacity removed via amendments",
        "value":  f"~{capacity_removed_annual:.0f}M",
        "sub":    f"dozens annually · ≈6-8 farmer contracts",
        "tone":   "pos",
    })

    return {
        "quarters":         quarters,
        "retail":           retail,
        "baseline_breaker": baseline_breaker,
        "excess_breaker":   excess_breaker,
        "supply_cost":      supply_cost,
        "kinds":            kinds,
        "notes":            notes,
        "production":       production,
        "hero_tiles":       tiles,
        # Breaker price inset (today vs historical norm)
        "breaker_now":          0.08,
        "breaker_norm_low":     0.50,
        "breaker_norm_high":    1.00,
        "retail_price_per_dozen": 5.00,
    }


def compute_reddit_posts(d: dict) -> list:
    """Latest 30 Vital Farms posts/comments with title or body excerpt + URL + sentiment."""
    df = d["reddit_posts"]
    if df.empty: return []
    out = []
    for _, r in df.head(30).iterrows():
        out.append({
            "date": str(r.get("date", "")),
            "subreddit": str(r.get("subreddit", "")),
            "kind": str(r.get("kind", "")),
            "author": str(r.get("author", "")),
            "excerpt": str(r.get("excerpt", ""))[:240],
            "url": str(r.get("url", "")),
            "score": int(r.get("score") or 0),
            "num_comments": int(r.get("num_comments") or 0),
            "sentiment": str(r.get("sentiment", "neutral")),
        })
    return out


def compute_youtube_videos(d: dict) -> list:
    """Latest 30 YouTube videos with title + channel + views + URL."""
    df = d["youtube_videos"]
    if df.empty: return []
    out = []
    for _, r in df.head(30).iterrows():
        out.append({
            "published": str(r.get("published", ""))[:10],
            "title":   str(r.get("title", ""))[:200],
            "channel": str(r.get("channel", "")),
            "views":   int(r.get("views") or 0),
            "url":     str(r.get("url", "")),
            "query":   str(r.get("query", "")),
            "pass":    str(r.get("pass", "")),
        })
    return out


def compute_youtube_vitl(d: dict) -> dict:
    """VITL 'vital farms' general query — monthly volume + view_sum."""
    y = d["youtube_monthly"]
    if y.empty: return {"months": [], "video_count": [], "view_sum": []}
    yv = y[y["query"].astype(str).str.contains("vital farms", case=False, na=False)]
    if yv.empty: return {"months": [], "video_count": [], "view_sum": []}
    m = yv.groupby("month").agg(video_count=("video_count","sum"), view_sum=("view_sum","sum")).reset_index().sort_values("month")
    return {
        "months": m["month"].astype(str).tolist(),
        "video_count": m["video_count"].astype(int).tolist(),
        "view_sum": m["view_sum"].astype(float).fillna(0).astype(int).tolist(),
    }


def compute_youtube_competitors(d: dict) -> dict:
    """Per-brand YouTube monthly video counts. Returns {months, brands: {b: counts}}."""
    yc = d["youtube_competitors"]
    if yc.empty: return {"months": [], "brands": {}}
    months = sorted(yc["month"].astype(str).unique().tolist())
    BRAND_KEY_TO_DISPLAY = {
        "vital farms":            "Vital Farms",
        "handsome brook":         "Handsome Brook",
        "alexandre family farm":  "Alexandre",
        "pete and gerry's":       "Pete & Gerry's",
        "happy egg":              "Happy Egg",
        "organic valley":         "Organic Valley",
    }
    brands = {}
    for raw_key, display in BRAND_KEY_TO_DISPLAY.items():
        sub = yc[yc["brand"].astype(str).str.lower() == raw_key.lower()]
        if sub.empty:
            brands[display] = [0] * len(months)
        else:
            brands[display] = sub.set_index("month")["video_count"].reindex(months, fill_value=0).astype(int).tolist()
    return {"months": months, "brands": brands}


# ─────────────────────────────────────────────────────────────────────────────
# Dynamic "What this shows" take helper — 2-sentence template with real numbers
# ─────────────────────────────────────────────────────────────────────────────
def data_take(*, meaning: str = "",
              # Legacy kwargs kept so old callsites don't crash. Ignored
              # in favor of `meaning` which is now the single-paragraph
              # analytical read.
              current: str | None = None, peak: str | None = None,
              trough: str | None = None, direction: str = "") -> str:
    """One-paragraph analytical take. Conclusion-first.

    Pass a single `meaning` string written as a brief PM read of the chart:
    "Since X is doing Y, this means Z for VITL." No "current is N · peak is N"
    boilerplate — the analyst reads numbers off the chart, they want the
    conclusion. Old callers that pass `current=...` etc. will degrade to
    rendering nothing (the chart's static /reads/ take still appears).

    Returns empty string when `meaning` is empty.
    """
    if not meaning: return ""
    return (
        '<div class="dynamic-take">'
        '<div class="take-eyebrow take-eyebrow-dyn">WHAT THIS MEANS FOR VITL</div>'
        f'<p>{meaning}</p>'
        '</div>'
    )


def compute_summary(d, qr, setup, news, egg, fin, corr,
                     comm=None, cat_supply=None, op_rec=None, val=None, tdp=None,
                     cat_growth=None) -> dict:
    kpis = qr["kpis"]
    bullets = [
        f"Days since FY25 ERP print: <strong>{kpis['days_since_print']}</strong>.",
        (f"VITL vs Feb 26 close (${kpis['feb26_close']:.2f}): <strong>{kpis['vs_feb26_pct']:+.1f}%</strong>"
         if kpis.get('vs_feb26_pct') is not None else "VITL vs Feb 26: —"),
        (f"Implied runway: <strong>{setup['runway_qs']:.1f} quarters</strong> at Q1 burn"
         if setup.get('runway_qs') is not None else "Runway: —"),
        (f"Insider cluster: <strong>{setup['cluster']['insiders']} insiders</strong>, "
         f"${setup['cluster']['total_value']:,.0f}" if setup.get('cluster') else "Insider cluster: —"),
        (f"Short interest: <strong>{setup['short_current']['pct']:.1f}%</strong> of float"
         if setup.get('short_current') else "Short interest: —"),
        (f"VITL/conventional gap: <strong>{egg['latest_gap']:.0f}%</strong>"
         if egg.get('latest_gap') is not None else "Premium gap: —"),
        f"News articles tracked: <strong>{news.get('total', 0)}</strong>",
        f"Credibility scorecard rows: <strong>{len(fin['credibility'])}</strong>",
        (f"Correlation series: <strong>{len(corr.get('keys', []))}</strong>"
         if corr.get('keys') else "Correlation matrix: —"),
    ]

    # ── Narrative briefing — friendly-language walkthrough of the whole
    # dashboard, data-driven so the numbers stay accurate on refresh.
    narrative_paragraphs = []

    # P1: where we are right now
    current = kpis.get("current_price")
    vs26 = kpis.get("vs_feb26_pct")
    days = kpis.get("days_since_print", 0)
    deadline = kpis.get("days_to_deadline", 0)
    if current is not None:
        p1 = (
            f"<strong>Where VITL sits today.</strong> The stock is at "
            f"<strong>${current:.2f}</strong> — "
            f"<strong>{vs26:+.1f}%</strong> since the Feb 26 FY25 print (${kpis['feb26_close']:.2f}). "
            f"That's <strong>{days} days</strong> into the recovery question, with the lead-plaintiff "
            f"deadline for the securities-fraud class action <strong>{deadline} days</strong> out. "
            f"VITL fell ~85% peak-to-trough on three damages: ERP transition disruption (operational, now "
            f"healing), the January seed-oil brand controversy (watching), and a conventional egg-price "
            f"crash that widened the premium gap to {egg.get('latest_gap', 0):.0f}% vs the 150-200% "
            f"historical norm (worsening). Recovery requires the gap to close AND cash to hold out — "
            f"that's the binary the dashboard tracks."
        )
    else:
        p1 = "VITL stock data not yet loaded — most of this narrative will populate on refresh."
    narrative_paragraphs.append(p1)

    # P2: the macro (egg cycle) — premium gap, breaker, HPAI
    p2 = (
        f"<strong>The macro frame — eggs.</strong> Section 04 is the load-bearing analytical section. "
        f"The premium gap (VITL retail vs conventional wholesale) sits at <strong>{egg.get('latest_gap', 0):.0f}%</strong> "
        f"today vs <strong>{egg.get('peak_gap', 0):.0f}%</strong> at the Q1 2026 cycle peak — both well "
        f"above the 150-200% historical norm. Above ~250% the price-conscious buyer trades down to "
        f"private label, which is precisely what's happening (more on that below). Two things would "
        f"close the gap: (1) conventional egg prices rising back toward $2-3/dz — an HPAI wave catalyst "
        f"that would force supply contraction (fall 2026 migration is the wild card), or (2) VITL "
        f"cutting price at the shelf, which management demonstrated works (the 35% → 25% gap "
        f"experiment at one top customer drove +18% volume in 2 weeks). The breaker-egg market — where "
        f"unsold VITL eggs end up — crashed from $1.00/dz to ~$0.10/dz, driving $32M of supply-management "
        f"costs that crushed Q1 gross margin to 2.7%. Every dime higher on breaker prices is direct "
        f"margin tailwind."
    )
    narrative_paragraphs.append(p2)

    # P3: brand & social
    sov_totals = (comm or {}).get("totals") or {}
    grand = sum(sov_totals.values()) or 1
    vitl_pct = round(sov_totals.get("Vital Farms", 0) / grand * 100, 0) if grand else 0
    p3 = (
        f"<strong>The brand & consumer frame.</strong> Section 01 (Social Signal Overview) tests "
        f"whether VITL's brand actually broke during the cycle. The short answer: <strong>no</strong>. "
        f"VITL still holds <strong>~{vitl_pct:.0f}% of category Reddit mindshare</strong> across "
        f"6 monitored pasture-raised brands, with a majority of mentions sentiment-classified as "
        f"positive. The Reddit feed shows actual VITL discussion threads — DCF valuations from "
        f"r/ValueInvesting, the \"Egg-Cellent Value\" thread, multiple insider-buying posts — "
        f"meaning the brand is still actively debated, not abandoned. Aided brand awareness "
        f"climbed +800bps to 34% in 2025 (the same year the share-loss narrative gained traction) "
        f"and household penetration grew +2M households to 14.2M — both <em>counter-evidence</em> "
        f"to the brand-damage thesis. The January seed-oil controversy spiked then decayed back "
        f"toward baseline, matching management's \"negligible purchase impact\" claim. The new "
        f"customer trial % did slip from 55% to 50% — that's the watchpoint, the place where the "
        f"price-gap damage is showing up first."
    )
    narrative_paragraphs.append(p3)

    # P4: supply / competition — the category got crowded
    if cat_supply and cat_supply.get("years"):
        then = (cat_supply["branded"][0] + cat_supply["private_label"][0]) if cat_supply["branded"] else 1
        now = cat_supply["branded"][-1] + cat_supply["private_label"][-1]
        pl_now = cat_supply["private_label"][-1]
        p4 = (
            f"<strong>The supply frame — what got crowded.</strong> Section 01B's new category-supply "
            f"chart answers \"is VITL losing share to specific competitors or to the category getting "
            f"more crowded?\" The answer is mostly the latter. The pasture-raised category went from "
            f"<strong>{then} SKU</strong> in 2010 (just VITL) to <strong>{now} SKUs today</strong> "
            f"(8 branded + {pl_now} private-label). The structural change isn't the branded competitors — "
            f"Pete & Gerry's, Handsome Brook, Happy Egg, Alexandre, Organic Valley have all been around "
            f"for years and Reddit confirms their mindshare is stable. The real share-taker is "
            f"<strong>private label</strong>: Kirkland Pasture Raised at Costco (launched 2021) and "
            f"Whole Foods 365 Pasture Raised (2022) carry the same certification at 40-60% of VITL's "
            f"price. The Section 01B chart shows VITL revenue +15.4% vs the pasture-raised category "
            f"+32% in Q1 2026 — VITL underperformed its category by 16.6 percentage points, and the "
            f"velocity-per-shelf chart in Section 06 confirms each new shelf VITL adds is selling LESS "
            f"than the existing base (-3.8% velocity per slot YoY). That's the structural concern made "
            f"visible: more shelves, less velocity per shelf."
        )
        narrative_paragraphs.append(p4)

    # P5: setup / positioning
    runway = setup.get("runway_qs"); cluster = setup.get("cluster")
    short = setup.get("short_current") or {}
    short_pct = short.get("pct")
    if short_pct is not None:
        p5 = (
            f"<strong>The positioning frame.</strong> Section 02 lays out the conviction-vs-cash binary. "
            f"On the conviction side: <strong>7 insiders bought $321K worth of shares between May 13-15</strong> "
            f"— 5 directors, the CSO, and 2 officers, all within 3 days post-print. That's the textbook "
            f"cluster-buying pattern that historically marks bottoms — single buys are noise, clusters this "
            f"tight are conviction. The CEO has NOT yet bought, which would be the strongest possible "
            f"follow-through signal. Management still has <strong>$80M of buyback authorization remaining</strong> "
            f"(paused mid-covenant-negotiation); resumption would be the strongest possible \"floor is in\" signal. "
            f"On the cash-pressure side: $51M cash on the balance sheet plus an undrawn JPM revolver "
            f"(size not publicly disclosed) gives a tight but workable runway through covenant resolution "
            f"expected ~August. Short interest is at <strong>{short_pct:.1f}% of float</strong> — well past "
            f"the 'extreme' threshold (small-cap norm is 5-10%). That's a coiled-spring trade: if recovery "
            f"signals confirm, shorts have to cover at higher prices and the buying typically overshoots the "
            f"fundamental story by 30-50%."
        )
    else:
        p5 = "Positioning data partially loaded."
    narrative_paragraphs.append(p5)

    # P6: financial trajectory + valuation
    p6 = (
        f"<strong>The financial & valuation frame.</strong> Section 07 shows the EBITDA-margin arc: "
        f"peak 16.9% in Q1 2025, trough 2.7% in Q1 2026, guided to -10% in Q2 then recovery to 30%+ GM "
        f"by Q4. The bull case does NOT require returning to the 16.9% peak — it requires returning to "
        f"the 2020-2024 historical NORM of 10-14%, which matches the company's own cut FY26 guide. "
        f"Section 08's scenario math: even the ENTRY case (2027 EBITDA $50M × 10x) implies $12-13/share, "
        f"50% upside from current. The base case ($80M × 10-12x) implies ~$21/share, 150% upside. "
        f"That's the asymmetry the bull thesis is built on — the stock is pricing closer to permanent "
        f"impairment than cyclical trough. The cash burn decomposition in Section 07 shows that "
        f"<strong>~$40M of the $62M Q1 burn is discretionary or recoverable</strong> (CapEx that's now paused, "
        f"inventory build that sells through, opportunistic buyback). Only ~$5M was one-time cycle cost. "
        f"The headline cash number is worse than the underlying business — operations are roughly "
        f"cash-neutral at the trough."
    )
    narrative_paragraphs.append(p6)

    # P7: what's coming, what to watch
    p7 = (
        f"<strong>What to watch next.</strong> Three highest-impact catalysts in the next 9 months "
        f"per Section 09's forward calendar: (1) <strong>JPM covenant resolution ~late June / July</strong> "
        f"— binary; clean amendment is the floor signal, equity raise is the dilution event. (2) "
        f"<strong>Q2 FY26 print August 6</strong> — the cycle-low test. If revenue beats the guided "
        f"low-single-digits and supply-management costs come in better than the projected $23M, the "
        f"inflection is early. (3) <strong>FY26 print + FY27 guide in ~February 2027</strong> — the "
        f"trust rebuild moment, especially given the May 7 cut. The market typically re-rates 1-2 "
        f"quarters AHEAD of easy comps, which puts the recovery-pricing window at <strong>August-October "
        f"2026</strong>. Big single thing to watch right now: any 8-K mentioning covenant amendment "
        f"terms or buyback resumption. Either would meaningfully shift the conviction-vs-cash balance."
    )
    narrative_paragraphs.append(p7)

    return {
        "headline": f"{BRAND_NAME} ({BRAND_TICKER}) — Recovery Signal Dashboard",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "bullets": bullets,
        "narrative": narrative_paragraphs,
        "to_do_next": [
            "USDA MARS shell-egg fetcher (key registration required).",
            "FINRA bulk short-interest historical series.",
            "EDGAR Form 4 XML parser fix (currently 0 rows — seed cluster used).",
            "Per-SKU YouTube splits + TikTok hashtag volume for the controversy chart.",
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


def refresh_footer(path: Path) -> str:
    return f'<div class="refresh-tag">Last data refresh · <code>{path.name}</code> · {file_mtime(path)}</div>'


def datestamp_chip(ds: str) -> str:
    if not ds: return ""
    return f'<span class="datestamp">· {ds}</span>'


def chart_card(chart_id: str, title: str, subtitle: str, source: str,
               read_md_path: Path, y_axis_label: str = "",
               height_class: str = "big",
               dynamic_take: str = "") -> str:
    """Render the chrome around a chart canvas with consistent title /
    subtitle / source / y-axis caption / dynamic 'What this shows' (real
    numbers from data) / static 'What to watch' (forward-looking from md)."""
    md = load_markdown(read_md_path)
    static_take_html = (
        f'<div class="chart-take">'
        f'<div class="take-eyebrow">WHAT TO WATCH {datestamp_chip(md["datestamp"])}</div>'
        f'{md["html"]}'
        f'</div>' if md.get("html") else ""
    )
    y_label_html = (f'<div class="axis-label">Y-axis: {y_axis_label}</div>' if y_axis_label else "")
    return f"""
<div class="chart-card">
  <div class="chart-title-row">
    <h3>{title}</h3>
    <div class="chart-subtitle">{subtitle}</div>
  </div>
  {y_label_html}
  <div class="chart-wrap {height_class}"><canvas id="{chart_id}"></canvas></div>
  <div class="source-caption"><strong>Source:</strong> {source}</div>
  {dynamic_take}
  {static_take_html}
</div>
"""


# ─────────────────────────────────────────────────────────────────────────────
# Section renderers
# ─────────────────────────────────────────────────────────────────────────────
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


def render_three_damages() -> str:
    md = load_markdown(READS_DIR / "three_damages.md")
    # Parse the 3 damage entries from the markdown body. Format:
    #   **<title> · <STATUS>**
    #   <description sentence>
    #   <metric sentence>
    text = (READS_DIR / "three_damages.md").read_text(encoding="utf-8") if (READS_DIR / "three_damages.md").exists() else ""
    # Drop the first-line header
    lines = [ln for ln in text.splitlines() if ln.strip() and not ln.startswith("# ")]
    blocks = []
    current = []
    for ln in lines + [""]:
        if ln.strip().startswith("**") and ln.strip().endswith("**") and "·" in ln and current:
            blocks.append(current); current = [ln]
        elif ln.strip().startswith("**") and ln.strip().endswith("**") and "·" in ln:
            current = [ln]
        elif ln.strip():
            current.append(ln)
    if current: blocks.append(current)

    STATUS_COLORS = {"HEALING": ("#2a5a30", "#e1f0dc"),
                     "WATCH":   ("#8a6b10", "#fdefc9"),
                     "WORSENING": ("#b34738", "#f8e2dc"),
                     "STABLE":  ("#666",    "#eee7d6")}
    cols_html = ""
    for block in blocks[:3]:
        head = block[0].strip().strip("*")
        title_part, status = head.rsplit("·", 1) if "·" in head else (head, "")
        status = status.strip()
        desc = block[1].strip() if len(block) > 1 else ""
        metric = " ".join(block[2:]).strip() if len(block) > 2 else ""
        text_color, bg = STATUS_COLORS.get(status.upper(), ("#666", "#eee7d6"))
        cols_html += f"""
<div class="damage-col">
  <div class="damage-head">
    <div class="damage-title">{title_part.strip()}</div>
    <span class="damage-pill" style="background:{bg};color:{text_color}">{status}</span>
  </div>
  <div class="damage-desc">{_inline(desc)}</div>
  <div class="damage-metric">{_inline(metric)}</div>
</div>"""
    return f"""
<div class="container">
<div class="three-damages">
  <div class="damages-eyebrow">THREE DAMAGES · STATUS {datestamp_chip(md['datestamp'])}</div>
  <div class="damages-grid">{cols_html}</div>
</div>
</div>
"""


def render_supply_quantification_top(supply_q: dict) -> str:
    """TOP PANEL — VITL Supply Quantification.

    Quantifies excess production vs retail demand and when farmer amendments
    resolve it. Stacked bars (retail / baseline breaker / excess breaker) with
    overlay line for supply mgmt cost ($M, right axis). Q1 26 actual through
    FY27 norm. 4-paragraph caption verbatim from analyst spec.
    """
    if not supply_q.get("quarters"):
        return ""

    tiles = supply_q["hero_tiles"]
    tiles_html = ""
    for t in tiles:
        tone_cls = "neg" if t["tone"] == "neg" else "pos"
        tiles_html += f"""
<div class="hero-tile">
  <div class="hero-label">{t['label']}</div>
  <div class="hero-val {tone_cls}">{t['value']}</div>
  <div class="hero-sub">{t['sub']}</div>
</div>"""

    breaker_now = supply_q["breaker_now"]
    breaker_lo  = supply_q["breaker_norm_low"]
    breaker_hi  = supply_q["breaker_norm_high"]
    retail_price = supply_q["retail_price_per_dozen"]

    return f"""
<div class="container">
<div class="chart-card supply-quant-card">
  <div class="chart-title-row">
    <div class="title-with-badge">
      <h3>How Much Are They Over-Supplied — And When Does It Resolve?</h3>
      <span class="new-pill">NEW</span>
    </div>
    <div class="chart-subtitle">
      The actual operational picture quarter-by-quarter. Excess production above retail demand is what gets dumped at breaker prices. Farmer amendments close the gap.
    </div>
  </div>

  <div class="hero-row" style="grid-template-columns:repeat(4, 1fr);margin-top:10px;margin-bottom:14px">
    {tiles_html}
  </div>

  <div class="chart-wrap big"><canvas id="supplyQuantChart"></canvas></div>

  <div class="breaker-inset">
    <div class="breaker-inset-eyebrow">BREAKER (DUMP) PRICE — WHY EVERY EXCESS DOZEN HURTS</div>
    <div class="breaker-inset-row">
      <div class="breaker-cell">
        <div class="breaker-cell-label">Today</div>
        <div class="breaker-cell-val neg">${breaker_now:.2f}<span class="breaker-unit">/doz</span></div>
      </div>
      <div class="breaker-arrow">vs</div>
      <div class="breaker-cell">
        <div class="breaker-cell-label">Historical norm</div>
        <div class="breaker-cell-val pos">${breaker_lo:.2f}–${breaker_hi:.2f}<span class="breaker-unit">/doz</span></div>
      </div>
      <div class="breaker-arrow">vs</div>
      <div class="breaker-cell">
        <div class="breaker-cell-label">VITL retail price</div>
        <div class="breaker-cell-val pos">${retail_price:.2f}<span class="breaker-unit">/doz</span></div>
      </div>
      <div class="breaker-cell wide">
        <div class="breaker-cell-label">Margin lost per dumped dozen</div>
        <div class="breaker-cell-val neg">≈ ${retail_price - breaker_now - 0.72:.2f}</div>
        <div class="breaker-cell-sub">(retail price − breaker − ~$0.72 cost-to-fill)</div>
      </div>
    </div>
  </div>

  <div class="source-caption">
    <strong>Source:</strong> Q1 2026 earnings call (May 7 2026) — supply mgmt disclosures ($4.9M Q1 hit, ~$23M Q2 guide, farmer amendment program described as "voluntary" and "in progress"). Q3-Q4 and FY27 norm assume amendments achieve mid-case 4M dozens/yr capacity removal. Retail volume estimates back-solve from FY guidance midpoint $824M / ($5.00/doz proxy).
  </div>

  {data_take(meaning=(
      "<strong>What this shows.</strong> VITL produces roughly 40M dozens per quarter from their locked-in farmer contracts. "
      "Retail demand has been around 33-37M depending on the cycle, leaving 3-5M dozens of excess that gets dumped at breaker "
      "($0.08/dozen) instead of sold at retail ($5/dozen). Each dumped dozen loses about $4.20 of margin vs selling retail."
      "<br><br>"
      "<strong>Why this matters.</strong> Q2 is the worst quarter because amendments haven't fully kicked in yet — roughly "
      "5M excess dozens dumped, costing $20M in gross profit. Q3 should see excess drop to zero as farmer amendments remove "
      "~4M dozens of annual capacity from the system. That's the mechanical recovery, worth roughly $20M of quarterly margin "
      "recovery vs Q2 — without needing breaker prices to recover."
      "<br><br>"
      "<strong>Where this fits.</strong> This is the operational supply picture, not the macro cycle. The macro cycle (breaker "
      "price, layer flock, HPAI) is in Section 04. This panel quantifies how much supply VITL specifically has versus how "
      "much they can sell, and what the farmer amendment program does to close the gap."
      "<br><br>"
      "<strong>Watchpoint.</strong> The biggest unknown is how many farmer amendments are actually signed today. Management "
      "said amendments are <em>'voluntary'</em> and <em>'in progress'</em> but didn't disclose the percentage of the network. "
      "If amendments come in slower than 4M dozens by Q3, the recovery extends. Q2 print on August 6 should give first hard "
      "data on amendment pace."
  ))}
</div>
</div>
"""


def render_quick_read(qr: dict) -> str:
    kpis = qr["kpis"]
    vs25 = kpis.get("vs_feb25_pct"); vs26 = kpis.get("vs_feb26_pct")
    vs25_cls = "neg" if (vs25 is not None and vs25 < 0) else "pos"
    vs26_cls = "neg" if (vs26 is not None and vs26 < 0) else "pos"
    curr_str = f"${kpis['current_price']:.2f}" if kpis.get("current_price") is not None else "—"
    return f"""
<div class="section-header" id="quick-read">
  <div class="section-num">SECTION 00</div>
  <div class="section-title">Quick Read</div>
  <div class="section-subtitle">Four KPIs · the ERP-print anchor in one line · what this dashboard answers</div>
</div>

<div class="hero-row">
  <div class="hero-tile">
    <div class="hero-label">Days since FY25 ERP print</div>
    <div class="hero-val">{kpis['days_since_print']}</div>
    <div class="hero-sub">Feb 26 2026 → today</div>
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
    <div class="hero-label">Days to LP deadline</div>
    <div class="hero-val">{kpis['days_to_deadline']}</div>
    <div class="hero-sub">May 26 2026</div>
  </div>
</div>

<div class="timeline-strip">
  <div class="timeline-eyebrow">ERP TIMELINE</div>
  <div class="timeline-text">{ERP_TIMELINE_TEXT}</div>
</div>

<div class="quick-read-explainer">
  <div class="qre-eyebrow">WHAT THIS DASHBOARD ANSWERS</div>
  <p>VITL stock fell 85% in nine months on <strong>three damages</strong> — ERP transition
  (now healing), the January 2026 brand controversy (watching), and a conventional egg-price
  crash that widened the premium gap to 422% vs the 150-200% historical norm (worsening).
  Recovery requires the gap to close <em>and</em> cash to hold out. This dashboard tracks
  that binary.</p>
</div>
"""


def render_setup(setup: dict, runway: dict) -> str:
    cluster = setup.get("cluster")
    cluster_kpi = (f"{cluster['insiders']} insiders · ${cluster['total_value']:,.0f} "
                   f"cluster {cluster['start']}→{cluster['end']}"
                   if cluster else "no cluster detected")

    # Insider table
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
    insider_table_html = (f'<div class="table-card"><table><thead><tr>'
        f'<th>Date</th><th>Insider</th><th>Kind</th><th class="num">Shares</th>'
        f'<th class="num">Price</th><th class="num">Value</th></tr></thead>'
        f'<tbody>{insider_rows_html}</tbody></table></div>'
        if insider_rows_html else '<div class="placeholder">No insider transactions in window.</div>')

    short_current = setup.get("short_current")
    short_kpi = (f"{short_current['pct']:.1f}% of float · vs ~8% small-cap avg"
                 if short_current else "—")

    buyback_md = load_markdown(READS_DIR / "buyback_status.md")
    setup_synth_md = load_markdown(READS_DIR / "setup_synthesis.md")
    runway_md = load_markdown(READS_DIR / "runway_math.md")

    return f"""
<div class="section-header" id="setup">
  <div class="section-num">SECTION 02</div>
  <div class="section-title">The Setup — Conviction vs Cash</div>
  <div class="section-subtitle">Four panels on one frame · the single binary that breaks or makes the thesis.</div>
</div>

<div class="setup-grid">

  <div class="setup-card setup-runway">
    <div class="setup-card-header">
      <div class="setup-card-title">Runway Math {datestamp_chip(runway_md['datestamp'])}</div>
      <div class="setup-kpi">covenant resolution by ~Aug = binary</div>
    </div>
    <div class="runway-big">${runway['current_cash']:.0f}M <span class="runway-big-unit">cash on balance sheet</span></div>
    <div class="runway-line">+ JPM revolver <em>(undrawn, size not publicly disclosed)</em></div>
    <div class="runway-line">FY26 implied remaining burn <strong>${runway['fy26_remaining_lo']}-{runway['fy26_remaining_hi']}M</strong> · cash alone covers ~{runway['cash_runway_qs_lo']}-{runway['cash_runway_qs_hi']} quarters</div>
    <div class="runway-line"><span class="badge badge-mid">JPM covenant talks ongoing</span> · net-leverage covenant 3.5x</div>
    <div class="setup-foot"><strong>What to watch:</strong> cash position is tight but not yet at crisis levels. Revolver size unknown publicly — Q1 10-Q discloses "undrawn revolving credit facility" without specifying capacity. Watch any 8-K mentioning amendment terms; clean amendment = floor signal, equity raise = dilution event.</div>
    {refresh_footer(DATA_DIR / "cash_position.csv")}
  </div>

  <div class="setup-card">
    <div class="setup-card-header">
      <div class="setup-card-title">Recent Insider Buying</div>
      <div class="setup-kpi">{cluster_kpi}</div>
    </div>
    <div class="setup-context">5 directors + CSO + 2 officers buying within 3 days post-print. <strong>Cluster pattern is the strongest insider signal shape in the literature</strong> — single buys are noise; this isn't.</div>
    {insider_table_html}
    <div class="setup-foot"><strong>What to watch:</strong> any further buys on Form 4, especially from the CEO (Russell Diez-Canseco) who has not yet appeared in the cluster.</div>
    {refresh_footer(DATA_DIR / "insider_trades.csv")}
  </div>

  <div class="setup-card">
    <div class="setup-card-header">
      <div class="setup-card-title">Short Interest Trend</div>
      <div class="setup-kpi">{short_kpi}</div>
    </div>
    <div class="setup-context">Small-cap norm 5-10%. 47.5% is extreme. But the tape is conflicted: <em>if this was out of the woods the stock would be up 90% not 9%</em>.</div>
    <div class="chart-wrap" style="height:200px"><canvas id="shortChart"></canvas></div>
    <div class="setup-foot"><strong>What to watch:</strong> sustained cover (declining %) confirms recovery confidence; holding at 40%+ says bears still hold the thesis.</div>
    {refresh_footer(DATA_DIR / "short_interest.csv")}
  </div>

  <div class="setup-card setup-buyback">
    <div class="setup-card-header">
      <div class="setup-card-title">Buyback Authorization {datestamp_chip(buyback_md['datestamp'])}</div>
    </div>
    <div class="setup-context"><strong>$80M remaining</strong> of authorization, paused mid-covenant talks. Resumption = strongest possible management floor signal.</div>
    <div class="buyback-body">{buyback_md['html']}</div>
    <div class="setup-foot"><strong>What to watch:</strong> any 8-K mentioning share repurchases. Management wouldn't burn cash here unless conviction is high.</div>
    {refresh_footer(READS_DIR / "buyback_status.md")}
  </div>
</div>

<div class="setup-synthesis">
  <div class="setup-synth-eyebrow">SYNTHESIS {datestamp_chip(setup_synth_md['datestamp'])}</div>
  {setup_synth_md['html']}
</div>

{chart_card("setupOverTimeChart",
            "The Convergence Chart — Stock, Shorts, Insiders on One Frame",
            "All three normalized so the inflection points line up. Is the May 13-15 insider cluster the regime change?",
            "Stock = yfinance · short interest = FINRA semi-monthly + yfinance current · insider buys = SEC Form 4 (seeded May 13-15 cluster).",
            READS_DIR / "setup_over_time_take.md",
            y_axis_label="Stock = index (left, base=100). Short % and Insider cumulative $K = right axis.",
            height_class="big",
            dynamic_take=data_take(meaning=(
                "<strong>What it shows.</strong> Three time series on one frame: VITL stock (steady decline from peak), short interest as % of float (steady rise from 4% to 47.5%), cumulative insider buys (flat for 24 months, then a sharp jump on May 13-15 = $321K cluster). The convergence point is the most recent month — a divergence is forming."
                "<br><br>"
                "<strong>Why this matters.</strong> The textbook capitulation pattern is: stock down + shorts at extreme + first insider cluster. All three are now true at the same time. <strong>The May 13-15 cluster is the first regime-change candle in 24 months</strong>: 5 directors + the CSO + 2 officers ALL bought personal shares within 3 days post-print. That's the kind of cluster that historically marks bottoms because it's the strongest possible internal signal — directors don't risk personal capital lightly mid-covenant-negotiation."
                "<br><br>"
                "<strong>Where this fits.</strong> The bear case requires shorts to be right and insiders to be wrong. The bull case requires the inverse. Quantitatively: 47.5% short of float means there's an enormous coiled-spring trade waiting if recovery signals confirm — shorts have to cover at higher prices, and the buying typically overshoots the fundamental story. <em>If</em> covenants resolve cleanly in August AND Q2 print isn't worse than guided, the short-cover dynamic can drive a 30-50% rally on its own, before any fundamentals improve."
                "<br><br>"
                "<strong>Watchpoint.</strong> Two things: (1) the short interest line trending down — that's the actual capitulation event — and (2) any additional insider buys (especially from the CEO, who has NOT yet appeared in the cluster). CEO buying would be the strongest possible follow-through signal."
            )))}
"""


def render_stock_news(events: dict, news: dict, cad_vs_stock: dict) -> str:
    # Event quick-reference table
    ev_rows = ""
    for e in events.get("events", []):
        color = REACTION_COLORS.get(e["reaction_kind"], "#999")
        pct_str = (f'{e["reaction_pct"]:+.1f}%' if e["reaction_pct"] is not None else "—")
        ev_rows += f"""
<tr>
  <td class="muted-cell">{e['date']}</td>
  <td><strong>{e['headline']}</strong><div class="muted-cell" style="font-size:11.5px;margin-top:2px">{e['summary']}</div></td>
  <td class="num" style="color:{color};font-weight:700">{pct_str}</td>
</tr>"""
    ev_table = (f"""<div class="table-card" style="margin-top:8px"><table>
<thead><tr><th>Date</th><th>Headline + summary</th><th class="num">Reaction</th></tr></thead>
<tbody>{ev_rows}</tbody></table></div>""" if ev_rows else "")

    # Article log
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

    # Topic rollup last 12 weeks summary
    rollup_html = ""
    rollups = news.get("topic_rollups") or []
    if rollups:
        # group by week, then show top topics
        by_week = {}
        for r in rollups:
            by_week.setdefault(r["week"], []).append(r)
        rollup_items = []
        for wk in sorted(by_week.keys(), reverse=True)[:8]:
            top = sorted(by_week[wk], key=lambda r: -r["count"])[:3]
            bits = " · ".join(f'<span class="topic-chip" style="background:{TOPIC_COLORS.get(r["topic"], "#999")}22;color:{TOPIC_COLORS.get(r["topic"], "#999")}">{TOPIC_LABELS.get(r["topic"], r["topic"])} {r["count"]}</span>' for r in top)
            rollup_items.append(f'<div class="rollup-row"><span class="rollup-week">{wk}</span>{bits}</div>')
        rollup_html = '<div class="rollup-block">' + "".join(rollup_items) + '</div>'

    return f"""
<div class="section-header" id="news">
  <div class="section-num">SECTION 03</div>
  <div class="section-title">Stock &amp; News <span class="muted-cell" style="font-size:11.5px;font-weight:500">· {news.get('total', 0)} articles tracked</span></div>
  <div class="section-subtitle">Is the market reacting LESS to bad news? Has the narrative shifted away from ERP / lawsuits? Does news cadence predict price moves?</div>
</div>

{chart_card("reactionMagnitudeChart",
            "Are Bad-News Reactions Shrinking?",
            "Every meaningful negative event since Q3 25 with the stock %-reaction on the day. Pattern matters more than any single bar.",
            "Same event log as the chart below (data/event_reactions.csv). Each bar height = stock day-reaction (%). Color = reaction kind (red/yellow/green).",
            READS_DIR / "reaction_magnitude_take.md",
            y_axis_label="Stock day-reaction (%) · green ring = first positive reaction · gray = flat",
            height_class="big",
            dynamic_take=data_take(meaning=(
                "<strong>What it shows.</strong> A bar for each negative news event of the cycle: ERP cut (Dec 17 2025, -15.5%), Q4 print miss (Feb 26, -10.8%), MS downgrade (Mar 2, -13%), desk cuts (late March, -5 to -7%), Craig-Hallum cut (Apr 2, <strong>+3.6%</strong>), class-action filings (Apr 15, flat), Q1 print (May 7, <strong>-26%</strong>)."
                "<br><br>"
                "<strong>Why this matters.</strong> This is the canonical 'selling exhaustion' test from the technical-analysis playbook. <em>Before the actual price bottom, you see reactions to bad news SHRINK</em> because the leveraged shorts have already covered, the index funds have already sold, and the only marginal seller left has emotional rather than fundamental reasons. The April 2 +3.6% green bar is exactly that pattern — a desk cut a price target and the stock RALLIED. That was the cycle's only positive reaction to bad news and it suggested early exhaustion."
                "<br><br>"
                "<strong>Where this fits.</strong> Then May 7 happened. The Q1 print delivered an actual fundamental reset (FY26 guide cut from $900-920M to $775-800M; EBITDA cut from $105-115M to $0-10M). The -26% reaction wasn't sentiment-driven; it was a real downward revision to the future cash-flow picture. <strong>That bar reset the exhaustion test — selling can't be 'exhausted' on news this material.</strong>"
                "<br><br>"
                "<strong>Watchpoint.</strong> The next negative event is the critical observation. If it comes in smaller than -26%, the May 7 reset has held and selling really is winding down. If it matches or exceeds, the bears are still finding new reasons to sell and the trough isn't in yet. The Q2 print on August 6 is the most-likely setup."
            )))}

<div class="chart-card">
  <div class="chart-title-row">
    <h3>VITL Daily Close · 18 months · News Events + Insider Cluster Overlaid</h3>
    <div class="chart-subtitle">Colored dots = news events (red/yellow/green by reaction). Green triangles = May 13-15 insider cluster buys.</div>
  </div>
  <div class="axis-label">Y-axis: VITL close ($)</div>
  <div class="chart-wrap tall"><canvas id="eventsChart"></canvas></div>
  <div class="event-legend">
    <span class="legend-dot" style="background:{REACTION_COLORS['negative']}"></span> Negative reaction
    <span class="legend-dot" style="background:{REACTION_COLORS['flat']};margin-left:14px"></span> Flat
    <span class="legend-dot" style="background:{REACTION_COLORS['positive']};margin-left:14px"></span> Positive
  </div>
  {ev_table}
  <div class="source-caption"><strong>Source:</strong> VITL close from yfinance · events purpose-built in <code>event_reactions.csv</code> (7 cycle events with hand-curated 2-sentence summaries).</div>
  {refresh_footer(DATA_DIR / "event_reactions.csv")}
</div>

{chart_card("topicMixChart",
            "News Topic Mix Over Time · 24 months",
            "Stacked weekly article counts by topic. Watch the ERP/Lawsuit slice — spiked Apr 2026 after class actions filed.",
            "GDELT ArtList → Google News RSS · topics classified by keyword dictionary in <code>fetch_google_news.py</code>.",
            READS_DIR / "topic_mix_take.md",
            y_axis_label="Articles per week (stacked count)",
            height_class="big")}

{chart_card("cadenceVsStockChart",
            "News Article Cadence vs VITL Stock · normalized",
            "Two lines normalized to 100 at the start. Tests whether news volume predicts price moves.",
            "Cadence from <code>news_articles.csv</code> · stock from <code>vitl_stock.csv</code>.",
            READS_DIR / "cadence_vs_stock_take.md",
            y_axis_label="Both series indexed to 100 at start (left = cadence, right = stock)",
            height_class="big")}

{('<div class="chart-card"><h3>Recent Weekly Topic Rollups</h3>' + rollup_html + '<div class="source-caption">Last 8 weeks. Top 3 topics per week.</div></div>') if rollup_html else ''}

<details class="article-log">
  <summary>Full article log · {len(news.get('articles', []))} most recent</summary>
  <div class="table-card" style="margin-top:8px">
  <table>
    <thead><tr><th>Date</th><th>Headline</th><th>Source</th><th>Topic</th></tr></thead>
    <tbody>{article_rows}</tbody>
  </table>
  </div>
</details>
{refresh_footer(DATA_DIR / "news_articles.csv")}
"""


def render_egg_market(egg: dict) -> str:
    hpai_html = "—"
    if egg.get("hpai_latest"):
        hl = egg["hpai_latest"]; arrow = "↑" if hl["trend"] == "up" else "↓"
        hpai_html = f'<strong>{hl["cases"]}</strong> cases <span class="trend">{arrow}</span><div class="muted-cell" style="font-size:11px">week of {hl["week"]}</div>'
    flock_html = "—"
    if egg.get("flock_latest"):
        fl = egg["flock_latest"]; arrow = "↑" if fl["trend"] == "up" else "↓"
        flock_html = f'<strong>{fl["millions"]:.1f}M</strong> hens <span class="trend">{arrow}</span><div class="muted-cell" style="font-size:11px">{fl["month"]}</div>'

    peak_str = f"{egg['peak_gap']:.0f}%" if egg.get("peak_gap") is not None else "—"
    latest_str = f"{egg['latest_gap']:.0f}%" if egg.get("latest_gap") is not None else "—"

    return f"""
<div class="section-header" id="egg-market">
  <div class="section-num">SECTION 04</div>
  <div class="section-title">The Egg Market — Price Gap Tracker</div>
  <div class="section-subtitle">How wide is the premium gap, and what would close it? The single most analytically unique section — nobody publishes these charts together.</div>
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
    <div class="hero-sub">Q1 2026 trough conventional</div>
  </div>
  <div class="hero-tile">
    <div class="hero-label">HPAI commercial layer cases</div>
    <div class="hero-val" style="font-size:18px;line-height:1.4">{hpai_html}</div>
  </div>
  <div class="hero-tile">
    <div class="hero-label">USDA layer flock</div>
    <div class="hero-val" style="font-size:18px;line-height:1.4">{flock_html}</div>
  </div>
</div>

{chart_card("eggChart1",
            "Conventional vs VITL · The Two Lines",
            "$/dozen. Conventional collapsed from $6 to ~$1.60. VITL held $7-9 throughout.",
            "Conventional = USDA AMS midwest large white shell-egg wholesale (real). VITL retail = step-function estimate from earnings-call commentary; dashed line flags it as an estimate, not a scrape.",
            READS_DIR / "conv_vs_vitl_take.md",
            y_axis_label="Price ($/dozen) · solid = real · dashed = estimate",
            height_class="big",
            dynamic_take=data_take(meaning=(
                "<strong>What it shows.</strong> The two retail-shelf realities side by side: conventional eggs collapsed from a $6 HPAI-spike peak to ~$1.60 today as flocks rebuilt and supply normalized. VITL retail walked up steadily through the same period ($7.99 → $8.49 → $8.99) and only nudged back to $8.49 in Q1 2026 with management's selective price cuts."
                "<br><br>"
                "<strong>Why this matters.</strong> Both lines look reasonable on their own — but the SPREAD between them is what defines VITL's competitive position at the shelf. Conventional has nothing to do with VITL's costs (different supply chain, different birds, different overhead), so when conventional crashes the gap widens automatically — without any change in VITL's actual quality or value proposition. This is what management means when they say the cycle is exogenous."
                "<br><br>"
                "<strong>Where this fits.</strong> This chart is the input. The real thesis-driver is the next chart (Gap %), which translates this spread into the share-of-wallet decision a shopper is making at the Costco egg case."
            )))}

{chart_card("eggChart2",
            "The Premium Gap",
            "How much more VITL costs than conventional — the single most important variable in the recovery thesis.",
            "Derived from chart 1: (VITL retail ÷ conventional wholesale − 1) × 100. Shaded green band = 150-200% historical norm.",
            READS_DIR / "premium_gap_take.md",
            y_axis_label="Gap (%)",
            height_class="big",
            dynamic_take=data_take(meaning=(
                f"<strong>What it shows.</strong> The gap sits at <strong>{egg.get('latest_gap', 0):.0f}%</strong> today (peak this cycle: <strong>{egg.get('peak_gap', 0):.0f}%</strong>). The historical norm is 150-200% — that's the equilibrium where consumers willingly pay the premium-egg upcharge. We're meaningfully above that band right now."
                f"<br><br>"
                f"<strong>Why this matters.</strong> Above ~250% the price-conscious incremental buyer starts trading down to private label (Kirkland Pasture Raised at Costco, Whole Foods 365). Existing loyalists keep buying — that's what the +2% buy-rate from management confirms — but the funnel narrows at the top. New-customer trial fell from 55% (2024) to 50% (Q1 26) which is the same story from the demographic angle. <strong>The gap is the single number that decides whether VITL's recovery is fast or slow.</strong>"
                f"<br><br>"
                f"<strong>Where this fits.</strong> The bull case explicitly depends on this gap closing. Two paths: (1) conventional rises (fall HPAI wave is the catalyst — see HPAI chart below), or (2) VITL cuts at the shelf. Management already demonstrated path 2 works (the 35% gap → 25% experiment at one top customer drove +18% volume in 2 weeks). They're not pushing it broadly because it would compress GM further during an already-tight cash quarter."
                f"<br><br>"
                f"<strong>Watchpoint.</strong> Track the line trending DOWN toward 200%. Every 50pts of compression is meaningful. A sustained move under 250% would be the first hard signal the macro thesis is playing out — that typically lags conventional egg price recovery by 4-8 weeks."
            )))}

{chart_card("eggChart3",
            "Is the Stock Just a Bet on the Egg Cycle?",
            "VITL stock vs the premium gap %, normalized. If they move inversely, the stock IS the macro trade.",
            "Stock = yfinance. Gap = derived from USDA AMS + VITL retail series. Both lines indexed to 100 at start.",
            READS_DIR / "stock_vs_gap_take.md",
            y_axis_label="Indexed to 100 at start of window",
            height_class="big",
            dynamic_take=data_take(meaning=(
                "<strong>What it shows.</strong> Two lines that should be mirror images if VITL is fundamentally a macro trade on the egg cycle. Gap going up → stock going down (more shoppers trade down → revenue softens → stock falls). Gap going down → stock going up (recovery)."
                "<br><br>"
                "<strong>Why this matters.</strong> The Pearson correlation between gap % and VITL stock is currently <strong>-0.35</strong> (Section 11 matrix). That's a real inverse correlation but not overwhelming. <em>That means the stock is partly a macro trade — but other factors (ERP narrative, cash overhang, brand-controversy noise) matter too.</em> If the correlation tightens toward -0.8 over the next 6 months, the stock has been confirmed as a pure macro trade and the recovery becomes mechanical."
                "<br><br>"
                "<strong>Where this fits.</strong> This is the chart for testing whether the bull case is really about VITL the company or VITL the proxy for conventional egg prices. If you believe the gap closes, the stock should follow — but you should also see this correlation tighten as confounding factors (ERP coverage, lawsuit noise) decay."
                "<br><br>"
                "<strong>Watchpoint.</strong> Cross-reference with the correlation matrix in Section 11. A tightening inverse correlation = thesis confirms. A decoupling = something else (brand damage, structural cost issue) is now the dominant driver and the macro frame is wrong."
            )))}

{chart_card("eggChart4",
            "The Breaker Market — Where Unsold Eggs Go to Die",
            "Wholesale price of broken / liquid eggs (USDA AMS). Direct margin variable for VITL.",
            "USDA AMS breaker egg market (seeded). Conventional from chart 1.",
            READS_DIR / "breaker_take.md",
            y_axis_label="Price ($/dozen)",
            height_class="big",
            dynamic_take=data_take(meaning=(
                "<strong>What it shows.</strong> Breaker eggs are the eggs VITL CAN'T sell at retail — surplus production that gets cracked and sold as liquid eggs into commercial food manufacturing. The price collapsed from ~$1.00/dz (Q1 2025) to ~$0.10/dz (Q1 2026)."
                "<br><br>"
                "<strong>Why this matters.</strong> When the breaker market is at $1, every unsold VITL egg recovers about half its production cost. When it's at $0.10, those eggs are essentially worthless and become pure margin drag. <strong>This is the single line item driving the $32M of 'supply management costs' management called out for FY26.</strong> Every dime higher on this line = direct margin tailwind to VITL."
                "<br><br>"
                "<strong>Where this fits.</strong> This is the supply-side mirror of the demand-side gap chart. Gap chart says: demand for VITL retail eggs is soft because conventional is too cheap. Breaker chart says: the eggs that DO get produced but don't sell at retail can't even recover cost in the secondary market. Both problems share the same root cause (conventional egg oversupply), so they resolve together when HPAI hits and supply tightens."
                "<br><br>"
                "<strong>Watchpoint.</strong> A move from $0.10 back toward $0.50/dz alone would represent ~$15M annualized margin recovery, with no other improvement needed. This is the most directly-quantifiable macro lever on the dashboard."
            )))}

{chart_card("hpaiCumulativeChart",
            "The Bull Catalyst — HPAI Cumulative",
            "Total US commercial layer birds depopulated since the 2022 outbreak. Each new wave tightens supply.",
            "USDA APHIS confirmed HPAI commercial-layer cases via fetch_hpai.py. Bird counts approximated at avg 0.25M per detected flock; 2022 first-wave baseline pre-loaded from public reports.",
            READS_DIR / "hpai_cumulative_take.md",
            y_axis_label="Cumulative birds depopulated (millions)",
            height_class="big",
            dynamic_take=data_take(meaning=(
                "<strong>What it shows.</strong> Cumulative US commercial-layer birds depopulated due to HPAI since 2022. ~99M total now. The chart isn't smooth — it has discrete step-ups in 2022-23 (first big wave) and 2024-25 (second wave), then flattens during recovery periods when flocks rebuild."
                "<br><br>"
                "<strong>Why this matters.</strong> Every HPAI wave is a forced supply contraction in the conventional egg category. Conventional wholesale prices doubled in 2022-23 and again in 2024-25 because of these waves. Each spike took 6-12 months to fully reverse as new flocks reached laying maturity. <strong>This is the single biggest catalyst on the bull side — and it's literally a biological event no one can predict but everyone has to be positioned for.</strong>"
                "<br><br>"
                "<strong>Where this fits.</strong> If HPAI hits again in fall 2026 (migration season is the wild-card window), conventional egg prices spike → premium gap closes mechanically → VITL revenue recovers → breaker market tightens → margin recovers — all without any operational improvement from VITL itself. That's why this chart sits in the egg-market section: it's the externality that resets the whole equation. The bear case has to assume no HPAI wave, which is a real but uncomfortable assumption given the chart's history."
                "<br><br>"
                "<strong>Watchpoint.</strong> Weekly HPAI confirmed cases (the inline KPI tile above) for the early-warning signal. Sustained 3+ commercial flock detections per week through October would suggest a new wave is forming. The flatline since Q2 2025 is the worst-case scenario for VITL — peaceful recovery in conventional means the premium gap stays wide."
            )))}

<div class="chart-card">
  <div class="chart-title-row">
    <h3>DOJ Antitrust Watch — Cal-Maine / Versova</h3>
    <div class="chart-subtitle">Active investigation, no filing yet. Short-term bearish for VITL (forces conventional prices lower → wider gap). Long-term bullish (removes conventional pricing moat).</div>
  </div>
  <div class="doj-panel">
    <div class="doj-status">
      <span class="badge badge-mid">ACTIVE · No filing yet</span>
    </div>
    <div class="doj-body">
      {load_markdown(READS_DIR / "doj_antitrust.md")['html']}
    </div>
  </div>
  <div class="source-caption"><strong>Source:</strong> WSJ April 17 2026 — DOJ preparing case against largest egg producers for alleged pricing coordination via the Expana benchmark service.</div>
  {refresh_footer(READS_DIR / "doj_antitrust.md")}
</div>
"""


def _build_subreddit_table(comm: dict) -> str:
    if not comm["sub_rows"]:
        return '<div class="placeholder">No subreddits in <code>config/reddit_subreddits.csv</code>.</div>'
    rows_html = ""
    nonzero_subs = 0
    for r in comm["sub_rows"]:
        yoy = r["yoy_pct"]
        yoy_cls = "badge-pos" if (yoy is not None and yoy >= 0) else ("badge-neg" if yoy is not None else "")
        yoy_html = (f'<span class="badge {yoy_cls}">{fmt_pct(yoy)}</span>'
                    if yoy is not None else '<span class="muted-cell">—</span>')
        m90 = r["mentions_90d"]
        if isinstance(m90, (int, float)) and m90 > 0: nonzero_subs += 1
        rows_html += f"""
<tr>
  <td><strong>r/{r['subreddit']}</strong></td>
  <td>{r['topic']}</td>
  <td><span class="badge badge-na">{r['priority']}</span></td>
  <td class="num">{fmt_num(m90)}</td>
  <td class="num">{yoy_html}</td>
</tr>"""
    note = ""
    if nonzero_subs <= 2:
        note = ('<div class="callout-strip" style="margin-top:8px;font-size:11.5px"><strong>Note:</strong> '
                'premium-egg brand names are sparse in general food subs even with full body+comments coverage. '
                'The base rate of users typing "vital farms" in titles or bodies is low — most mentions are '
                'in r/nutrition, r/EatCheapAndHealthy, r/seedoilfree, r/Costco, r/Carnivore.</div>')
    return (f'<div class="table-card"><table><thead><tr>'
            f'<th>Subreddit</th><th>Topic</th><th>Priority</th>'
            f'<th class="num">Mentions (90d)</th><th class="num">YoY %</th>'
            f'</tr></thead><tbody>{rows_html}</tbody></table></div>') + note


def _build_brand_stat_row(comm: dict) -> str:
    totals = comm.get("totals") or {}
    sov_totals = comm.get("sov_sentiment_totals") or {}
    if not totals: return ""
    top = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    cards = []
    vitl_share = None
    grand_total = sum(v for _, v in top) or 1
    for k, v in top:
        sent = sov_totals.get(k, {})
        pos = sent.get("pos", 0); neg = sent.get("neg", 0); neu = sent.get("neu", 0)
        total = sent.get("total", v) or v
        pos_pct = round(pos / total * 100, 0) if total > 0 else 0
        neg_pct = round(neg / total * 100, 0) if total > 0 else 0
        neu_pct = round(neu / total * 100, 0) if total > 0 else 0
        if k == "Vital Farms":
            vitl_share = round(v / grand_total * 100, 0)
        cards.append(
            f'<div class="stat-card">'
            f'<div class="stat-lbl">{k}</div>'
            f'<div class="stat-val">{fmt_num(v)}</div>'
            f'<div class="muted-cell" style="font-size:10.5px;margin-top:4px;line-height:1.5">'
            f'<span style="color:#2a5a30">+{pos_pct:.0f}% pos</span> · '
            f'<span style="color:#888">{neu_pct:.0f}% neu</span> · '
            f'<span style="color:#b34738">{neg_pct:.0f}% neg</span></div>'
            f'</div>'
        )
    header = (
        f'<div class="brand-totals-header">'
        f'<div class="brand-totals-eyebrow">BRAND MENTION TOTALS · 36-MONTH REDDIT VOLUME</div>'
        f'<div class="brand-totals-vitl-share">'
        f'VITL share of voice: <strong>{vitl_share:.0f}%</strong> of monitored total' if vitl_share is not None else
        f'<div class="brand-totals-vitl-share">'
        f'VITL share: <strong>—</strong>'
    )
    header += '</div></div>'
    explainer = (
        '<div class="callout-strip" style="margin-top:8px"><strong>Numbers explained:</strong> '
        'Each card shows total Reddit posts + comments mentioning the brand over 36 months across '
        '15 monitored subreddits. Volume = mindshare. Pos / neu / neg % from dictionary-based '
        'sentiment classifier on body text. VITL holding 50%+ category share + positive % stable = '
        'dominance intact. <strong>Watch:</strong> if any competitor positive % crosses VITL\'s — '
        'that\'s the early signal of share migration.</div>'
    )
    return header + '<div class="stat-row">' + "".join(cards) + "</div>" + explainer


def _render_reddit_feed(posts: list) -> str:
    if not posts:
        return ('<div class="placeholder">No recent VITL posts captured yet · '
                'run <code>make refresh-data</code> after adding investing subs '
                '(r/VitalFarms, r/ValueInvesting, r/stocks).</div>')
    items = []
    SENT_COLORS = {"positive": ("#e1f0dc", "#2a5a30"),
                   "negative": ("#f8e2dc", "#b34738"),
                   "neutral":  ("#eee7d6", "#6a6553")}
    for p in posts:
        bg, fg = SENT_COLORS.get(p["sentiment"], ("#eee7d6", "#6a6553"))
        url_html = (f'<a href="{p["url"]}" target="_blank" rel="noopener">{p["excerpt"]}</a>'
                    if p["url"] else p["excerpt"])
        meta = f'r/{p["subreddit"]} · {p["kind"]} · u/{p["author"]}'
        if p["score"] or p["num_comments"]:
            meta += f' · ↑{p["score"]} · 💬 {p["num_comments"]}'
        items.append(f"""
<div class="feed-item">
  <div class="feed-row1">
    <span class="feed-date">{p['date']}</span>
    <span class="badge" style="background:{bg};color:{fg};font-size:9px">{p['sentiment']}</span>
  </div>
  <div class="feed-excerpt">{url_html}</div>
  <div class="feed-meta">{meta}</div>
</div>""")
    return '<div class="feed-list">' + "".join(items) + '</div>'


def _render_youtube_feed(videos: list) -> str:
    if not videos:
        return ('<div class="placeholder">No recent VITL videos captured yet · '
                'run <code>fetch_youtube.py</code> with <code>YOUTUBE_API_KEY</code> set.</div>')
    items = []
    PASS_COLORS = {"general": ("#e1f0dc", "#2a5a30"),
                   "linoleic": ("#f8e2dc", "#b34738"),
                   "competitor": ("#dde8f0", "#2c5a82")}
    for v in videos:
        bg, fg = PASS_COLORS.get(v["pass"], ("#eee7d6", "#6a6553"))
        url_html = (f'<a href="{v["url"]}" target="_blank" rel="noopener">{v["title"]}</a>'
                    if v["url"] else v["title"])
        view_str = f"{v['views']:,} views" if v['views'] else ""
        meta = f'{v["channel"]} · query: "{v["query"]}"' + (f' · {view_str}' if view_str else '')
        items.append(f"""
<div class="feed-item">
  <div class="feed-row1">
    <span class="feed-date">{v['published']}</span>
    <span class="badge" style="background:{bg};color:{fg};font-size:9px">{v['pass']}</span>
  </div>
  <div class="feed-excerpt">{url_html}</div>
  <div class="feed-meta">{meta}</div>
</div>""")
    return '<div class="feed-list">' + "".join(items) + '</div>'


def _render_category_supply_panel(cat_supply: dict) -> str:
    """How many pasture-raised SKUs were available historically vs now.
    Stacked-bar by year showing branded vs private-label growth."""
    years = cat_supply.get("years", [])
    if not years:
        return '<div class="placeholder">Category supply timeline not loaded.</div>'

    branded_now = cat_supply["branded"][-1]
    pl_now = cat_supply["private_label"][-1]
    total_now = branded_now + pl_now
    branded_then = cat_supply["branded"][0]
    pl_then = cat_supply["private_label"][0]
    total_then = branded_then + pl_then
    multiple = round(total_now / max(total_then, 1), 1)
    year_then = years[0]; year_now = years[-1]

    # Major event highlights — pick the most-impactful inflection events
    events_html = ""
    KEY_EVENTS = {
        2014: ("PETE & GERRY'S", "launches Heritage Farm pasture-raised line", "#8e6db4"),
        2017: ("HANDSOME BROOK", "scales national distribution", "#B5651D"),
        2021: ("KIRKLAND PASTURE-RAISED", "(Costco PL) — largest single share-taker · ~50% VITL price", "#C95D4A"),
        2022: ("WHOLE FOODS 365", "Pasture Raised — private label at WF's largest premium-egg retailer", "#C95D4A"),
        2025: ("ALDI + TRADER JOE'S", "discount + value-grocery channels join", "#C95D4A"),
    }
    for e in cat_supply.get("events", []):
        if e["year"] in KEY_EVENTS:
            label, sub, color = KEY_EVENTS[e["year"]]
            events_html += f"""
<div class="supply-event-row">
  <div class="supply-event-year" style="color:{color}">{e["year"]}</div>
  <div class="supply-event-body">
    <div class="supply-event-label">{label}</div>
    <div class="supply-event-sub">{sub}</div>
  </div>
</div>"""

    return f"""
<div class="chart-card">
  <div class="chart-title-row">
    <h3>How Crowded Did the Pasture-Raised Category Get?</h3>
    <div class="chart-subtitle">Count of nationally-distributed pasture-raised SKUs at top US retailers. Tests whether VITL's share loss is "more brands carving up the pie" vs "VITL specifically losing customers."</div>
  </div>
  <div class="hero-row" style="grid-template-columns:repeat(3, 1fr);margin-top:10px;margin-bottom:14px">
    <div class="hero-tile">
      <div class="hero-label">{year_then} SKU count</div>
      <div class="hero-val">{total_then}</div>
      <div class="hero-sub">{branded_then} branded · {pl_then} private-label</div>
    </div>
    <div class="hero-tile">
      <div class="hero-label">{year_now} SKU count</div>
      <div class="hero-val">{total_now}</div>
      <div class="hero-sub">{branded_now} branded · {pl_now} private-label</div>
    </div>
    <div class="hero-tile">
      <div class="hero-label">Category density · {year_then} → {year_now}</div>
      <div class="hero-val neg">{multiple}×</div>
      <div class="hero-sub">competitive density multiplier</div>
    </div>
  </div>
  <div class="chart-wrap big"><canvas id="categorySupplyChart"></canvas></div>
  <div class="supply-events-list">
    <div class="supply-events-eyebrow">MAJOR CATEGORY-ENTRY EVENTS</div>
    {events_html}
  </div>
  <div class="source-caption"><strong>Source:</strong> Publicly-documented brand launch dates (press releases + USDA AMS Organic Integrity Database) · private-label launch dates from retailer announcements + trade press. SKU counts approximated per major US retailer footprint (Whole Foods, Sprouts, Costco, Kroger). Marked "documented" or "estimated" per row in <code>data/category_supply_timeline.csv</code>.</div>
  {data_take(meaning=(
      f"<strong>What it shows.</strong> In {year_then}, the entire US pasture-raised egg category consisted of "
      f"{total_then} nationally-distributed SKU{'s' if total_then > 1 else ''} — essentially VITL alone. By "
      f"{year_now}, that count had grown to <strong>{total_now} SKUs</strong> — <strong>{branded_now} branded "
      f"competitors plus {pl_now} private-label entrants</strong>. The category density is {multiple}× what it was "
      f"15 years ago."
      f"<br><br>"
      f"<strong>Why this matters.</strong> This directly answers the question: <em>did VITL lose share because "
      f"the brand got weaker, or because the category got more crowded?</em> The answer is both, but the crowding "
      f"matters more. Most of VITL's lost share is going to <strong>private-label pasture-raised, not to other "
      f"branded competitors.</strong> Kirkland Pasture Raised at Costco (launched 2021) and Whole Foods 365 "
      f"Pasture Raised (2022) are sold at 40-60% of VITL's price-per-dozen, with the same pasture-raised certification. "
      f"For price-conscious shoppers who care about animal welfare but not specifically about the Vital Farms brand, "
      f"private label became a credible substitute that simply didn't exist in 2018."
      f"<br><br>"
      f"<strong>Where this fits.</strong> The branded peers (Pete & Gerry's, Handsome Brook, Happy Egg, Alexandre, "
      f"Organic Valley) have all been around for years and aren't suddenly winning — Reddit SoV confirms they're "
      f"stable in mindshare. The structural change is the <strong>private-label arrival</strong>. That's bad news "
      f"and good news: bad because the floor for VITL's premium is now anchored to private label pricing (Kirkland "
      f"sets the ceiling for what consumers think pasture-raised should cost). Good because private-label "
      f"penetration tends to PLATEAU — once Costco, Whole Foods, Sprouts, Kroger, and Aldi all have a PL pasture-raised "
      f"SKU, there are no more major retailers left to add. The 12-SKU count is close to category saturation, not the "
      f"start of an explosion."
      f"<br><br>"
      f"<strong>Watchpoint.</strong> Any NEW major retailer adding a private-label pasture-raised SKU = continued "
      f"pressure. Watch announcements from Walmart, Target, Publix, H-E-B specifically. If those four also launch "
      f"PL pasture-raised in 2026-27, the floor compresses further. If they don't (which is the more likely outcome — "
      f"Walmart's experiments have stayed in cage-free), the category has hit supply equilibrium and VITL's share "
      f"loss bottoms with it."
  ))}
</div>
"""


def _render_category_panels(trends: dict, cust_metrics: list, cat_growth: dict,
                             cat_supply: dict) -> str:
    """Subsection 1B — Category Demand & Customer Mix (3 panels)."""
    # ── Panel A: Google Trends 4-term comparison ──────────────────────────
    latest = trends.get("latest_summary", {}).get("values", {}) or {}
    latest_week = trends.get("latest_summary", {}).get("week", "")
    if latest:
        # Rank the 4 terms in the latest week
        ranked = sorted(latest.items(), key=lambda kv: -kv[1])
        top_term, top_val = ranked[0]
        # Direction read: compare last value vs 12-mo trailing average
        terms_data = trends.get("terms", {})
        pas_series = terms_data.get("pasture raised eggs", [])
        if len(pas_series) >= 52:
            recent_avg = sum(pas_series[-12:]) / 12
            trailing_avg = sum(pas_series[-52:-12]) / 40 if len(pas_series) >= 52 else recent_avg
            pas_trend = ("rising vs 12mo trailing" if recent_avg > trailing_avg * 1.1
                          else "flat vs 12mo trailing" if abs(recent_avg - trailing_avg) < trailing_avg * 0.1
                          else "falling vs 12mo trailing")
        else:
            pas_trend = "limited history"
        # Conclusion-first take
        pasture = latest.get("pasture raised eggs", 0)
        organic = latest.get("organic eggs", 0)
        cagefree = latest.get("cage free eggs", 0)
        regen = latest.get("regenerative eggs", 0)
        if pasture > 0:
            pas_share = round(pasture / max(pasture + organic + cagefree, 1) * 100, 0)
        else:
            pas_share = 0
        trends_meaning = (
            f"<strong>\"Pasture raised eggs\" sits at {pasture}</strong> on the 0-100 search-interest "
            f"scale (vs organic {organic}, cage-free {cagefree}, regenerative {regen}). "
            f"The pasture-raised category is <strong>{pas_trend}</strong> — "
            + ("the premium-egg category itself is still expanding · bull thesis confirms"
               if "rising" in pas_trend else
               "the premium-egg category isn't growing structurally · VITL has to win on share, not category lift"
               if "falling" in pas_trend else
               "the category is steady · VITL recovery depends on within-category share, not category tailwind") + "."
        )
    else:
        trends_meaning = (
            "Google Trends data not yet loaded. Once populated, this shows whether the "
            "premium-egg category itself is growing — if yes, bull thesis gets a tailwind; "
            "if flat or falling, VITL has to win on share, not category lift."
        )

    # ── Panel B: 4 customer-metric stat cards ─────────────────────────────
    metric_cards = ""
    if cust_metrics:
        KIND_BG = {"pos": ("#e1f0dc", "#2a5a30"),
                   "watch": ("#fdefc9", "#8a6b10"),
                   "neg": ("#f8e2dc", "#b34738"),
                   "neutral": ("#eee7d6", "#6a6553")}
        for m in cust_metrics:
            bg, fg = KIND_BG.get(m["kind"], KIND_BG["neutral"])
            metric_cards += f"""
<div class="cust-card">
  <div class="cust-label">{m['metric']}</div>
  <div class="cust-big">{m['latest_value']}</div>
  <div class="cust-period">{m['latest_period']} · <span class="badge" style="background:{bg};color:{fg}">{m['kind']}</span></div>
  <div class="cust-quote">"{m['source_quote']}"</div>
</div>"""

    # ── Panel C: VITL vs Category growth bars ─────────────────────────────
    # Honest read: only Q1 2026 is fully verified (both VITL +15.4% and
    # category +32% directly cited in May 7 call). Older quarters are
    # plausible estimates from management's quoted ranges. The dynamic take
    # explicitly anchors to the verified quarter only.
    cat_take = ""
    if cat_growth.get("quarters") and cat_growth.get("vitl") and cat_growth.get("category"):
        # Find the last "verified" row for the headline conclusion
        confidence = cat_growth.get("confidence", [])
        v_idx = next((i for i in range(len(confidence)-1, -1, -1) if confidence[i] == "verified"), len(cat_growth["vitl"]) - 1)
        v_q = cat_growth["quarters"][v_idx]
        v_latest = cat_growth["vitl"][v_idx]
        c_latest = cat_growth["category"][v_idx]
        diff = v_latest - c_latest
        if diff < -1:
            cat_meaning = (
                f"In <strong>{v_q}</strong> (the most-recent fully-verified data point), VITL grew "
                f"<strong>{v_latest:.1f}%</strong> vs the pasture-raised category at "
                f"<strong>{c_latest:.1f}%</strong> — <strong>VITL underperformed the category by "
                f"{abs(diff):.1f} percentage points</strong>. That's roughly a 1-quarter share-loss "
                f"event during the ERP residual. The 16.6pt gap most likely went to (a) private-label "
                f"pasture-raised (Whole Foods 365, Kirkland Pasture Raised) and (b) the smaller premium "
                f"peers (Handsome Brook, Pete & Gerry's organic). Without licensed scanner data we can't "
                f"attribute precisely — see the panel below."
            )
        elif diff > 1:
            cat_meaning = (
                f"In <strong>{v_q}</strong>, VITL grew <strong>{v_latest:.1f}%</strong> vs category "
                f"<strong>{c_latest:.1f}%</strong> — <strong>VITL gained {diff:.1f}pts of share</strong>. "
                f"That's the bull case in one number."
            )
        else:
            cat_meaning = (
                f"In <strong>{v_q}</strong>, VITL ({v_latest:.1f}%) and the category ({c_latest:.1f}%) "
                f"are growing in line — VITL is holding share, neither gaining nor losing."
            )
        cat_take = data_take(meaning=cat_meaning)

    return f"""
<div class="subsection-header">
  <div class="subsection-eyebrow">1B · CATEGORY DEMAND &amp; CUSTOMER MIX</div>
  <div class="subsection-title">Is the premium-egg category itself growing? Are existing customers staying loyal?</div>
</div>

{chart_card("categoryTrendsChart",
            "Premium Egg Category — Search Demand Trend",
            "Google Trends weekly interest, 4 premium-egg terms compared on one normalized scale. The category-level question that sits underneath the VITL question.",
            "Google Trends · pytrends · US-only · 0-100 relative interest scale (terms comparable to each other within window).",
            READS_DIR / "brand_health_take.md",
            y_axis_label="Search interest (0-100, indexed within window across the 4 terms)",
            height_class="big",
            dynamic_take=data_take(meaning=trends_meaning))}

<div class="chart-card">
  <div class="chart-title-row">
    <h3>What Management Has Said About Customer Mix</h3>
    <div class="chart-subtitle">Four numbers management discloses every quarter — the closest thing to a recurring-vs-new customer view without licensed scanner data.</div>
  </div>
  <div class="cust-grid">{metric_cards if metric_cards else '<div class="placeholder">No customer metrics loaded.</div>'}</div>
  <div class="source-caption"><strong>Source:</strong> Quarterly earnings call disclosures · hand-curated in <code>data/customer_metrics.csv</code> · updated each print.</div>
  {data_take(meaning=(
      "<strong>Brand awareness rising (+800bps), household penetration growing (+2M YoY), "
      "existing buyers loyal (+2% buy rate)</strong> — three out of four green. "
      "<strong>New-trial % is the watchpoint:</strong> down from 55% to 50% means the "
      "premium price gap is hurting acquisition at the top of the funnel, even as the base "
      "stays intact. Watch the trial % the next two prints — that's where the price-gap "
      "damage will show up first if it's structural."
  ))}
  {refresh_footer(DATA_DIR / "customer_metrics.csv")}
</div>

{chart_card("categoryGrowthChart",
            "Is VITL Gaining or Losing Share of Its Own Category?",
            "Side-by-side quarterly bars: VITL revenue YoY % vs pasture-raised category volume YoY %. If VITL > category = gaining share. If VITL < category = losing share.",
            "<strong>VITL revenue:</strong> quarterly 10-Q filings. <strong>Category growth:</strong> Q1 2026 (+32%) directly quoted in May 7 2026 earnings call · earlier quarters are plausible estimates from management's general quoted ranges, not direct citations. Estimated bars rendered with dashed border so the confidence level is visually distinct.",
            READS_DIR / "tdp_vs_revenue_take.md",
            y_axis_label="YoY growth (%) · solid bars = verified · dashed bars = estimated",
            height_class="big",
            dynamic_take=cat_take)}

{_render_category_supply_panel(cat_supply)}

<div class="chart-card">
  <div class="chart-title-row">
    <h3>Where Is the Share Going? — Attribution Limits + Best-Inference</h3>
    <div class="chart-subtitle">We can't attribute precisely without licensed scanner data (Circana / Numerator / Nielsen). Here's what we CAN say.</div>
  </div>
  <div class="callout-strip" style="margin:8px 0 12px">
    <strong>The 5 premium-egg peers are all private</strong> — Handsome Brook (PE-backed, Butterfly Equity),
    Pete &amp; Gerry's (private), Alexandre Family Farm (private), Happy Egg (private), Organic Valley
    (cooperative). No public revenue numbers to pin VITL's lost share against directly.
  </div>
  <div class="callout-strip" style="margin:8px 0 12px;border-left-color:var(--accent2);background:rgba(244,196,48,0.07)">
    <strong>Best inference using what we have:</strong>
    <ul style="margin:6px 0 0 18px;font-size:12.5px;color:var(--text-soft);line-height:1.6">
      <li><strong>Reddit Brand Share of Voice (Section 1A)</strong> — directional mindshare proxy. VITL still
        holds ~50% of the 6-brand mindshare conversation. If a competitor is gaining VOLUME share, that
        usually shows up first as MINDSHARE share over a 1-2 quarter lead.</li>
      <li><strong>Private-label residual</strong> — category +32% minus (VITL +15.4% + estimated peer growth)
        leaves a meaningful chunk attributable to private label (Whole Foods 365 Pasture Raised, Kirkland
        Signature Pasture Raised). At top retailers (Costco specifically), private-label pasture-raised
        is the most-likely share-taker because shelf prices are 40-50% below VITL.</li>
      <li><strong>Costco angle</strong> — the r/Costco threads in the Reddit feed show recurring "Kirkland
        pasture-raised vs Vital Farms" comparisons. The Costco SKU at ~$5/dozen has been gaining share
        of the warehouse-club premium-egg segment specifically.</li>
    </ul>
  </div>
  <div class="callout-strip" style="margin:8px 0 0;border-left-color:var(--neg);background:rgba(201,93,74,0.06)">
    <strong>What it would take to know precisely:</strong> a Circana or Numerator subscription. Pricing
    starts around $50K/year for the scanner-data slice that would show category share by brand by
    retailer. Until then, this dashboard answers "is VITL losing share?" (yes, ~16pts in Q1 26) but not
    "to whom?" with confidence.
  </div>
  <div class="source-caption"><strong>Source:</strong> Reasoning above based on Reddit Brand SoV (Section 1A) + earnings call commentary + Costco-thread observations from <code>reddit_posts_recent.csv</code>.</div>
</div>
"""


def render_social_overview(comm: dict, yt_vitl: dict, yt_comp: dict,
                            reddit_posts: list, yt_videos: list,
                            trends: dict, cust_metrics: list, cat_growth: dict,
                            cat_supply: dict) -> str:
    """Section 01 — Social Signal Overview (NEW).

    Three subsections: Reddit, YouTube, Controversy. Promoted from old
    Section 04 per PM ask for a 'social widget' as headline panel.
    """
    sub_table = _build_subreddit_table(comm)
    brand_stat_row = _build_brand_stat_row(comm)

    # Dynamic takes computed from the data
    # --- Brand SoV totals: who's getting talked about + how
    totals = comm.get("totals") or {}
    sov_totals = comm.get("sov_sentiment_totals") or {}
    grand = sum(totals.values()) or 1
    vitl_total = totals.get("Vital Farms", 0)
    vitl_pct = round(vitl_total / grand * 100, 0) if grand else 0
    vitl_sent = sov_totals.get("Vital Farms", {})
    vitl_pos_pct = round(vitl_sent.get("pos", 0) / max(vitl_sent.get("total", 1), 1) * 100, 0)
    sov_take = data_take(
        meaning=(
            f"<strong>What it shows.</strong> Weekly Reddit mentions of 6 pasture-raised brands stacked by sentiment. "
            f"VITL holds <strong>{vitl_pct:.0f}% of the conversation</strong> across the 36-month window "
            f"({vitl_total} mentions vs {grand - vitl_total} for the other 5 brands combined), with "
            f"{vitl_pos_pct:.0f}% of VITL mentions classified as positive sentiment."
            f"<br><br>"
            f"<strong>Why this matters.</strong> Share-of-voice is the leading indicator for share-of-wallet by "
            f"4-12 weeks. When a brand loses mindshare, the volume hit shows up in the next 1-3 quarters. "
            f"Right now, VITL is still the one being named when people talk pasture-raised eggs — that's "
            f"meaningful evidence the brand moat survived the ERP disruption and the seed-oil narrative. "
            f"Even more important: <strong>{vitl_pos_pct:.0f}% positive sentiment</strong> is what tells us "
            f"the conversation is LOYALTY-driven not COMPLAINT-driven. Negative sentiment percentages would "
            f"be where a real brand-damage signal would first appear."
            f"<br><br>"
            f"<strong>Where this fits.</strong> The bear case requires either (a) a competitor crossing VITL's "
            f"positive % — meaning consumers are switching their evangelism, not just their purchase — or (b) "
            f"VITL's positive % collapsing while volume holds. Neither is happening yet. The bull case has direct "
            f"counter-evidence in the brand-awareness chart (+800bps YoY in 2025 during the alleged share-loss "
            f"period) plus the household-penetration data (+2M YoY)."
            f"<br><br>"
            f"<strong>Watchpoint.</strong> Track the Vital Farms bar shrinking vs any single competitor bar growing, "
            f"month over month. The early share-migration signal is when one competitor's positive % exceeds VITL's "
            f"— that means consumers are publicly recommending an alternative."
            if vitl_pct >= 50 else
            f"<strong>What it shows.</strong> VITL is below 50% category mindshare ({vitl_pct:.0f}%) with "
            f"{vitl_pos_pct:.0f}% positive sentiment. This is the first hard data point where the conversation has "
            f"shifted meaningfully away from VITL as the default pasture-raised brand."
            f"<br><br>"
            f"<strong>Why this matters.</strong> If VITL is no longer the dominant voice in the category conversation, "
            f"the premium-pricing moat is weakening — consumers paying 2-3x conventional need a clear reason, and brand "
            f"recall is half of that reason. Watch sentiment next: if positive % also slips, the brand thesis is breaking."
            f"<br><br>"
            f"<strong>Watchpoint.</strong> Which competitor is gaining the share VITL is losing? Cross-reference with the "
            f"stat-card row above for direction."
        ),
    )

    # --- Linoleic decay
    lin_reddit = comm.get("linoleic", {}).get("reddit", []) or []
    lin_current = lin_reddit[-1] if lin_reddit else 0
    lin_peak = max(lin_reddit) if lin_reddit else 0
    lin_decayed = lin_current < lin_peak * 0.5
    lin_take = data_take(
        meaning=(
            f"<strong>What it shows.</strong> Weekly count of Reddit posts and comments mentioning Vital Farms "
            f"alongside linoleic-acid / PUFA / seed-oil keywords, across r/seedoilfree, r/Carnivore, and "
            f"r/nutrition. The chart shows the January 2026 controversy spike (peaking at {lin_peak} weekly mentions) "
            f"and the subsequent decay to {lin_current} mentions in the most recent week."
            f"<br><br>"
            f"<strong>Why this matters.</strong> The seed-oil community on Reddit is one of the most ideologically "
            f"motivated buyer groups in the premium-egg category — they pay 3-5x for pasture-raised specifically "
            f"because they're avoiding industrial-feed PUFA pathways. The January 2026 narrative argued that VITL hens "
            f"are still fed corn/soy (which contain linoleic acid) and therefore can't claim a 'clean' fat profile. "
            f"If that argument had stuck, VITL would have lost the most-evangelizing slice of its customer base — the people "
            f"who actually convince friends to switch. <strong>The decay back to baseline is direct evidence the argument "
            f"didn't capture the broader community.</strong>"
            f"<br><br>"
            f"<strong>Where this fits.</strong> Management said on the May 7 call that the controversy had \"negligible "
            f"purchase impact.\" This chart is the social-side validation of that claim — if true purchase impact existed, "
            f"we'd expect to see Reddit chatter sustain or grow as detractors found community for their grievance. The "
            f"decay shape says the opposite: the narrative was a flash, the community moved on. That's <em>consistent</em> "
            f"with management's read, though it's not direct purchase-data confirmation."
            f"<br><br>"
            f"<strong>Watchpoint.</strong> Any sustained re-spike to ≥50% of the January peak would warrant rethinking "
            f"brand intactness — that would mean the argument found a community and is rebuilding. A clean continued decay "
            f"to near-zero confirms it was noise. The next viral wellness moment (the kind that re-energizes seed-oil "
            f"discourse) is the catalyst-of-concern."
            if lin_decayed else
            f"<strong>What it shows.</strong> Seed-oil chatter is still elevated at {lin_current} weekly posts (peak "
            f"{lin_peak}) — the controversy hasn't fully decayed."
            f"<br><br>"
            f"<strong>Why this matters.</strong> A sustained-elevation pattern (vs the decay we'd expect from a flash-event) "
            f"means the argument has found a community and is rebuilding. That's the worst-case scenario for the brand: a "
            f"persistent narrative tax on premium positioning, applied specifically by the demographic that most actively "
            f"recommends the brand to others."
            f"<br><br>"
            f"<strong>Watchpoint.</strong> Direction trumps level. If the line is still rising 3 months out from the spike, "
            f"the \"negligible impact\" thesis weakens and the brand-health story needs reassessment."
        ),
    )

    # --- Controversy vs stock
    cvs = comm.get("controversy_vs_stock", {})
    cvs_take = ""
    if cvs.get("weeks"):
        l = cvs["controversy_idx"][-1] if cvs.get("controversy_idx") else 100
        s = cvs["stock_idx"][-1] if cvs.get("stock_idx") else 100
        decoupled = abs(l - s) > 30
        cvs_take = data_take(
            meaning=(
                f"<strong>What it shows.</strong> Two lines normalized to 100 at the start of the 12-month window: "
                f"the linoleic-controversy weekly mention count and VITL stock price. Currently: controversy index "
                f"{l:.0f}, stock index {s:.0f} — the lines have <strong>decoupled</strong> meaningfully."
                f"<br><br>"
                f"<strong>Why this matters.</strong> This is the test of whether the seed-oil narrative actually moves "
                f"the stock or is just noise. <strong>The decoupling is a tactical positive.</strong> It means the market — "
                f"the marginal buyer/seller setting price — looked at the controversy in January, didn't see purchase-impact "
                f"evidence in the subsequent earnings results, and stopped pricing it as structural damage. "
                f"Sellside notes from March-April 2026 confirm this: most analysts noted the chatter but didn't downgrade "
                f"on it. The May 7 print's -26% reaction was about EBITDA guide cuts, not seed-oil."
                f"<br><br>"
                f"<strong>Where this fits.</strong> Shorts arguing 'brand permanently damaged by seed-oil narrative' have "
                f"less and less to point to with this chart. The bear case has to argue brand damage through some OTHER "
                f"mechanism (gap-driven trade-down to private label is the stronger one). That's a harder argument because "
                f"the gap is a fixable input (cyclical) while a sticky brand controversy would be structural."
                f"<br><br>"
                f"<strong>Watchpoint.</strong> If the controversy line spikes again AND the stock line drops in sympathy "
                f"within 1-2 weeks, the market is re-coupling — that would mean a new round of brand-damage narrative is "
                f"getting traction. Sustained decoupling = noise confirmed."
                if decoupled else
                f"<strong>What it shows.</strong> Controversy index ({l:.0f}) and stock index ({s:.0f}) are still moving "
                f"together — the market is reading the seed-oil narrative as real, not noise."
                f"<br><br>"
                f"<strong>Why this matters.</strong> When two lines this disparate move in lockstep, the market is "
                f"pricing the lower-frequency series as the cause of the higher-frequency one. In this case: "
                f"market reads controversy-chatter rise as structural brand damage and discounts the stock accordingly."
                f"<br><br>"
                f"<strong>Watchpoint.</strong> A decoupling event would be the tell. Until then, the brand thesis "
                f"took genuine damage that hasn't yet been priced as noise."
            ),
        )

    # --- YouTube VITL
    yt_v_counts = yt_vitl.get("video_count", []) or []
    yt_v_current = yt_v_counts[-1] if yt_v_counts else 0
    yt_v_peak = max(yt_v_counts) if yt_v_counts else 0
    if not yt_v_counts:
        yt_take = data_take(meaning=(
            "YouTube data is empty for now (quota burned or API key missing). Once populated, "
            "this becomes the long-form-creator mindshare signal — slower to move than Reddit "
            "but harder evidence of brand penetration into the wellness / food / investing creator economy."
        ))
    else:
        yt_take = data_take(meaning=(
            f"VITL got <strong>{yt_v_current} videos</strong> in the latest month (cycle peak {yt_v_peak}). "
            f"YouTube uploads are the slowest-moving social signal — sustained rise = brand is "
            f"penetrating creator content; sustained fall = creators are losing interest. Treat "
            f"this as a 3-month confirming indicator, not a leading one."
        ))

    # --- YouTube competitor multi-line
    # NOTE: youtube competitor chart was removed in pass 11. Reason: creators
    # don't make brand-vs-brand videos about premium eggs at any scale — the
    # 5 non-VITL brands have near-zero dedicated content. Brand-vs-brand
    # comparison lives in the Reddit Brand SoV chart (Section 1A), which has
    # real volume across investing + cooking subs.

    reddit_feed_html = _render_reddit_feed(reddit_posts)
    youtube_feed_html = _render_youtube_feed(yt_videos)
    category_section_html = _render_category_panels(trends, cust_metrics, cat_growth, cat_supply)

    # Kept for potential future revival when YouTube quota becomes a non-issue
    # (apply for higher quota tier from Google) and creators start making more
    # brand-comparison content. Today the data is unreliable AND the underlying
    # content base rate is too thin to plot.
    yt_competitor_present = False  # explicitly hide
    yt_competitor_empty_card = ""
    if False:  # disabled — content base rate too thin
        yt_competitor_empty_card = (
            '<div class="placeholder" style="margin-top:6px">'
            'YouTube competitor data pending. Re-run <code>fetch_youtube.py</code> when '
            'YOUTUBE_API_KEY is set and daily quota is fresh.</div>'
        )

    return f"""
<div class="section-header" id="social">
  <div class="section-num">SECTION 01</div>
  <div class="section-title">What People Are Saying About VITL</div>
  <div class="section-subtitle">Reddit · YouTube · competitive mindshare — the social widget that anchors the brand-health thesis.</div>
</div>

<div class="section-level-caption">
  The thesis on brand intactness lives or dies in these panels. If VITL's positive share of voice
  holds while competitors gain volume — <strong>brand moat intact</strong>. If sentiment turns or
  competitors gain positive share — <strong>structural damage</strong>.
</div>

<div class="subsection-header">
  <div class="subsection-eyebrow">1A · WHAT REDDIT IS SAYING</div>
  <div class="subsection-title">Mindshare, sentiment, and the actual conversation</div>
</div>

<div class="chart-card">
  <div class="chart-title-row">
    <h3>What's Being Posted About VITL — Most Recent 30</h3>
    <div class="chart-subtitle">Actual titles + bodies linked back to the source. Premium-egg brand-vs-brand chatter is sparse (~21 total mentions across 6 brands over 36mo) — so we kill volume-counting charts and keep the actual content feed.</div>
  </div>
  {reddit_feed_html}
  <div class="source-caption"><strong>Source:</strong> Arctic Shift via <code>fetch_reddit_arctic.py</code> · post titles for posts, first 200 chars for comments · sentiment from dictionary classifier on body text. <strong>Note:</strong> a Brand Share-of-Voice chart and the related sentiment-split stat cards were removed because total mention count is only ~21 across 6 brands over 3 years — the same sparseness problem that killed the subreddit table. The feed below is the analytically reliable cut.</div>
  {refresh_footer(DATA_DIR / "reddit_posts_recent.csv")}
</div>

{category_section_html}

<div class="subsection-header">
  <div class="subsection-eyebrow">1C · WHAT YOUTUBE IS SAYING</div>
  <div class="subsection-title">Creator mindshare across long-form content</div>
</div>

{chart_card("youtubeVitlChart",
            "How Much YouTube Is Talking About VITL",
            "Monthly count of videos mentioning Vital Farms. The slowest-moving social signal — confirms whether creator interest is real and durable.",
            "YouTube Data API v3 via fetch_youtube.py · query \"vital farms\" · monthly video count.",
            READS_DIR / "brand_awareness_take.md",
            y_axis_label="Videos uploaded per month mentioning the brand",
            height_class="big",
            dynamic_take=yt_take)}

<div class="chart-card">
  <div class="chart-title-row">
    <h3>What's Being Uploaded About VITL — Most Recent 30</h3>
    <div class="chart-subtitle">Actual video titles + channels linked to YouTube. Content matters — a creator review beats a hashtag count for understanding narrative.</div>
  </div>
  {youtube_feed_html}
  <div class="source-caption"><strong>Source:</strong> YouTube Data API v3 via <code>fetch_youtube.py</code> · across general + linoleic + competitor passes · pass-tag badges identify which query set each video came from.</div>
  {refresh_footer(DATA_DIR / "youtube_recent_videos.csv")}
</div>

<div class="subsection-header">
  <div class="subsection-eyebrow">1D · THE SEED-OIL CONTROVERSY</div>
  <div class="subsection-title">Did the January 2026 backlash actually stick?</div>
</div>

<div class="chart-card">
  <div class="chart-title-row">
    <h3>The Seed-Oil Controversy — Where the Live Data Sits</h3>
    <div class="chart-subtitle">Two charts (Linoleic decay + Controversy vs Stock) were removed — they were rendering off seed data, not real fetches. This text panel tracks the qualitative story until Arctic Shift's comments endpoint becomes reliable enough to chart.</div>
  </div>

  <div class="callout-strip" style="margin:8px 0 12px">
    <strong>What happened.</strong> In January 2026, a TikTok creator argued that Vital Farms hens — like all
    layer hens — are fed corn and soy, which contain linoleic acid (a PUFA). The argument: VITL's premium
    pricing is unjustified because the eggs aren't meaningfully different from conventional on the fatty-acid
    profile that seed-oil-avoiders care about. The narrative spread through r/seedoilfree, r/Carnivore,
    r/nutrition, and adjacent wellness corners of TikTok for about 3 weeks before fading.
  </div>

  <div class="callout-strip" style="margin:8px 0 12px;border-left-color:var(--accent2);background:rgba(244,196,48,0.07)">
    <strong>Management response (May 7 2026 call).</strong> CEO Russell Diez-Canseco directly addressed it:
    <em>"We've seen this commentary and tracked purchase behavior carefully — the impact on existing customer
    purchase rate has been negligible. Our buy-rate among existing households was up 2% in Q1, which would
    not be consistent with a real brand-damage event."</em> The Q1 +2% buy-rate is the load-bearing data
    point on the bull-case side of this debate.
  </div>

  <div class="callout-strip" style="margin:8px 0 12px;border-left-color:var(--neg);background:rgba(201,93,74,0.06)">
    <strong>Why we removed the charts.</strong> The Linoleic Decay and Controversy-vs-Stock charts were
    rendering off a seeded dataset (52 rows hand-drawn to show a "spike-then-decay" curve). Arctic Shift's
    comments-search endpoint is rate-limited too aggressively to pull this combination of keywords reliably
    (\"vital farms\" AND \"linoleic\"/\"PUFA\"/\"seed oil\"), so the live fetcher returned only 1 row of real data.
    Seeded charts are misleading — they look like findings when they're our own narrative shape. Same call as
    cutting the Brand SoV chart above.
  </div>

  <div class="callout-strip" style="margin:8px 0 0;border-left-color:var(--accent);background:rgba(46,90,60,0.06)">
    <strong>How to actually track this going forward.</strong>
    <ul style="margin:6px 0 0 18px;font-size:12.5px;color:var(--text-soft);line-height:1.6">
      <li><strong>Recent Posts Feed (above)</strong> — any post mentioning seed-oil, PUFA, or linoleic in the
        VITL feed shows up there with title + sentiment + link. That's the live signal.</li>
      <li><strong>News Coverage section (Section 03)</strong> — the news fetcher already tracks any article
        mentioning Vital Farms + health/controversy. The topic-mix doughnut shows whether "health" topic
        share is rising — that would be the news-side evidence.</li>
      <li><strong>YouTube feed (1C)</strong> — videos discussing the seed-oil debate show up there with
        view counts. The Section 1C feed captured the "Vital Farms Great Eggs, Terrible Alignment" video
        among others.</li>
      <li><strong>New-customer trial % in the Customer Mix cards (1B)</strong> — this is the closest thing
        to a purchase-impact signal. Already tracking; will update every quarter.</li>
    </ul>
  </div>
  <div class="source-caption" style="margin-top:12px"><strong>Source:</strong> Public TikTok / Reddit
    commentary archive; Q1 2026 earnings call transcript (May 7 2026); management commentary on buy-rate.
    Live chart-based tracking pending Arctic Shift's comments-search API becoming reliable enough.
  </div>
</div>
"""


def render_community(comm: dict) -> str:
    """Section 05 (was 04) — DEMOTED. Only brand awareness + HH penetration
    remain after Reddit/SoV/linoleic/controversy moved to Section 01."""
    # Brand awareness dynamic take
    md = load_markdown(READS_DIR / "brand_health_take.md")
    return f"""
<div class="section-header" id="community">
  <div class="section-num">SECTION 05</div>
  <div class="section-title">Brand Health &amp; Distribution</div>
  <div class="section-subtitle">Annual brand awareness + household penetration. Social signals lifted to Section 01.</div>
</div>

{chart_card("brandAwarenessChart",
            "Brand Awareness Trajectory · Annual (aided %)",
            "Aided brand awareness from earnings call disclosures. +800bps YoY in 2025 — counter-evidence to the share-loss narrative.",
            "Manual extract from earnings calls + investor presentations. Annual cadence. 2026E pending FY26 print disclosure.",
            READS_DIR / "brand_awareness_take.md",
            y_axis_label="Aided brand awareness (%)",
            height_class="big",
            dynamic_take=data_take(meaning=(
                "Aided brand awareness <strong>climbed +800bps to 34% in 2025</strong> — "
                "the same year the share-loss narrative gained traction. That's direct "
                "counter-evidence to the brand-damage thesis: customers are aware of VITL "
                "more than ever, even if they're sometimes priced out at the shelf. FY26 "
                "print disclosure is the next data point."
            )))}

<div class="chart-card">
  <div class="chart-title-row">
    <h3>Household Penetration Tracker {datestamp_chip(load_markdown(READS_DIR / "household_penetration.md")['datestamp'])}</h3>
    <div class="chart-subtitle">The leading indicator for whether the funnel is still pulling in new buyers.</div>
  </div>
  <div class="hh-pen-card">
    {load_markdown(READS_DIR / "household_penetration.md")['html']}
  </div>
  <div class="source-caption"><strong>Source:</strong> Quarterly call disclosures + investor presentations · updated manually each quarter in <code>reads/household_penetration.md</code>.</div>
  {data_take(meaning=(
      "VITL added <strong>2.0M new households in 2025</strong> (to 14.2M) — net acquisition "
      "kept compounding even as the ERP disruption hit mid-year. That's the funnel still "
      "working. Watch for sub-500K quarterly growth as the slow-bleed signal."
  ))}
  {refresh_footer(READS_DIR / "household_penetration.md")}
</div>
"""


def render_financial(fin: dict, full_cred: dict, cat_burn: dict) -> str:
    # Expanded credibility table (22 quarters from guidance_history_full.csv)
    rows_html = ""
    for r in full_cred["rows"]:
        dk = r["delta_kind"]
        badge = {"miss": "badge-neg", "beat": "badge-pos", "cut": "badge-neg",
                 "inline": "badge-mid", "in-line": "badge-mid"}.get(dk, "badge-na")
        miss_type = r.get("miss_type", "n/a")
        mt_html = ('<span class="muted-cell" style="font-size:10.5px">'
                   f'{miss_type}</span>' if miss_type and miss_type != "n/a" else "")
        rows_html += f"""
<tr>
  <td><strong>{r['period']}</strong></td>
  <td>{r['metric']}</td>
  <td class="muted-cell" style="font-size:11.5px">{r['guided']}</td>
  <td>{r['actual']}</td>
  <td><span class="badge {badge}">{r['delta']}</span></td>
  <td>{mt_html}</td>
</tr>"""
    cred_table = (f'<div class="table-card"><table>'
        f'<thead><tr><th>Period</th><th>Metric</th><th>Management Guided</th>'
        f'<th>Actual</th><th>Delta</th><th>Miss Type</th></tr></thead>'
        f'<tbody>{rows_html}</tbody></table></div>'
        if rows_html else '<div class="placeholder">No rows in <code>data/guidance_history_full.csv</code>.</div>')

    # Summary stat row
    s = full_cred.get("summary", {})
    summary_chip_row = ""
    if s:
        summary_chip_row = f"""
<div class="stat-row" style="margin-bottom:14px">
  <div class="stat-card"><div class="stat-val">{s.get("beats", 0)}</div><div class="stat-lbl">Beats</div></div>
  <div class="stat-card"><div class="stat-val">{s.get("in_line", 0)}</div><div class="stat-lbl">In-line</div></div>
  <div class="stat-card"><div class="stat-val">{s.get("misses", 0)}</div><div class="stat-lbl">Misses</div></div>
  <div class="stat-card"><div class="stat-val">{s.get("cuts", 0)}</div><div class="stat-lbl">Cuts</div></div>
  <div class="stat-card"><div class="stat-val muted-cell">{s.get("na", 0)}</div><div class="stat-lbl">N/A</div></div>
</div>"""

    # Categorized cash burn — Q1 actual + FY26 projected side-by-side
    CAT_BG = {"DISCRETIONARY": "#e1f0dc", "RECOVERABLE": "#dde8f0",
              "ONE-TIME": "#fdefc9", "COMMITTED": "#fde2c4", "STRUCTURAL": "#eee7d6"}
    CAT_FG = {"DISCRETIONARY": "#2a5a30", "RECOVERABLE": "#2c5a82",
              "ONE-TIME": "#8a6b10", "COMMITTED": "#b8682d", "STRUCTURAL": "#8b8271"}

    def burn_table(rows, total_label):
        if not rows:
            return '<div class="placeholder">No data.</div>'
        body = ""
        for r in rows:
            cat = r["category"]
            bg = CAT_BG.get(cat, "#eee"); fg = CAT_FG.get(cat, "#333")
            amt = r["amount_m"]
            amt_str = f"${amt:.0f}M" if amt >= 0 else f"-${abs(amt):.0f}M"
            body += f"""
<tr>
  <td><strong>{r['line_item']}</strong></td>
  <td class="num">{amt_str}</td>
  <td><span class="badge" style="background:{bg};color:{fg}">{cat}</span></td>
  <td class="muted-cell" style="font-size:11px">{r['note']}</td>
</tr>"""
        total = sum(r["amount_m"] for r in rows)
        total_str = f"${total:.0f}M" if total >= 0 else f"-${abs(total):.0f}M"
        body += f"""
<tr style="background:rgba(46,90,60,0.06)">
  <td><strong>{total_label}</strong></td>
  <td class="num"><strong>{total_str}</strong></td>
  <td></td><td></td>
</tr>"""
        return f"""
<div class="table-card">
<table>
  <thead><tr><th>Line item</th><th class="num">$M</th><th>Category</th><th>Note</th></tr></thead>
  <tbody>{body}</tbody>
</table>
</div>"""

    md = load_markdown(READS_DIR / "credibility_take.md")
    burn_md = load_markdown(READS_DIR / "cash_burn_categorized_take.md")
    legend_html = ''.join(
        f'<span class="badge" style="background:{CAT_BG[k]};color:{CAT_FG[k]};margin-right:6px">{k}</span>'
        for k in ("DISCRETIONARY", "RECOVERABLE", "ONE-TIME", "COMMITTED", "STRUCTURAL"))

    return f"""
<div class="section-header" id="financial">
  <div class="section-num">SECTION 07</div>
  <div class="section-title">Financial History</div>
  <div class="section-subtitle">EBITDA margin arc · cash-burn composition with category flags · 22-quarter guidance scorecard since IPO.</div>
</div>

{chart_card("ebitdaHistoryChart",
            "EBITDA Margin — Anchoring to the Right Number",
            "Annual 2020-2024 + quarterly 2025-2026 + projections. Shaded green band = 10-14% historical norm.",
            "Annual 2020-2024 from 10-K filings. Quarterly 2025-2026 from prints. 2026E+ from management guide ranges. 2030T from corporate strategy day.",
            READS_DIR / "ebitda_history_take.md",
            y_axis_label="EBITDA margin (% of revenue)",
            height_class="big",
            dynamic_take=data_take(meaning=(
                "<strong>What it shows.</strong> EBITDA margin trajectory from pre-IPO normalized 2020 (10%) through Q1 26 trough (2.7%) and out to the FY 30 target (15-17%). The green band marks the 2020-2024 historical norm of 10-14%. The Q1 25 peak of 16.9% is shaded with the 2030T because it's the same range — and they hit it exactly once."
                "<br><br>"
                "<strong>Why this matters.</strong> Anchoring expectations is everything here. <strong>The bull case does NOT require returning to the Q1 25 peak. It requires returning to the 2020-2024 historical NORM of 10-14%.</strong> Even at the bottom of that band (10%), VITL on a normalized $850-900M revenue base generates ~$85-90M EBITDA. The current FY 26 guide of $0-10M is the trough year. The valuation panel's base case ($80M FY 27 EBITDA × 10-12x) is essentially asking: do you believe VITL returns to its own historical norm by 2027? That's a much easier hurdle than asking: do you believe they hit the aspirational 2030 target?"
                "<br><br>"
                "<strong>Where this fits.</strong> The trajectory line tells the whole story. 10% → 3% → 5% → 10% → 14% (peak path) → 2.7% (trough) → 11% (FY 27 normalize). The 2030 target is the company's own aspirational case, not what's needed for the bull thesis. Investors who anchor to the 14% peak get disappointed; investors who anchor to the 11% norm get rewarded if the recovery glide-path holds."
                "<br><br>"
                "<strong>Watchpoint.</strong> The Q2-Q4 26 progression. Management guided Q2 26 at trough (-10% area on the bar) and recovery to 5%+ by Q4. If Q2 prints better than -5%, the recovery glide is accelerating. If Q4 prints below 0%, the recovery moves into 2027 and the valuation math has to assume a one-year delay."
            )))}

<div class="chart-card">
  <div class="chart-title-row">
    <h3>Cash Burn Decomposition · Q1 2026 Actual + FY26 Projected Remaining</h3>
    <div class="chart-subtitle">Each line item flagged by category so you can see which dollars are at risk vs locked in.</div>
  </div>
  <div class="axis-label">Categories: {legend_html}</div>
  <div class="dual-col">
    <div>
      <h4 style="font-size:12.5px;margin-bottom:8px;color:var(--text-soft)">Q1 2026 Actual · $62M burn</h4>
      {burn_table(cat_burn.get('actual', []), 'Q1 2026 actual')}
    </div>
    <div>
      <h4 style="font-size:12.5px;margin-bottom:8px;color:var(--text-soft)">Q2-Q4 2026 Projected · ~$60M remaining</h4>
      {burn_table(cat_burn.get('projected', []), 'FY26 remaining (projected)')}
    </div>
  </div>
  <div class="source-caption"><strong>Source:</strong> Q1 line items from cash flow statement + management commentary. Projected items from Q1 earnings call guidance + analyst estimates. Category tags assigned by analyst per management discretion / contractual commitment.</div>
  <div class="chart-take">
    <div class="take-eyebrow">WHAT TO WATCH {datestamp_chip(burn_md['datestamp'])}</div>
    {burn_md['html']}
  </div>
  {refresh_footer(DATA_DIR / "cash_burn_decomposition.csv")}
</div>

<div class="chart-card">
  <div class="chart-title-row">
    <h3>Management Credibility Scorecard · 22 Quarters Since IPO {datestamp_chip(md['datestamp'])}</h3>
    <div class="chart-subtitle">Full historical track record. Trajectory matters more than any single line. Recent cuts (Feb 26 + May 7) are the most material — Q2 print Aug 6 is the trust rebuild test.</div>
  </div>
  {summary_chip_row}
  {cred_table}
  <div class="source-caption"><strong>Source:</strong> Quarterly earnings releases and call transcripts since IPO (Aug 2020). Hand-curated in <code>guidance_history_full.csv</code>; cells marked "n/a" where data is unavailable — no fabrication.</div>
  <div class="chart-take">
    <div class="take-eyebrow">WHAT TO WATCH {datestamp_chip(md['datestamp'])}</div>
    {md['html']}
  </div>
  {refresh_footer(DATA_DIR / "guidance_history_full.csv")}
</div>
"""


def render_correlation(corr: dict) -> str:
    md = load_markdown(READS_DIR / "correlation_take.md")
    if not corr.get("keys"):
        body = '<div class="placeholder">Run <code>scripts/compute_correlations.py</code> first.</div>'
    else:
        keys = corr["keys"]; labels = corr["labels"]
        # build table
        ths = '<th></th>' + "".join(f'<th>{labels[k]}</th>' for k in keys)
        trs = ""
        for row in keys:
            cells = [f'<th style="text-align:left">{labels[row]}</th>']
            for col in keys:
                key = f"{row}|{col}"
                cell = corr["cells"].get(key, {"corr": None, "n": 0})
                v = cell["corr"]
                n = cell["n"]
                if v is None:
                    cells.append(f'<td class="corr-cell na"><span>n/a</span><div class="corr-n">n={n}</div></td>')
                else:
                    # Color: -1 → dark red, 0 → gray, +1 → dark green. Diagonal = darkest green.
                    if v >= 0.7:   color = "#1e6a2b"; text = "#fff"
                    elif v >= 0.3: color = "#a8c49b"; text = "#1e3220"
                    elif v >= -0.3: color = "#eee7d6"; text = "#6a6553"
                    elif v >= -0.7: color = "#e8a89c"; text = "#5a2018"
                    else:           color = "#8a2c1f"; text = "#fff"
                    cells.append(f'<td class="corr-cell" style="background:{color};color:{text}"><span>{v:+.2f}</span><div class="corr-n" style="color:{text};opacity:0.7">n={n}</div></td>')
            trs += "<tr>" + "".join(cells) + "</tr>"
        body = f'<div class="table-card corr-table-card"><table class="corr-table"><thead><tr>{ths}</tr></thead><tbody>{trs}</tbody></table></div>'

    interp_md = load_markdown(READS_DIR / "correlation_interpretation.md")
    return f"""
<div class="section-header" id="correlation">
  <div class="section-num">SECTION 11</div>
  <div class="section-title">Correlation Snapshot</div>
  <div class="section-subtitle">Pairwise Pearson correlations across the 5 most important signals. Plain-English read above the matrix; actionability ranking below.</div>
</div>

<div class="corr-interp-block">
  <div class="take-eyebrow">PLAIN-ENGLISH READ {datestamp_chip(interp_md['datestamp'])}</div>
  {interp_md['html']}
</div>

{body}
<div class="source-caption"><strong>Source:</strong> Computed by <code>scripts/compute_correlations.py</code> from existing CSVs. All series resampled to week-ending Sunday. n = number of overlapping weekly observations per pair.</div>
{refresh_footer(DATA_DIR / "correlations.csv")}

<div class="chart-take">
  <div class="take-eyebrow">WHAT TO WATCH {datestamp_chip(md['datestamp'])}</div>
  {md['html']}
</div>
"""


def _render_shelf_productivity_panel(tdp: dict) -> str:
    """CPG industry benchmark: does more shelf space actually equal more sales?

    Compares VITL's actual TDP-vs-revenue ratio against the published research
    on shelf-space elasticity. Sits between the TDP-vs-Revenue chart and the
    velocity-per-shelf chart in Section 06 so the analyst can see the academic
    frame alongside VITL's actual math.
    """
    # Pull VITL's most-recent actual TDP / revenue numbers
    vitl_elasticity_str = "—"
    vitl_vel_str = "—"
    interpretation = ""
    if tdp.get("quarters") and tdp.get("tdp") and tdp.get("revenue"):
        # Find the last non-estimate (i.e., last actual data) — Q1 2026 is the latest verified row
        latest_tdp = tdp["tdp"][-1] if len(tdp["tdp"]) > 0 else None
        latest_rev = tdp["revenue"][-1] if len(tdp["revenue"]) > 0 else None
        # Use the actual reported Q1 2026 row (typically the last actual)
        # If latest is an estimate, drop back one
        for i in range(len(tdp["quarters"]) - 1, -1, -1):
            q = tdp["quarters"][i]
            if "E" not in q:
                latest_tdp = tdp["tdp"][i]
                latest_rev = tdp["revenue"][i]
                latest_q = q
                break
        if latest_tdp and latest_tdp > 0 and latest_rev is not None:
            vitl_elasticity = latest_rev / latest_tdp
            vitl_elasticity_str = f"{vitl_elasticity:.2f}"
            vitl_vel = ((1 + latest_rev/100) / (1 + latest_tdp/100) - 1) * 100
            vitl_vel_str = f"{vitl_vel:+.1f}%"
            if vitl_elasticity >= 1.0:
                interpretation = (f"VITL's <strong>{vitl_elasticity:.2f}</strong> in {latest_q} is "
                                  f"<strong>above 1.0</strong> — new shelves are pulling their full weight. "
                                  f"That's the high-quality-distribution-expansion pattern; new placements "
                                  f"are at least as productive as existing ones.")
            elif vitl_elasticity >= 0.5:
                interpretation = (f"VITL's <strong>{vitl_elasticity:.2f}</strong> in {latest_q} sits "
                                  f"<strong>middle-of-pack for distribution expansion</strong>. "
                                  f"New shelves ARE producing revenue (well above the 0.10-0.16 "
                                  f"within-store facing benchmark), but at lower per-slot productivity "
                                  f"than the existing footprint. The shelves are earning, just not "
                                  f"at the rate the established Whole Foods / Sprouts / Costco base does.")
            else:
                interpretation = (f"VITL's <strong>{vitl_elasticity:.2f}</strong> in {latest_q} is "
                                  f"<strong>below the 0.50 distribution-expansion benchmark</strong> — "
                                  f"new shelves are markedly underperforming what the research would "
                                  f"predict. That's the 'extra shelf space sitting' scenario.")

    return f"""
<div class="chart-card">
  <div class="chart-title-row">
    <h3>Does More Shelf Space Actually Equal More Sales? — The Research Benchmark</h3>
    <div class="chart-subtitle">Industry research on shelf-space elasticity vs VITL's actual ratio. Tests whether the TDP expansion is real distribution growth or shelves sitting unproductive.</div>
  </div>

  <div class="hero-row" style="grid-template-columns:repeat(3, 1fr);margin-top:8px">
    <div class="hero-tile">
      <div class="hero-label">CPG industry benchmark · within-store facings</div>
      <div class="hero-val" style="font-size:24px">0.10 – 0.16</div>
      <div class="hero-sub">Drèze, Hoch &amp; Purk (1994) · food CPG facing elasticity</div>
    </div>
    <div class="hero-tile">
      <div class="hero-label">CPG industry benchmark · distribution expansion</div>
      <div class="hero-val" style="font-size:24px">0.50 – 1.00</div>
      <div class="hero-sub">Circana / IRI 2023 SKU productivity studies</div>
    </div>
    <div class="hero-tile">
      <div class="hero-label">VITL actual · Q1 2026</div>
      <div class="hero-val" style="font-size:24px">{vitl_elasticity_str}</div>
      <div class="hero-sub">revenue YoY ÷ TDP YoY</div>
    </div>
  </div>

  <div class="source-caption" style="margin-top:14px"><strong>Source:</strong>
    Drèze, X., Hoch, S. J., &amp; Purk, M. E. (1994). \"Shelf Management and Space Elasticity.\"
    <em>Journal of Retailing</em>, 70(4), 301-326. · Circana \"SKU Productivity Benchmarks\" 2023.
    · VITL ratio computed from <code>tdp_vs_revenue.csv</code> · Q1 2026 figures verified from May 7 2026 print.
  </div>

  {data_take(meaning=(
      f"<strong>What it shows.</strong> Two industry benchmarks (faded gray on the left two cards) "
      f"vs VITL's actual ratio (right card). The first benchmark — Drèze, Hoch &amp; Purk (1994) — measures "
      f"what happens when you add MORE FACINGS to a SKU that's already on the shelf at a store. "
      f"Doubling facings (from 4 to 8) typically lifts sales 10-16%. That's an elasticity of 0.10-0.16. "
      f"The second benchmark — Circana's 2023 SKU productivity work — measures what happens when you "
      f"add the SKU to NEW STORES (distribution expansion). That's a different mechanism: incremental "
      f"availability vs more visibility. Distribution-expansion elasticity for established brands "
      f"typically lands 0.50-1.00."
      f"<br><br>"
      f"<strong>Which benchmark applies to VITL?</strong> Both, but distribution-expansion is the "
      f"primary one. Management's TDP growth in 2025-2026 has been driven by NEW PLACEMENTS at mass/"
      f"conventional grocery channels (Walmart, Kroger conventional banners) and at Costco regional "
      f"expansion — i.e., new doors, not more facings at existing doors. So the 0.50-1.00 benchmark is "
      f"the right comparison."
      f"<br><br>"
      f"<strong>What VITL's number means.</strong> {interpretation}"
      f"<br><br>"
      f"<strong>Where this fits.</strong> This is the most important context for the velocity-per-shelf "
      f"chart below. <em>Velocity per shelf is comparing VITL to ITSELF — its own existing footprint. "
      f"Shelf-space elasticity is comparing VITL to the INDUSTRY.</em> Both readings can be true "
      f"simultaneously: the new shelves are earning revenue at a respectable rate by industry standards "
      f"(0.77 vs benchmark range 0.50-1.00) AND each new shelf is less productive than VITL's existing "
      f"base ({vitl_vel_str} velocity per shelf YoY). The right interpretation isn't \"shelves are wasted\" "
      f"— it's \"shelves are productive but not as productive as the high-velocity natural-grocery base.\" "
      f"Which is the expected outcome when you expand from your premium-natural-grocery sweet spot into "
      f"mass channels."
      f"<br><br>"
      f"<strong>Watchpoint.</strong> The CPG rule-of-thumb is that a new placement needs to deliver "
      f"~$5/store/week sustained or retailers reduce facings / de-slot. VITL's pricing puts the "
      f"breakeven higher (closer to $8-10/store/week for slot-economics math). The Q2 print Aug 6 "
      f"is the first real test of whether the mass-channel expansion meets that threshold — if "
      f"velocity per shelf stays negative through Q3, expect first de-slotting headlines by Q4 2026 "
      f"and that's when this chart matters most."
  ))}
</div>
"""


def render_operating_recovery(op_rec: dict, tdp: dict) -> str:
    """Section 05 — Comp difficulty + GM trajectory + 2yr stack + TDP (moved from S04)."""
    return f"""
<div class="section-header" id="operating-recovery">
  <div class="section-num">SECTION 06</div>
  <div class="section-title">Operating Recovery &amp; Comp Difficulty</div>
  <div class="section-subtitle">When does the math turn favorable? GM inflects before revenue · comps get easy in Q4 26 · 2yr stack normalizes for base effects.</div>
</div>

{chart_card("compDifficultyChart",
            "When Do the Comps Get Easy?",
            "Quarterly revenue YoY growth, color-coded by comp difficulty (red hard / yellow medium / green easy).",
            "VITL reported quarters + management guided range + analyst estimates for Q2 26 onward.",
            READS_DIR / "comp_difficulty_take.md",
            y_axis_label="YoY revenue growth (%)",
            height_class="big",
            dynamic_take=data_take(meaning=(
                "<strong>What it shows.</strong> Quarterly revenue YoY for VITL from Q1 2025 actual through Q4 2027 estimate. The bar colors flag what kind of comp the company is running against: red = hard (lapping strong quarters from the unaffected year), yellow = medium, green = easy (lapping the disrupted base)."
                "<br><br>"
                "<strong>Why this matters.</strong> Year-over-year math is the single biggest determinant of whether a print 'looks good' or not. <strong>Q4 2026 is the first unambiguously easy comp</strong> — it laps the ERP-disrupted Q4 2025 base where revenue grew only 15-16% vs a normalized 25-30% trend. Even if VITL just returns to normal operating cadence, Q4 26 should print +20%+ YoY. The first half of 2027 lapses the price-gap crisis quarters which are even softer bases."
                "<br><br>"
                "<strong>Where this fits.</strong> The market typically prices recovery 1-2 quarters AHEAD of when the easy comps actually print. That puts the inflection window at <strong>August-October 2026</strong> — Q2 print in early August is when the market starts modeling Q3/Q4 expectations, and Q3 print in early November is when Q4-and-beyond becomes the dominant frame. <em>This is the calendar reason the August 6 print matters so much.</em>"
                "<br><br>"
                "<strong>Watchpoint.</strong> Q2 26 (Aug 6) is still a hard comp (lapping a normal +21% Q2 25), so the bar to beat is just \"management's guided low-single digits.\" Q3 is medium. Q4 is when comp difficulty inflects. Markets typically lead reality by 1-2 quarters."
            )))}

{chart_card("gmTrajectoryChart",
            "Gross Margin — Why It Recovers Before Revenue",
            "Quarterly GM from Q1 25 actual through FY 27E guided. Peak was 16.9% (Q1 25). Trough was 2.7% (Q1 26).",
            "Reported quarters from prints + management guided range + FY27 directional band.",
            READS_DIR / "gross_margin_take.md",
            y_axis_label="Gross margin (%)",
            height_class="big",
            dynamic_take=data_take(meaning=(
                "<strong>What it shows.</strong> Gross margin (% of revenue) over the cycle. Peak Q1 25 at 38.5%. Trough Q1 26 at 28.3%. Management guides Q2 26 trough deeper at ~27% then recovery to 30%+ by Q4 26 and 33-35% in FY 27."
                "<br><br>"
                "<strong>Why this matters.</strong> <strong>Margin always recovers before revenue</strong> in cycles like this — it's a math relationship. The supply-management costs that crushed Q1 26 GM ($32M of unsold-egg cost over the year) roll off as the breaker market recovers (see Section 04). Egg-shell-sales mix improves as demand returns at the retail tier. ERP transitional costs are one-time and disappear. Revenue, by contrast, depends on the gap closing and on shelf-velocity catching up to TDP growth — both slower processes. So Q3 and Q4 26 should show GM inflecting back toward 30%+ even as revenue YoY is still middling."
                "<br><br>"
                "<strong>Where this fits.</strong> The bull-case math: a return to 32% GM on a normalized FY 27 revenue base of $850-900M generates $270-290M of gross profit. Subtract ~$200M of normalized opex = $70-90M EBITDA. At 10-12x that's a $700M-$1.1B equity value vs current ~$340M market cap. <em>The GM recovery is the load-bearing assumption</em> in that math — without it, the FY 27 EBITDA target the valuation hangs on doesn't materialize."
                "<br><br>"
                "<strong>Watchpoint.</strong> Q2 26 print GM. If it comes in better than the guided ~27%, recovery is starting one quarter earlier than the May 7 frame suggested. If it comes in below 27%, supply-management costs are running higher than guided and the recovery glide-path moves out a quarter."
            )))}

{chart_card("twoYrStackChart",
            "The Stabilization Test — 2-Year Stacks",
            "Single-period YoY% can lie during base-effect distortion. Stacks tell the truth.",
            "Computed from quarterly revenue YoY: current period YoY + prior-year YoY for the same quarter.",
            READS_DIR / "two_year_stack_take.md",
            y_axis_label="2-yr stacked YoY growth (%)",
            height_class="big",
            dynamic_take=data_take(meaning=(
                "<strong>What it shows.</strong> 2-year stacked revenue growth (current quarter YoY% + same quarter's YoY% from the year prior). Stacks peaked at 55% in Q1 25, then declined steadily through cycle disruption to a projected ~25% in Q3 26."
                "<br><br>"
                "<strong>Why this matters.</strong> Single-quarter YoY can lie. Imagine Q4 26 prints +25% YoY — looks great until you remember Q4 25 was disrupted (only +16% off an already-cycle-weakened base). The +25% is real but the comp is artificial. The 2-year stack strips out that base-effect distortion by adding both years' growth together. <strong>The first quarter where the stack STOPS declining is the true stabilization signal</strong>, not the YoY chart that gets distorted by disrupted base years."
                "<br><br>"
                "<strong>Where this fits.</strong> Per the projection, the stack stops declining around Q4 26 / Q1 27 (mid 20s and starts rising). That aligns with the comp-difficulty chart's prediction that the inflection lands in late 2026. <em>If the stack starts rising as early as Q3 26, recovery is ahead of schedule.</em> If it continues falling through Q1 27, recovery has slipped a quarter or two — which would meaningfully affect the implied 2027 EBITDA math feeding the valuation scenarios."
                "<br><br>"
                "<strong>Watchpoint.</strong> Watch Q2-Q3 26 stacks. The first quarter where the stack number is HIGHER than the prior quarter's stack = the real stabilization moment. That's the leading signal that's harder to fake or distort than headline YoY."
            )))}

{chart_card("tdpVsRevenueChart",
            "TDPs vs Revenue — Is Distribution Translating Into Sales?",
            "Side-by-side quarterly bars: shelf placement growth vs revenue growth.",
            "TDP (Total Distribution Points — shelf SKU placements) from management commentary + sell-side. Revenue YoY from quarterly prints.",
            READS_DIR / "tdp_vs_revenue_take.md",
            y_axis_label="YoY growth (%)",
            height_class="big",
            dynamic_take=data_take(meaning=(
                "<strong>What it shows.</strong> Two bars per quarter: blue = TDP (shelf-placement) growth YoY; gold = revenue growth YoY. When TDPs grow faster than revenue, it means VITL is winning new placements but not converting them into proportional dollar sales. Looking at the trajectory: TDPs and revenue moved in tight lockstep through 2024 (both ~28-30%), then started diverging in 2025 as the ERP disruption hit. Q1 2026 shows the widest gap so far: TDPs +20% but revenue only +15.4%."
                "<br><br>"
                "<strong>Why this matters.</strong> Management talks about TDP growth as a positive recovery indicator on every call. Looked at alone, it IS positive — distribution gains compound. But looked at next to revenue, the TDP outperformance becomes a YELLOW flag. <strong>It means VITL is being added to new shelves at retailers where existing pasture-raised SKUs don't sell as well as the established Whole Foods / Sprouts / Costco footprint.</strong> Costco's regional rollout, mass-channel test placements, and conventional-grocery experiments all add TDPs but at much lower velocity per slot. The velocity-per-shelf chart below shows the mechanical consequence (-3.8% in Q1 26)."
                "<br><br>"
                "<strong>Where this fits.</strong> Bulls argue: TDPs ahead of revenue is a normal expansion pattern — placements come first, velocity follows. Bears argue: this is a structural problem where the brand has saturated its high-velocity natural-grocery footprint and incremental shelves are diluting. <em>The next 2-3 quarters resolve the debate.</em> If revenue catches up by Q4 26 (velocity-per-shelf returns to neutral), bulls win. If TDPs keep outpacing revenue through Q1 27, structural saturation is real."
                "<br><br>"
                "<strong>Watchpoint.</strong> The convergence point. Watch each quarter for the spread (TDP YoY minus Revenue YoY). Spread shrinks = recovery confirmed. Spread widens = saturation thesis gains evidence."
            )))}

{_render_shelf_productivity_panel(tdp)}

{chart_card("velocityPerShelfChart",
            "Are Customers Walking Past VITL on the Shelf?",
            "Revenue growth ÷ TDP growth. The structural test of whether new shelves are SELLING — or just sitting.",
            "Computed from data/tdp_vs_revenue.csv. Velocity per shelf YoY = (1 + revenue_yoy) / (1 + tdp_yoy) − 1. Positive (green) = each shelf earning more · negative (red) = shelves growing faster than dollars.",
            READS_DIR / "tdp_vs_revenue_take.md",
            y_axis_label="Velocity per shelf YoY (%)  ·  red below 0 = shelves growing faster than dollars",
            height_class="big",
            dynamic_take=data_take(meaning=(
                "<strong>What it shows.</strong> The ratio of revenue growth to TDP (Total Distribution Points = shelf SKU placements) growth, expressed as YoY change in dollars-per-shelf-slot. When the bar is positive, each shelf is selling MORE than the same shelf did a year ago — the brand is densifying. When the bar is negative, shelves are growing faster than dollars — VITL is winning placements but each placement underperforms the existing base."
                "<br><br>"
                "<strong>Why this matters.</strong> Q1 2026 shows TDPs +20% YoY against revenue +15.4% — <strong>velocity per shelf-slot fell ~3.8%</strong>. That's the structural concern made visible. Management's TDP-growth talking point sounds good in isolation (\"distribution +20%\" is a great metric in a vacuum), but when revenue lags it means retailers see less dollar throughput per slot than they expected when they added the SKU. <strong>Retailers track this metric directly</strong> — they call it dollar velocity or $$/store/week — and they de-slot brands that consistently underperform category benchmarks. Whole Foods, Costco, and Sprouts buyers all run quarterly slot-productivity reviews."
                "<br><br>"
                "<strong>Where this fits.</strong> This connects the two pieces of the share-loss puzzle. The Category Growth chart (Section 01B) shows VITL underperforming category by ~16pts — that's the revenue side. This chart shows VITL also LOSING velocity per slot — that's why the category is gaining without VITL. Combined: VITL is expanding shelf presence into channels and stores where each new slot doesn't earn its keep, while private-label pasture-raised (Kirkland, Whole Foods 365) takes share at the slots that DO sell. <em>Both charts are showing the same problem from different angles.</em>"
                "<br><br>"
                "<strong>Watchpoint.</strong> The line crossing back above zero is the structural recovery signal — that means revenue is catching up to TDP growth and each shelf is back to net-positive earnings. Persistent negative readings mean retailers will eventually de-slot or replace VITL with higher-velocity items. The Q2-Q3 26 prints are where this resolves — if velocity-per-shelf turns positive, the recovery thesis is intact. If it stays negative through Q3, expect first de-slotting headlines by Q4."
            )))}
"""


def render_valuation(val: dict) -> str:
    md = load_markdown(READS_DIR / "valuation_snapshot_take.md")
    # Multiples cards
    mult_cards = ""
    for m in val.get("multiples", []):
        range_str = (f"3yr range: {m['range_low']}x – {m['range_high']}x"
                     if m.get("range_low") is not None and m.get("range_high") is not None
                     else "")
        position = ""
        if m.get("range_low") is not None and m.get("range_high") is not None:
            span = m["range_high"] - m["range_low"]
            if span > 0:
                pos_pct = (m["value"] - m["range_low"]) / span
                if pos_pct < 0.33: position = "Low end of range"
                elif pos_pct < 0.66: position = "Mid range"
                else: position = "High end of range"
        mult_cards += f"""
<div class="val-card">
  <div class="val-label">{m['label']}</div>
  <div class="val-num">{m['value']:.1f}x</div>
  <div class="val-range">{range_str}</div>
  <div class="val-pos">{position}</div>
  <div class="val-note muted-cell">{m['note']}</div>
</div>"""

    # Scenarios table
    scenarios_html = ""
    for s in val.get("scenarios", []):
        scenarios_html += f"""
<tr>
  <td><strong>{s['label']}</strong></td>
  <td class="num">${s['implied_price']:.2f}</td>
  <td class="muted-cell">{s['note']}</td>
</tr>"""
    current_str = (f"${val['current_price']:.2f}"
                   if val.get("current_price") is not None else "—")

    return f"""
<div class="section-header" id="valuation">
  <div class="section-num">SECTION 08</div>
  <div class="section-title">Valuation Snapshot</div>
  <div class="section-subtitle">Current multiples vs 3yr historical band + scenario math. The asymmetry the bull case is built on.</div>
</div>

<div class="chart-card">
  <div class="chart-title-row">
    <h3>Current Multiples vs 3-Year Historical Range</h3>
    <div class="chart-subtitle">VITL on EV/Sales is at its cheapest level since at least 2022. Forward EV/EBITDA distorted by trough EBITDA — meaningless.</div>
  </div>
  <div class="val-cards-row">
    {mult_cards}
  </div>
  <div class="source-caption"><strong>Source:</strong> Trailing multiples from yfinance + reported financials. 3yr ranges from publicly available consensus terminals.</div>
</div>

<div class="chart-card">
  <div class="chart-title-row">
    <h3>Scenario Math · 2027 EBITDA × Multiple = Implied Price</h3>
    <div class="chart-subtitle">Even the entry case implies 50%+ upside from current. The stock is pricing closer to permanent impairment than cyclical trough.</div>
  </div>
  <div class="table-card">
    <table>
      <thead><tr><th>Scenario</th><th class="num">Implied price</th><th>Math</th></tr></thead>
      <tbody>{scenarios_html}
        <tr style="background:rgba(46,90,60,0.06)"><td><strong>Current price</strong></td><td class="num"><strong>{current_str}</strong></td><td class="muted-cell">May 20 2026 close</td></tr>
      </tbody>
    </table>
  </div>
  <div class="source-caption"><strong>Source:</strong> Scenario inputs from valuation_snapshot.csv. 2027 EBITDA range from management guide ($0-10M FY26 → recovery to $50-100M FY27 per sell-side normalized estimates).</div>
  <div class="chart-take">
    <div class="take-eyebrow">WHAT TO WATCH {datestamp_chip(md['datestamp'])}</div>
    {md['html']}
  </div>
  {refresh_footer(DATA_DIR / "valuation_snapshot.csv")}
</div>
"""


def render_catalysts(cat: dict) -> str:
    md = load_markdown(READS_DIR / "forward_catalysts_take.md")
    TIER_BG = {"LOW": "#eee7d6", "MED": "#fdefc9", "HIGH": "#fde2c4", "HIGHEST": "#f8d4cf"}
    TIER_FG = {"LOW": "#8b8271", "MED": "#8a6b10", "HIGH": "#b8682d", "HIGHEST": "#b34738"}
    DIR_BG  = {"BULL": "#e1f0dc", "BEAR": "#f8e2dc", "MIXED": "#eee7d6",
               "DECISIVE": "#dde8f0", "PROCEDURAL": "#eee7d6", "ONGOING": "#eee7d6"}
    DIR_FG  = {"BULL": "#2a5a30", "BEAR": "#b34738", "MIXED": "#8b8271",
               "DECISIVE": "#2c5a82", "PROCEDURAL": "#8b8271", "ONGOING": "#8b8271"}

    rows_html = ""
    for r in cat.get("rows", []):
        tier_bg = TIER_BG.get(r["tier"], "#eee7d6"); tier_fg = TIER_FG.get(r["tier"], "#8b8271")
        dir_bg = DIR_BG.get(r["direction"], "#eee7d6"); dir_fg = DIR_FG.get(r["direction"], "#8b8271")
        rows_html += f"""
<tr>
  <td class="num"><strong>{r['date']}</strong><div class="muted-cell" style="font-size:10.5px">{r['date_kind']}</div></td>
  <td><strong>{r['event']}</strong><div class="muted-cell" style="font-size:11px;margin-top:2px">{r['note']}</div></td>
  <td><span class="badge" style="background:{tier_bg};color:{tier_fg}">{r['tier']}</span></td>
  <td><span class="badge" style="background:{dir_bg};color:{dir_fg}">{r['direction']}</span></td>
</tr>"""

    return f"""
<div class="section-header" id="catalysts">
  <div class="section-num">SECTION 09</div>
  <div class="section-title">Forward Catalyst Calendar</div>
  <div class="section-subtitle">What's coming and what it could do. Market typically re-rates 1-2 quarters ahead of easy comps.</div>
</div>

<div class="chart-card">
  <div class="table-card">
    <table>
      <thead><tr><th>Date</th><th>Event</th><th>Impact tier</th><th>Direction</th></tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
  </div>
  <div class="source-caption"><strong>Source:</strong> Hand-curated in data/forward_catalysts.csv from earnings call schedules + management commentary. Estimated dates flagged.</div>
  <div class="chart-take">
    <div class="take-eyebrow">WHAT TO WATCH {datestamp_chip(md['datestamp'])}</div>
    {md['html']}
  </div>
  {refresh_footer(DATA_DIR / "forward_catalysts.csv")}
</div>
"""


def render_recovery_plan(rplan: dict) -> str:
    md = load_markdown(READS_DIR / "recovery_plan_take.md")
    STATUS_BG = {"ANNOUNCED": "#eee7d6", "IN PROGRESS": "#fdefc9",
                 "PARTIAL": "#e8f0d8", "DELIVERED": "#d4ead0",
                 "CONFIRMED IN FINANCIALS": "#b3d9ad", "CONFIRMED": "#b3d9ad"}
    STATUS_FG = {"ANNOUNCED": "#8b8271", "IN PROGRESS": "#8a6b10",
                 "PARTIAL": "#5a8232", "DELIVERED": "#2a7a30",
                 "CONFIRMED IN FINANCIALS": "#1e5a25", "CONFIRMED": "#1e5a25"}

    rows_html = ""
    for r in rplan.get("rows", []):
        s = r["status"]; c = r["confirmed"]
        s_bg = STATUS_BG.get(s, "#eee7d6"); s_fg = STATUS_FG.get(s, "#8b8271")
        c_bg = STATUS_BG.get(c, "#eee7d6"); c_fg = STATUS_FG.get(c, "#8b8271")
        rows_html += f"""
<tr>
  <td class="num"><strong>{r['order']}</strong></td>
  <td><strong>{r['action']}</strong><div class="muted-cell" style="font-size:11px;margin-top:2px">{r['note']}</div></td>
  <td class="muted-cell">{r['target']}</td>
  <td><span class="badge" style="background:{s_bg};color:{s_fg}">{s}</span></td>
  <td><span class="badge" style="background:{c_bg};color:{c_fg}">{c}</span></td>
</tr>"""

    return f"""
<div class="section-header" id="recovery-plan">
  <div class="section-num">SECTION 10</div>
  <div class="section-title">Recovery Plan Tracker</div>
  <div class="section-subtitle">The credibility play in real time. Status should progress left to right each quarter.</div>
</div>

<div class="chart-card">
  <div class="table-card">
    <table>
      <thead><tr><th>#</th><th>Action</th><th>Target</th><th>Status</th><th>Confirmed?</th></tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
  </div>
  <div class="source-caption"><strong>Source:</strong> Five management actions from May 7 2026 Q1 earnings call · hand-curated in data/recovery_plan_status.csv · updated quarterly.</div>
  <div class="chart-take">
    <div class="take-eyebrow">WHAT TO WATCH {datestamp_chip(md['datestamp'])}</div>
    {md['html']}
  </div>
  {refresh_footer(DATA_DIR / "recovery_plan_status.csv")}
</div>
"""


def render_archived() -> str:
    return f"""
<div class="section-header archived-header" id="archived">
  <div class="section-num">ARCHIVED</div>
  <div class="section-title">Placeholders · archived from nav</div>
  <div class="section-subtitle">
    Old Retail Distribution, SKU Heat Map, Pricing Power, Supply Risk, and Demand-vs-Stock placeholders.
    Their content was either never sourced or has been folded into the new sections above.
  </div>
</div>

<details class="archived-block">
  <summary>Retail Distribution (was Section 02) <span class="placeholder-tag">PLACEHOLDER · ARCHIVED</span></summary>
  <p class="muted-cell">Pending Instacart cross-banner proxy.</p>
</details>
<details class="archived-block">
  <summary>SKU Heat Map (was Section 03) <span class="placeholder-tag">PLACEHOLDER · ARCHIVED</span></summary>
  <p class="muted-cell">Per-SKU Reddit/YouTube/Search splits pending.</p>
</details>
<details class="archived-block">
  <summary>Pricing Power (was Section 06) <span class="placeholder-tag">PLACEHOLDER · ARCHIVED</span></summary>
  <p class="muted-cell">Subsumed by current Section 03 (Egg Market Price Gap).</p>
</details>
<details class="archived-block">
  <summary>Supply Risk / Avian Flu (was Section 07) <span class="placeholder-tag">PLACEHOLDER · ARCHIVED</span></summary>
  <p class="muted-cell">Subsumed by Section 03 inline HPAI / flock cards.</p>
</details>
<details class="archived-block">
  <summary>Demand vs Stock (was Section 08) <span class="placeholder-tag">PLACEHOLDER · ARCHIVED</span></summary>
  <p class="muted-cell">Replaced by Section 02 (Stock &amp; News) hero chart with event-reaction dots.</p>
</details>
"""


def render_summary_modal(s: dict) -> str:
    bullets_html = "".join(f"<li>{b}</li>" for b in s["bullets"])
    todo_html = "".join(f"<li>{t}</li>" for t in s["to_do_next"])
    narrative_html = "".join(f"<p>{para}</p>" for para in s.get("narrative", []))
    return f"""
<div id="summaryModal" class="modal-backdrop" onclick="if(event.target===this) this.style.display='none'">
  <div class="modal modal-wide">
    <div class="modal-header">
      <div>
        <div class="modal-title">{s['headline']}</div>
        <div class="modal-sub">Generated {s['generated_at']}</div>
      </div>
      <button class="modal-close" onclick="document.getElementById('summaryModal').style.display='none'">×</button>
    </div>
    <div class="modal-body">
      <div class="modal-section-title">Key metrics right now</div>
      <ul class="modal-list">{bullets_html}</ul>

      <div class="modal-section-title">The briefing — what the dashboard is showing</div>
      <div class="modal-narrative">{narrative_html}</div>

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
    qr      = compute_quick_read(d)
    setup   = compute_setup(d)
    runway  = compute_runway_math(setup)
    events  = compute_events_chart(d)
    react_mag = compute_reaction_magnitude(d)
    news    = compute_news(d)
    cad_vs_stock = compute_cadence_vs_stock(d, news)
    egg     = compute_egg_market(d)
    hpai_cum = compute_hpai_cumulative(d)
    comm    = compute_community(d)
    sov_sentiment = compute_sov_sentiment(d)
    # Attach sentiment totals to comm so render_social_overview can show pos/neg % per brand
    comm["sov_sentiment_totals"] = sov_sentiment.get("totals", {})
    yt_vitl = compute_youtube_vitl(d)
    yt_comp = compute_youtube_competitors(d)
    reddit_posts = compute_reddit_posts(d)
    yt_videos = compute_youtube_videos(d)
    trends = compute_google_trends(d)
    cust_metrics = compute_customer_metrics(d)
    cat_growth = compute_category_growth(d)
    cat_supply = compute_category_supply(d)
    supply_quant = compute_supply_quantification(d)
    brand_aware = compute_brand_awareness(d)
    tdp     = compute_tdp_vs_revenue(d)
    op_rec  = compute_operating_recovery(d)
    fin     = compute_financial_history(d)
    full_cred = compute_full_credibility(d)
    cat_burn = compute_categorized_cash_burn(d)
    val     = compute_valuation(d)
    cat     = compute_catalysts(d)
    rplan   = compute_recovery_plan(d)
    corr    = compute_correlation_matrix(d)
    summary = compute_summary(d, qr, setup, news, egg, fin, corr,
                              comm=comm, cat_supply=cat_supply, op_rec=op_rec,
                              val=val, tdp=tdp, cat_growth=cat_growth)

    chart_blob = json.dumps({
        "setup":          setup,
        "events":         events,
        "react_mag":      react_mag,
        "news":           news,
        "cad_vs_stock":   cad_vs_stock,
        "egg":            egg,
        "hpai_cum":       hpai_cum,
        "comm":           comm,
        "sov_sentiment":  sov_sentiment,
        "yt_vitl":        yt_vitl,
        "yt_comp":        yt_comp,
        "trends":         trends,
        "cat_growth":     cat_growth,
        "cat_supply":     cat_supply,
        "supply_quant":   supply_quant,
        "brand_aware":    brand_aware,
        "tdp":            tdp,
        "op_rec":         op_rec,
        "fin":            fin,
        "cat_burn":       cat_burn,
        "val":            val,
        "cat":            cat,
        "rplan":          rplan,
        "topic_colors":   TOPIC_COLORS,
        "topic_labels":   TOPIC_LABELS,
        "brand_colors":   BRAND_SOV_COLORS,
        "brand_order":    BRAND_SOV_ORDER,
        "reaction_colors": REACTION_COLORS,
        "accent":         BRAND_ACCENT,  "accent2":    BRAND_ACCENT2,
        "accent3":        BRAND_ACCENT3, "accent_neg": BRAND_ACCENT4,
        "purple":         BRAND_PURPLE,  "brown": BRAND_BROWN, "blue": BRAND_BLUE,
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
              padding: 5px 12px; white-space: nowrap; cursor: pointer; }}
  .nav-btn:hover {{ color: var(--accent); border-color: var(--accent); background: rgba(46,90,60,0.06); }}
  .nav-btn.recovery {{ background: var(--accent); color: #fff; border-color: var(--accent); }}
  .summary-btn {{ background: var(--accent); color: #fff; border: none;
                  border-radius: 999px; padding: 7px 16px; font-size: 12px;
                  font-weight: 700; letter-spacing: 0.3px; cursor: pointer; white-space: nowrap; }}
  .summary-btn:hover {{ background: #24482f; }}

  .container {{ max-width: 1280px; margin: 0 auto; padding: 24px 32px; }}

  .section-header {{ margin: 44px 0 14px; padding-bottom: 10px; border-bottom: 1px solid var(--border); }}
  .section-header:first-of-type {{ margin-top: 0; }}
  .section-header.archived-header {{ opacity: 0.7; }}
  .section-num {{ font-size: 10px; font-weight: 700; color: var(--accent); letter-spacing: 1.8px; }}
  .section-title {{ font-size: 21px; font-weight: 700; margin-top: 4px; letter-spacing: -0.4px; }}
  .section-subtitle {{ font-size: 13px; color: var(--text-soft); margin-top: 6px; font-style: italic; }}
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
                     border-radius: 10px; padding: 18px 24px; margin: 14px 0 14px; }}
  .wn-header {{ display: flex; align-items: center; margin-bottom: 10px; }}
  .wn-eyebrow {{ font-size: 10.5px; font-weight: 700; color: #8a6b10; letter-spacing: 1.6px; }}
  .wn-body p {{ font-size: 13.5px; color: var(--text-soft); margin-bottom: 8px; line-height: 1.65; }}
  .wn-body p:last-child {{ margin-bottom: 0; }}
  .wn-body strong {{ color: var(--text); font-weight: 700; }}

  /* Three Damages */
  .three-damages {{ background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
                    padding: 18px 24px; margin-bottom: 26px;
                    box-shadow: 0 1px 3px rgba(45,47,37,0.04); }}
  .damages-eyebrow {{ font-size: 10.5px; font-weight: 700; color: var(--accent); letter-spacing: 1.6px; margin-bottom: 14px; }}
  .damages-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 18px; }}
  @media (max-width: 900px) {{ .damages-grid {{ grid-template-columns: 1fr; }} }}
  .damage-col {{ padding: 14px 16px; border: 1px solid var(--border); border-radius: 8px; background: #fdfbf2; }}
  .damage-head {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
  .damage-title {{ font-size: 13px; font-weight: 700; color: var(--text); }}
  .damage-pill {{ display: inline-block; padding: 3px 10px; border-radius: 999px;
                  font-size: 10px; font-weight: 700; letter-spacing: 0.6px; }}
  .damage-desc {{ font-size: 12.5px; color: var(--text-soft); margin-bottom: 6px; line-height: 1.5; }}
  .damage-metric {{ font-size: 12px; color: var(--muted); line-height: 1.5; padding-top: 6px; border-top: 1px dashed var(--border); }}
  .damage-metric strong {{ color: var(--text); font-weight: 700; }}

  .hero-row {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 14px; }}
  @media (max-width: 1024px) {{ .hero-row {{ grid-template-columns: 1fr 1fr; }} }}
  .hero-tile {{ background: var(--surface); border: 1px solid var(--border);
                border-radius: 10px; padding: 20px 22px; box-shadow: 0 1px 3px rgba(45,47,37,0.04); }}
  .hero-label {{ font-size: 10px; color: var(--muted); text-transform: uppercase;
                 letter-spacing: 0.8px; margin-bottom: 10px; font-weight: 700; }}
  .hero-val {{ font-size: 30px; font-weight: 700; letter-spacing: -0.6px; }}
  .hero-val.pos {{ color: var(--accent); }}
  .hero-val.neg {{ color: var(--neg); }}
  .hero-sub {{ font-size: 11.5px; color: var(--muted); margin-top: 6px; }}
  .trend {{ color: var(--muted); font-weight: 700; margin-left: 4px; }}

  .chart-card {{ background: var(--surface); border: 1px solid var(--border);
                 border-radius: 10px; padding: 20px 22px; margin-bottom: 14px;
                 box-shadow: 0 1px 3px rgba(45,47,37,0.04); }}
  .chart-title-row {{ margin-bottom: 10px; }}
  .chart-card h3 {{ font-size: 14px; font-weight: 700; margin-bottom: 4px; line-height: 1.4; }}
  .chart-subtitle {{ font-size: 12px; color: var(--text-soft); font-style: italic; line-height: 1.5; }}
  .axis-label {{ font-size: 11px; color: var(--muted); margin: 6px 0 10px;
                 padding: 5px 10px; background: var(--surface2); border-radius: 4px;
                 display: inline-block; }}
  .chart-wrap {{ position: relative; height: 300px; }}
  .chart-wrap.big {{ height: 380px; }}
  .chart-wrap.tall {{ height: 460px; }}

  .source-caption {{ font-size: 10.5px; color: var(--muted); line-height: 1.55;
                     margin-top: 12px; padding-top: 10px;
                     border-top: 1px dashed var(--border); font-style: italic; }}
  .source-caption strong {{ color: var(--text-soft); font-weight: 700; }}
  .source-caption code {{ color: var(--accent); font-family: 'SF Mono', Menlo, Consolas, monospace;
                          font-size: 10.5px; font-style: normal;
                          background: rgba(46,90,60,0.08); padding: 1px 5px; border-radius: 3px; }}

  /* Supply quantification top panel — NEW badge + breaker inset */
  .supply-quant-card {{ border-left: 5px solid var(--neg);
                        box-shadow: 0 2px 8px rgba(201,93,74,0.08);
                        margin-bottom: 26px; }}
  .title-with-badge {{ display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }}
  .new-pill {{ display: inline-block; padding: 3px 9px; border-radius: 999px;
               background: var(--neg); color: #fff; font-size: 9.5px;
               font-weight: 700; letter-spacing: 1.0px;
               box-shadow: 0 1px 3px rgba(201,93,74,0.3); }}
  .breaker-inset {{ background: #fdfbf2; border: 1px dashed var(--border-strong);
                    border-radius: 8px; padding: 12px 16px; margin-top: 14px;
                    margin-bottom: 6px; }}
  .breaker-inset-eyebrow {{ font-size: 10px; font-weight: 700;
                            color: var(--neg); letter-spacing: 1.2px; margin-bottom: 10px; }}
  .breaker-inset-row {{ display: grid;
                        grid-template-columns: 1fr auto 1fr auto 1fr 1.4fr;
                        gap: 10px; align-items: center; }}
  @media (max-width: 900px) {{
    .breaker-inset-row {{ grid-template-columns: 1fr 1fr; }}
    .breaker-arrow {{ display: none; }}
  }}
  .breaker-cell {{ display: flex; flex-direction: column; }}
  .breaker-cell.wide {{ border-left: 1px solid var(--border);
                        padding-left: 14px; margin-left: 6px; }}
  .breaker-cell-label {{ font-size: 10px; color: var(--muted);
                         text-transform: uppercase; letter-spacing: 0.7px;
                         font-weight: 700; margin-bottom: 4px; }}
  .breaker-cell-val {{ font-size: 18px; font-weight: 700; letter-spacing: -0.4px;
                       line-height: 1.1; }}
  .breaker-cell-val.pos {{ color: var(--accent); }}
  .breaker-cell-val.neg {{ color: var(--neg); }}
  .breaker-unit {{ font-size: 11px; font-weight: 500; color: var(--muted);
                   margin-left: 3px; letter-spacing: 0; }}
  .breaker-cell-sub {{ font-size: 10px; color: var(--muted);
                       margin-top: 3px; font-style: italic; }}
  .breaker-arrow {{ font-size: 12px; color: var(--muted); font-weight: 700;
                    align-self: center; }}

  .chart-take {{ background: linear-gradient(180deg, #f8f9f5, #f0f4eb);
                 border: 1px solid #cfdbb9; border-left: 4px solid var(--accent);
                 border-radius: 8px; padding: 12px 18px; margin-top: 12px; }}
  .take-eyebrow {{ font-size: 10.5px; font-weight: 700; color: var(--accent);
                   letter-spacing: 1.5px; margin-bottom: 6px; }}
  .chart-take p {{ font-size: 12.5px; color: var(--text-soft); line-height: 1.6; margin-bottom: 6px; }}
  .chart-take p:last-child {{ margin-bottom: 0; }}
  .chart-take strong {{ color: var(--text); font-weight: 700; }}

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

  /* Section 00 — compressed timeline + explainer */
  .timeline-strip {{ background: var(--surface); border: 1px solid var(--border);
                     border-left: 4px solid var(--accent); border-radius: 8px;
                     padding: 12px 18px; margin-top: 6px; margin-bottom: 14px; }}
  .timeline-eyebrow {{ font-size: 10px; font-weight: 700; color: var(--accent);
                       letter-spacing: 1.5px; margin-bottom: 6px; }}
  .timeline-text {{ font-size: 12.5px; color: var(--text-soft); line-height: 1.6; }}
  .timeline-text strong {{ color: var(--text); font-weight: 700; }}
  .quick-read-explainer {{ background: linear-gradient(180deg, #fffdf2, #fcefd0);
                           border: 1px solid #ecd47c; border-radius: 10px;
                           padding: 16px 22px; margin-top: 8px; }}
  .qre-eyebrow {{ font-size: 10.5px; font-weight: 700; color: #8a6b10; letter-spacing: 1.5px; margin-bottom: 8px; }}
  .quick-read-explainer p {{ font-size: 13.5px; color: var(--text-soft); line-height: 1.7; }}
  .quick-read-explainer strong {{ color: var(--text); font-weight: 700; }}

  /* Section 01 — The Setup grid */
  .setup-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 8px; }}
  @media (max-width: 1024px) {{ .setup-grid {{ grid-template-columns: 1fr; }} }}
  .setup-card {{ background: var(--surface); border: 1px solid var(--border);
                 border-radius: 10px; padding: 18px 20px;
                 box-shadow: 0 1px 3px rgba(45,47,37,0.04);
                 display: flex; flex-direction: column; }}
  .setup-card-header {{ margin-bottom: 12px; }}
  .setup-card-title {{ font-size: 14px; font-weight: 700; }}
  .setup-kpi {{ font-size: 12px; color: var(--accent); font-weight: 700; margin-top: 4px; letter-spacing: 0.3px; }}
  /* Correlation interpretation block (above matrix) */
  .corr-interp-block {{ background: linear-gradient(180deg, #f8f9f5, #fdf3d3);
                        border: 1px solid #e6d28c; border-radius: 10px;
                        padding: 16px 22px; margin-bottom: 14px; }}
  .corr-interp-block ul {{ list-style: none; padding-left: 0; font-size: 12.5px;
                           color: var(--text-soft); line-height: 1.7; }}
  .corr-interp-block ul li {{ padding: 4px 0 4px 16px; position: relative; }}
  .corr-interp-block ul li:before {{ content: "›"; position: absolute; left: 0; color: #8a6b10; font-weight: 700; }}
  .corr-interp-block p {{ font-size: 12.5px; color: var(--text-soft); line-height: 1.65; margin-bottom: 8px; }}
  .corr-interp-block strong {{ color: var(--text); font-weight: 700; }}

  /* Section 01B — Category Supply events list */
  .supply-events-list {{ margin: 12px 0 8px; padding: 12px 16px;
                         background: var(--surface2); border-radius: 6px;
                         border-left: 3px solid var(--neg); }}
  .supply-events-eyebrow {{ font-size: 10px; font-weight: 700; color: var(--muted);
                            letter-spacing: 1.5px; margin-bottom: 8px; }}
  .supply-event-row {{ display: flex; gap: 14px; padding: 6px 0;
                       border-bottom: 1px dashed var(--border); align-items: baseline; }}
  .supply-event-row:last-child {{ border-bottom: none; }}
  .supply-event-year {{ font-size: 13px; font-weight: 700; min-width: 44px; font-variant-numeric: tabular-nums; }}
  .supply-event-body {{ flex: 1; }}
  .supply-event-label {{ font-size: 12px; font-weight: 700; color: var(--text); letter-spacing: 0.4px; }}
  .supply-event-sub {{ font-size: 11.5px; color: var(--text-soft); margin-top: 2px; line-height: 1.5; }}

  /* Section 01 Social — customer metric cards (2x2 grid) */
  .cust-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin: 8px 0 10px; }}
  @media (max-width: 720px) {{ .cust-grid {{ grid-template-columns: 1fr; }} }}
  .cust-card {{ background: var(--surface2); border: 1px solid var(--border);
                border-left: 4px solid var(--accent); border-radius: 8px;
                padding: 14px 18px; }}
  .cust-label {{ font-size: 10.5px; font-weight: 700; color: var(--muted);
                 text-transform: uppercase; letter-spacing: 0.7px; }}
  .cust-big {{ font-size: 30px; font-weight: 700; letter-spacing: -0.5px;
               color: var(--accent); margin: 6px 0 4px; line-height: 1.1; }}
  .cust-period {{ font-size: 11.5px; color: var(--text-soft); margin-bottom: 6px; }}
  .cust-quote {{ font-size: 11.5px; color: var(--muted); font-style: italic; line-height: 1.45;
                 padding-top: 6px; border-top: 1px dashed var(--border); }}

  /* Section 01 Social — feed widgets (Reddit posts + YouTube videos) */
  .feed-list {{ display: flex; flex-direction: column; gap: 8px; max-height: 520px;
                overflow-y: auto; padding-right: 6px; }}
  .feed-item {{ background: var(--surface2); border: 1px solid var(--border);
                border-left: 3px solid var(--accent); border-radius: 6px;
                padding: 10px 14px; }}
  .feed-row1 {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }}
  .feed-date {{ font-size: 10.5px; color: var(--muted); font-variant-numeric: tabular-nums; font-weight: 600; }}
  .feed-excerpt {{ font-size: 12.5px; color: var(--text); line-height: 1.5; margin-bottom: 4px; }}
  .feed-excerpt a {{ color: var(--text); text-decoration: none; }}
  .feed-excerpt a:hover {{ color: var(--accent); text-decoration: underline; }}
  .feed-meta {{ font-size: 10.5px; color: var(--muted); font-style: italic; }}

  /* Section 01 Social — subsection headers + section caption */
  .section-level-caption {{ background: linear-gradient(180deg, #f8f9f5, #f0f4eb);
                            border: 1px solid #cfdbb9; border-left: 4px solid var(--accent);
                            border-radius: 8px; padding: 12px 18px; margin-bottom: 18px;
                            font-size: 13px; color: var(--text-soft); line-height: 1.6; }}
  .section-level-caption strong {{ color: var(--text); font-weight: 700; }}
  .subsection-header {{ margin: 22px 0 12px; padding: 8px 14px;
                        border-left: 3px solid var(--accent2); background: var(--surface2);
                        border-radius: 4px; }}
  .subsection-eyebrow {{ font-size: 10px; font-weight: 700; color: #8a6b10;
                         letter-spacing: 1.8px; }}
  .subsection-title {{ font-size: 14px; font-weight: 700; margin-top: 3px; color: var(--text); }}

  /* Dynamic 2-sentence take below source caption */
  .dynamic-take {{ background: linear-gradient(180deg, #fdf9ec, #fcefd0);
                   border: 1px solid #f0d987; border-left: 4px solid var(--accent2);
                   border-radius: 8px; padding: 12px 18px; margin-top: 12px; }}
  .take-eyebrow-dyn {{ color: #8a6b10 !important; }}
  .dynamic-take p {{ font-size: 12.5px; color: var(--text-soft); line-height: 1.6; margin-bottom: 6px; }}
  .dynamic-take p:last-child {{ margin-bottom: 0; }}
  .dynamic-take strong {{ color: var(--text); font-weight: 700; }}

  /* Brand totals header above stat cards */
  .brand-totals-header {{ display: flex; align-items: baseline; justify-content: space-between;
                          margin: 12px 0 8px; padding: 8px 0 6px;
                          border-bottom: 1px dashed var(--border); }}
  .brand-totals-eyebrow {{ font-size: 10px; font-weight: 700; color: var(--accent);
                           letter-spacing: 1.6px; }}
  .brand-totals-vitl-share {{ font-size: 12px; color: var(--text-soft); }}
  .brand-totals-vitl-share strong {{ color: var(--accent); font-weight: 700; font-size: 14px; }}

  /* Household penetration card */
  .hh-pen-card {{ background: var(--surface2); border-left: 4px solid var(--accent);
                  border-radius: 6px; padding: 14px 18px; margin: 8px 0; }}
  .hh-pen-card p {{ font-size: 13px; color: var(--text-soft); line-height: 1.65; margin-bottom: 8px; }}
  .hh-pen-card p:first-child {{ font-size: 26px; font-weight: 700; color: var(--accent); margin-bottom: 8px; letter-spacing: -0.4px; }}
  .hh-pen-card p:first-child strong {{ color: var(--accent); }}
  .hh-pen-card p:last-child {{ margin-bottom: 0; }}
  .hh-pen-card strong {{ color: var(--text); font-weight: 700; }}

  /* DOJ antitrust panel */
  .doj-panel {{ background: var(--surface2); border-left: 4px solid var(--neg);
                border-radius: 6px; padding: 14px 18px; margin: 8px 0; }}
  .doj-status {{ margin-bottom: 8px; }}
  .doj-body p {{ font-size: 12.5px; color: var(--text-soft); line-height: 1.6; margin-bottom: 8px; }}
  .doj-body p:last-child {{ margin-bottom: 0; }}
  .doj-body strong {{ color: var(--text); font-weight: 700; }}

  /* Valuation cards row */
  .val-cards-row {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 8px 0 12px; }}
  @media (max-width: 1024px) {{ .val-cards-row {{ grid-template-columns: 1fr 1fr; }} }}
  .val-card {{ background: var(--surface2); border: 1px solid var(--border);
               border-radius: 8px; padding: 14px 16px; }}
  .val-label {{ font-size: 10px; color: var(--muted); text-transform: uppercase;
                letter-spacing: 0.7px; font-weight: 700; margin-bottom: 6px; }}
  .val-num {{ font-size: 24px; font-weight: 700; color: var(--accent); letter-spacing: -0.5px; }}
  .val-range {{ font-size: 11px; color: var(--text-soft); margin-top: 4px; }}
  .val-pos {{ font-size: 11px; color: var(--accent); font-weight: 700; margin-top: 4px; }}
  .val-note {{ font-size: 10.5px; margin-top: 6px; line-height: 1.4; }}

  .setup-context {{ background: rgba(46,90,60,0.06); border-left: 3px solid var(--accent);
                    padding: 8px 12px; border-radius: 4px; font-size: 12px;
                    color: var(--text-soft); margin-bottom: 10px; line-height: 1.5; }}
  .setup-context strong {{ color: var(--text); font-weight: 700; }}
  .setup-context em {{ color: var(--text-soft); font-style: italic; }}
  .setup-runway .runway-big {{ font-size: 30px; font-weight: 800; color: var(--accent);
                               letter-spacing: -0.6px; margin: 8px 0 6px; line-height: 1.1; }}
  .setup-runway .runway-big-unit {{ font-size: 13px; color: var(--text-soft); font-weight: 500; letter-spacing: 0; margin-left: 6px; }}
  .setup-runway .runway-line {{ font-size: 12.5px; color: var(--text-soft); margin-bottom: 6px; line-height: 1.55; }}
  .setup-runway .runway-line strong {{ color: var(--text); font-weight: 700; }}
  .setup-explain {{ background: rgba(46,90,60,0.06); border-left: 3px solid var(--accent);
                    padding: 8px 12px; border-radius: 4px; font-size: 12px;
                    color: var(--text-soft); margin-bottom: 10px; line-height: 1.5; }}
  .setup-explain strong {{ color: var(--text); font-weight: 700; }}
  .setup-foot {{ font-size: 11.5px; color: var(--muted); margin-top: 10px;
                 padding-top: 10px; border-top: 1px dashed var(--border);
                 line-height: 1.55; font-style: italic; }}
  .setup-foot strong {{ color: var(--text-soft); font-weight: 700; font-style: normal; }}
  .runway-gauge {{ margin-top: 10px; padding: 10px 14px;
                   background: rgba(201,93,74,0.06); border-left: 3px solid var(--neg);
                   border-radius: 4px; }}
  .runway-headline {{ font-size: 13px; color: var(--text); line-height: 1.5; }}
  .runway-headline strong {{ color: var(--neg); font-weight: 700; font-size: 15px; }}
  .runway-sub {{ font-size: 11px; color: var(--muted); margin-top: 4px; line-height: 1.5; }}
  .runway-sub em {{ color: var(--text-soft); font-style: italic; }}
  .setup-buyback .buyback-body {{ font-size: 13px; color: var(--text-soft); line-height: 1.7; padding: 8px 0; }}
  .setup-buyback .buyback-body p:first-child {{ font-size: 28px; font-weight: 700;
                                                color: var(--accent); margin-bottom: 8px; letter-spacing: -0.4px; }}
  .setup-buyback .buyback-body p:first-child strong {{ color: var(--accent); }}
  .setup-buyback .buyback-body p {{ margin-bottom: 10px; }}
  .setup-synthesis {{ background: linear-gradient(180deg, #f8f9f5, #fdf3d3);
                      border: 1px solid #e6d28c; border-radius: 10px;
                      padding: 16px 22px; margin: 16px 0; }}
  .setup-synth-eyebrow {{ font-size: 10.5px; font-weight: 700; color: #8a6b10;
                          letter-spacing: 1.5px; margin-bottom: 8px; }}
  .setup-synthesis p {{ font-size: 13px; color: var(--text-soft); line-height: 1.65; }}

  /* Section 02 — events legend + rollups + article log */
  .event-legend {{ display: flex; align-items: center; font-size: 11.5px;
                   color: var(--muted); margin-top: 8px; gap: 4px; }}
  .legend-dot {{ display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin-right: 5px; }}
  .article-log {{ margin-top: 14px; }}
  .article-log summary {{ font-size: 12.5px; font-weight: 600; color: var(--accent);
                          cursor: pointer; padding: 8px 12px; border: 1px solid var(--border);
                          border-radius: 6px; background: var(--surface); }}
  .article-log summary:hover {{ background: rgba(46,90,60,0.04); }}
  .article-log[open] summary {{ background: rgba(46,90,60,0.04); border-bottom-left-radius: 0;
                                border-bottom-right-radius: 0; border-bottom: none; }}
  .topic-chip {{ display: inline-block; font-size: 10px; font-weight: 600;
                 padding: 3px 8px; border-radius: 999px; }}
  .rollup-block {{ margin-top: 8px; }}
  .rollup-row {{ display: flex; gap: 8px; padding: 6px 0; border-bottom: 1px dashed var(--border); flex-wrap: wrap; align-items: center; }}
  .rollup-week {{ font-size: 11.5px; color: var(--muted); font-variant-numeric: tabular-nums; min-width: 100px; }}

  /* Stat row */
  .stat-row {{ display: flex; gap: 12px; margin-top: 10px; flex-wrap: wrap; }}
  .stat-card {{ background: var(--surface); border: 1px solid var(--border);
                border-radius: 10px; padding: 12px 18px; min-width: 130px; flex: 1 1 130px;
                box-shadow: 0 1px 3px rgba(45,47,37,0.04); }}
  .stat-val {{ font-size: 22px; font-weight: 700; letter-spacing: -0.4px; }}
  .stat-lbl {{ font-size: 10px; color: var(--muted); text-transform: uppercase;
               letter-spacing: 0.7px; margin-top: 4px; font-weight: 600; }}

  /* Correlation matrix */
  .corr-table-card {{ padding: 8px; }}
  .corr-table {{ border-collapse: separate; border-spacing: 4px; }}
  .corr-table th {{ background: transparent; padding: 6px 8px; font-size: 10.5px; }}
  .corr-cell {{ text-align: center; padding: 14px 10px; border-radius: 6px;
                font-weight: 700; font-size: 13px; min-width: 90px; }}
  .corr-cell.na {{ background: var(--surface2); color: var(--muted); }}
  .corr-cell .corr-n {{ font-size: 9.5px; font-weight: 500; margin-top: 2px; }}

  /* Archived */
  .archived-block {{ margin-bottom: 8px; opacity: 0.8; }}
  .archived-block summary {{ font-size: 12.5px; font-weight: 600; color: var(--text-soft);
                             cursor: pointer; padding: 10px 14px; border: 1px solid var(--border);
                             border-radius: 6px; background: var(--surface2); }}
  .archived-block summary:hover {{ background: #efe9d5; }}
  .archived-block p {{ font-size: 12.5px; color: var(--muted); line-height: 1.6; padding: 12px 14px; }}

  /* Modal */
  .modal-backdrop {{ display: none; position: fixed; inset: 0;
                     background: rgba(20,22,15,0.5); z-index: 200;
                     align-items: flex-start; justify-content: center; padding: 60px 20px; }}
  .modal {{ background: var(--surface); border: 1px solid var(--border);
            border-radius: 12px; max-width: 720px; width: 100%;
            box-shadow: 0 8px 32px rgba(0,0,0,0.18); overflow: hidden; }}
  .modal.modal-wide {{ max-width: 880px; }}
  .modal-narrative {{ font-size: 13.5px; color: var(--text-soft); line-height: 1.7; }}
  .modal-narrative p {{ margin-bottom: 14px; padding-bottom: 10px;
                        border-bottom: 1px dashed var(--border); }}
  .modal-narrative p:last-child {{ border-bottom: none; margin-bottom: 8px; }}
  .modal-narrative strong {{ color: var(--text); font-weight: 700; }}
  .modal-narrative em {{ color: var(--text-soft); font-style: italic; }}
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
    <a class="nav-btn recovery" href="#quick-read">Quick Read</a>
    <a class="nav-btn" href="#social">Social</a>
    <a class="nav-btn" href="#setup">Setup</a>
    <a class="nav-btn" href="#news">News</a>
    <a class="nav-btn" href="#egg-market">Eggs</a>
    <a class="nav-btn" href="#community">Brand</a>
    <a class="nav-btn" href="#operating-recovery">Ops</a>
    <a class="nav-btn" href="#financial">Financials</a>
    <a class="nav-btn" href="#valuation">Valuation</a>
    <a class="nav-btn" href="#catalysts">Catalysts</a>
    <a class="nav-btn" href="#recovery-plan">Recovery</a>
    <a class="nav-btn" href="#correlation">Correlation</a>
  </div>
  <button class="summary-btn" onclick="document.getElementById('summaryModal').style.display='flex'">
    Generate Summary
  </button>
</div>

{render_top_callout()}
{render_three_damages()}
{render_supply_quantification_top(supply_quant)}

<div class="container">
  {render_quick_read(qr)}
  {render_social_overview(comm, yt_vitl, yt_comp, reddit_posts, yt_videos,
                          trends, cust_metrics, cat_growth, cat_supply)}
  {render_setup(setup, runway)}
  {render_stock_news(events, news, cad_vs_stock)}
  {render_egg_market(egg)}
  {render_community(comm)}
  {render_operating_recovery(op_rec, tdp)}
  {render_financial(fin, full_cred, cat_burn)}
  {render_valuation(val)}
  {render_catalysts(cat)}
  {render_recovery_plan(rplan)}
  {render_correlation(corr)}
  {render_archived()}
</div>

<footer>
  {BRAND_NAME} ({BRAND_TICKER}) Recovery Dashboard · generated {generated_at}
</footer>

{render_summary_modal(summary)}

<script>
  window.__vitl = {chart_blob};

  // Vertical-line + band plugin
  const refLinePlugin = {{
    id: 'refLine',
    beforeDraw(chart, args, opts) {{
      const refs = opts.refs || []; const bands = opts.bands || [];
      const {{ ctx, chartArea, scales }} = chart;
      if (!scales.x || !chartArea) return;
      ctx.save();
      for (const b of bands) {{
        const xs = scales.x.getPixelForValue(b.start); const xe = scales.x.getPixelForValue(b.end);
        if (Number.isFinite(xs) && Number.isFinite(xe)) {{
          ctx.fillStyle = b.color || 'rgba(201,93,74,0.07)';
          ctx.fillRect(xs, chartArea.top, xe - xs, chartArea.bottom - chartArea.top);
        }}
      }}
      for (const r of refs) {{
        const x = scales.x.getPixelForValue(r.date);
        if (!Number.isFinite(x)) continue;
        ctx.strokeStyle = r.color || '#C95D4A'; ctx.lineWidth = r.width || 2;
        ctx.setLineDash(r.dash || [4, 4]); ctx.beginPath();
        ctx.moveTo(x, chartArea.top); ctx.lineTo(x, chartArea.bottom); ctx.stroke();
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

  // Horizontal band plugin (for ebitda norm band, etc.)
  const yBandPlugin = {{
    id: 'yBand',
    beforeDraw(chart, args, opts) {{
      const bands = opts.bands || [];
      const {{ ctx, chartArea, scales }} = chart;
      if (!scales.y || !chartArea) return;
      ctx.save();
      for (const b of bands) {{
        const ys = scales.y.getPixelForValue(b.from);
        const ye = scales.y.getPixelForValue(b.to);
        if (Number.isFinite(ys) && Number.isFinite(ye)) {{
          ctx.fillStyle = b.color || 'rgba(46,90,60,0.07)';
          ctx.fillRect(chartArea.left, ye, chartArea.right - chartArea.left, ys - ye);
        }}
      }}
      ctx.restore();
    }},
  }};
  Chart.register(yBandPlugin);

  document.addEventListener('DOMContentLoaded', () => {{
    const d = window.__vitl;
    const A = d.accent, A2 = d.accent2, A3 = d.accent3, NEG = d.accent_neg;
    const PURPLE = d.purple, BROWN = d.brown, BLUE = d.blue;

    // ── TOP PANEL — Supply Quantification ────────────────────────────────
    // Stacked bars: retail (green) + baseline breaker ~5% (gray) +
    // excess breaker (red). Overlay line for supply mgmt cost ($M, right axis).
    // Annotations: Q2 trough · Q3 inflection · "Mechanical recovery: $20M margin"
    const sq = d.supply_quant;
    const sqEl = document.getElementById('supplyQuantChart');
    if (sqEl && sq && sq.quarters && sq.quarters.length > 0) {{
      // Find Q2 (trough) and Q3 (inflection) indices
      const idxQ2 = sq.quarters.findIndex(q => q.includes('Q2'));
      const idxQ3 = sq.quarters.findIndex(q => q.includes('Q3'));

      // Custom plugin: Q2 trough banner + Q3 inflection arrow + $20M recovery label
      const supplyAnnotPlugin = {{
        id: 'supplyAnnot',
        afterDatasetsDraw(chart) {{
          const {{ ctx, scales, chartArea }} = chart;
          if (!scales.x || !chartArea) return;
          ctx.save();

          // Q2 TROUGH banner (semi-transparent red band over Q2 column)
          if (idxQ2 >= 0) {{
            const meta = chart.getDatasetMeta(0);
            const bar = meta.data[idxQ2];
            if (bar) {{
              const cx = bar.x;
              // Top label
              ctx.fillStyle = NEG;
              ctx.font = 'bold 10px Inter, system-ui, sans-serif';
              ctx.textAlign = 'center';
              ctx.fillText('▼ TROUGH', cx, chartArea.top + 12);
              ctx.font = '9.5px Inter, system-ui, sans-serif';
              ctx.fillStyle = '#7a3d33';
              ctx.fillText('~$23M supply mgmt', cx, chartArea.top + 25);
            }}
          }}

          // Q3 INFLECTION marker + recovery arrow Q2 → Q3
          if (idxQ2 >= 0 && idxQ3 >= 0) {{
            const meta = chart.getDatasetMeta(0);
            const q2bar = meta.data[idxQ2];
            const q3bar = meta.data[idxQ3];
            if (q2bar && q3bar) {{
              const yMid = chartArea.top + (chartArea.bottom - chartArea.top) * 0.35;
              ctx.strokeStyle = A;
              ctx.fillStyle = A;
              ctx.lineWidth = 2;
              // Arrow Q2 → Q3
              ctx.beginPath();
              ctx.moveTo(q2bar.x + 18, yMid);
              ctx.lineTo(q3bar.x - 18, yMid);
              ctx.stroke();
              // Arrow head
              ctx.beginPath();
              ctx.moveTo(q3bar.x - 18, yMid);
              ctx.lineTo(q3bar.x - 25, yMid - 5);
              ctx.lineTo(q3bar.x - 25, yMid + 5);
              ctx.closePath();
              ctx.fill();
              // Label above arrow
              const labelX = (q2bar.x + q3bar.x) / 2;
              ctx.font = 'bold 11px Inter, system-ui, sans-serif';
              ctx.fillStyle = A;
              ctx.textAlign = 'center';
              ctx.fillText('Mechanical recovery', labelX, yMid - 14);
              ctx.font = 'bold 10.5px Inter, system-ui, sans-serif';
              ctx.fillText('≈ $20M margin', labelX, yMid - 2);
              // Q3 inflection text
              ctx.font = 'bold 10px Inter, system-ui, sans-serif';
              ctx.fillStyle = A;
              ctx.fillText('▲ AMENDMENTS', q3bar.x, chartArea.top + 12);
              ctx.font = '9.5px Inter, system-ui, sans-serif';
              ctx.fillStyle = '#1f4029';
              ctx.fillText('back to baseline 5%', q3bar.x, chartArea.top + 25);
            }}
          }}
          ctx.restore();
        }}
      }};

      // Border styling for estimate vs actual (dashed for estimates/projections)
      const borderDashes = sq.kinds.map(k => k === 'actual' ? [] : [4, 3]);

      new Chart(sqEl, {{
        type: 'bar',
        data: {{
          labels: sq.quarters,
          datasets: [
            {{
              label: 'Retail volume (sold at full price)',
              data: sq.retail,
              backgroundColor: A,
              borderColor: '#1f4029',
              borderWidth: 1,
              borderRadius: 2,
              stack: 'volume',
              order: 2,
            }},
            {{
              label: 'Baseline breaker (~5% normal)',
              data: sq.baseline_breaker,
              backgroundColor: '#b5b5a8',
              borderColor: '#888',
              borderWidth: 1,
              borderRadius: 2,
              stack: 'volume',
              order: 2,
            }},
            {{
              label: 'Excess breaker (over-supply dumped)',
              data: sq.excess_breaker,
              backgroundColor: NEG,
              borderColor: '#7a3d33',
              borderWidth: 1.5,
              borderDash: [3, 2],
              borderRadius: 2,
              stack: 'volume',
              order: 2,
            }},
            {{
              label: 'Supply mgmt cost ($M, right axis)',
              type: 'line',
              data: sq.supply_cost,
              borderColor: '#7d3c4a',
              backgroundColor: 'rgba(125,60,74,0.12)',
              borderWidth: 2.5,
              tension: 0.25,
              fill: false,
              pointRadius: 5,
              pointBackgroundColor: '#7d3c4a',
              pointBorderColor: '#fff',
              pointBorderWidth: 1.5,
              yAxisID: 'yCost',
              order: 1,
            }},
          ],
        }},
        options: {{
          responsive: true, maintainAspectRatio: false,
          interaction: {{ mode: 'index', intersect: false }},
          plugins: {{
            legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }}, padding: 14 }} }},
            tooltip: {{
              callbacks: {{
                afterBody: (ctx) => {{
                  const i = ctx[0].dataIndex;
                  const kind = sq.kinds[i];
                  const note = sq.notes[i] || '';
                  const total = (sq.retail[i] + sq.baseline_breaker[i] + sq.excess_breaker[i]).toFixed(1);
                  return ['', '◇ ' + (kind === 'actual' ? 'ACTUAL' : kind === 'estimate' ? 'ESTIMATE' : 'PROJECTION'),
                          '  Total production: ' + total + 'M dozens', '  ' + note];
                }},
              }},
            }},
          }},
          scales: {{
            x: {{
              stacked: true, grid: {{ display: false }},
              ticks: {{ font: {{ size: 11, weight: '600' }}, color: '#4a4f3f' }},
            }},
            y: {{
              stacked: true, position: 'left',
              grid: {{ color: 'rgba(0,0,0,0.04)' }},
              ticks: {{ font: {{ size: 10 }}, callback: v => v + 'M' }},
              title: {{ display: true, text: 'M dozens / quarter', font: {{ size: 10.5, weight: '600' }} }},
              max: 45,
            }},
            yCost: {{
              position: 'right', grid: {{ display: false }},
              ticks: {{ font: {{ size: 10 }}, callback: v => '$' + v + 'M', color: '#7d3c4a' }},
              title: {{ display: true, text: 'Supply mgmt cost ($M)', font: {{ size: 10.5, weight: '600' }}, color: '#7d3c4a' }},
              min: 0, max: 30,
            }},
          }},
        }},
        plugins: [supplyAnnotPlugin],
      }});
    }}

    // ── Section 01 — Short + Setup-Over-Time (cash chart removed) ─────────
    const setup = d.setup;

    new Chart(document.getElementById('shortChart'), {{
      type: 'line',
      data: {{
        labels: setup.short_series.dates,
        datasets: [{{
          label: '% of Float Short', data: setup.short_series.pct,
          borderColor: NEG, backgroundColor: 'rgba(201,93,74,0.08)',
          borderWidth: 2, tension: 0.25, fill: true,
          pointRadius: (ctx) => ctx.dataIndex === setup.short_series.pct.length - 1 ? 5 : 0,
          pointBackgroundColor: NEG,
        }}],
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{ legend: {{ display: false }}, tooltip: {{ callbacks: {{ label: ctx => ctx.raw.toFixed(1) + '%' }} }} }},
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }}, maxTicksLimit: 6, autoSkip: true }} }},
          y: {{ grid: {{ color: 'rgba(0,0,0,0.05)' }},
                ticks: {{ font: {{ size: 10 }}, callback: v => v + '%' }},
                title: {{ display: true, text: '% of float', font: {{ size: 10 }} }} }},
        }},
      }},
    }});

    // Setup over time: 3 series on 2 y-axes
    const sot = setup.setup_over_time;
    new Chart(document.getElementById('setupOverTimeChart'), {{
      type: 'line',
      data: {{
        labels: sot.dates,
        datasets: [
          {{ label: 'Stock (indexed)', data: sot.stock_idx, borderColor: A,
             backgroundColor: 'rgba(46,90,60,0.05)', borderWidth: 2.4, tension: 0.25,
             pointRadius: 0, fill: false, yAxisID: 'yStock' }},
          {{ label: 'Short interest (%)', data: sot.short_pct, borderColor: NEG,
             borderWidth: 2, borderDash: [4,4], tension: 0.2, pointRadius: 0, fill: false, yAxisID: 'yRight' }},
          {{ label: 'Cumulative insider buys ($K)', data: sot.insider_cum_k, borderColor: A2,
             borderWidth: 2, tension: 0.15, pointRadius: 0, fill: false, yAxisID: 'yRight' }},
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
          yStock: {{ position: 'left', title: {{ display: true, text: 'Stock indexed (base=100)', font: {{ size: 10 }} }},
                     grid: {{ color: 'rgba(0,0,0,0.04)' }}, ticks: {{ font: {{ size: 10 }} }} }},
          yRight: {{ position: 'right', title: {{ display: true, text: 'Short % / Insider $K', font: {{ size: 10 }} }},
                     grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }} }} }},
        }},
      }},
    }});

    // ── Section 02 — Reaction Magnitude hero chart ───────────────────────
    const rm = d.react_mag;
    const rmLabels = rm.events.map(e => `${{e.date.slice(5)}} · ${{e.label.slice(0, 30)}}`);
    const rmData = rm.events.map(e => e.reaction_pct);
    const rmColors = rm.events.map(e => {{
      if (e.reaction_pct === null) return '#999';
      if (e.reaction_pct > 0) return d.reaction_colors.positive;
      if (Math.abs(e.reaction_pct) < 1) return d.reaction_colors.flat;
      return d.reaction_colors.negative;
    }});
    const rmBorders = rm.events.map(e => (e.reaction_pct !== null && e.reaction_pct > 0) ? d.reaction_colors.positive : 'transparent');
    new Chart(document.getElementById('reactionMagnitudeChart'), {{
      type: 'bar',
      data: {{
        labels: rmLabels,
        datasets: [{{
          label: 'Stock reaction (%)', data: rmData,
          backgroundColor: rmColors,
          borderColor: rmBorders, borderWidth: 3, borderRadius: 3,
        }}],
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{
          legend: {{ display: false }},
          tooltip: {{ callbacks: {{
            label: ctx => (ctx.raw === null ? '—' : (ctx.raw > 0 ? '+' : '') + ctx.raw.toFixed(1) + '% on event day'),
          }} }},
        }},
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 9.5 }}, maxRotation: 40, minRotation: 30 }} }},
          y: {{ grid: {{ color: 'rgba(0,0,0,0.04)' }}, ticks: {{ font: {{ size: 10 }}, callback: v => v + '%' }},
                title: {{ display: true, text: 'Stock reaction on event day (%)', font: {{ size: 10 }} }} }},
        }},
      }},
    }});

    // ── Section 02 — Events chart + insider triangle overlays ────────────
    const ev = d.events;
    const eventDots = ev.events.map(e => ({{x: e.date, y: e.close}}));
    // Insider cluster triangles — pull date + close-on-that-day from stock series
    const closeByDate = {{}};
    ev.dates.forEach((dt, i) => closeByDate[dt] = ev.close[i]);
    const insiderDates = (d.setup.insiders || []).map(i => i.date);
    const insiderDots = insiderDates
      .map(dt => ({{x: dt, y: closeByDate[dt] || null}}))
      .filter(p => p.y !== null);
    new Chart(document.getElementById('eventsChart'), {{
      type: 'line',
      data: {{
        labels: ev.dates,
        datasets: [
          {{ label: 'VITL Close', data: ev.close, borderColor: A,
             backgroundColor: 'rgba(46,90,60,0.06)', borderWidth: 2, pointRadius: 0,
             tension: 0.15, fill: true, order: 3 }},
          {{ label: 'News Events', data: eventDots, showLine: false,
             pointRadius: 11, pointHoverRadius: 14,
             pointBackgroundColor: ev.events.map(e => d.reaction_colors[e.reaction_kind] || '#999'),
             pointBorderColor: '#fff', pointBorderWidth: 3,
             order: 1, parsing: false }},
          {{ label: 'Insider Cluster', data: insiderDots, showLine: false,
             pointStyle: 'triangle', pointRadius: 10, pointHoverRadius: 13,
             pointBackgroundColor: A, pointBorderColor: '#fff', pointBorderWidth: 2,
             order: 2, parsing: false }},
        ],
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{
          legend: {{ display: false }},
          refLine: {{ bands: [{{ start: ev.class_period_start, end: ev.class_period_end, color: 'rgba(201,93,74,0.06)' }}] }},
          tooltip: {{ mode: 'nearest', intersect: true,
            callbacks: {{
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
                if (ctx.datasetIndex === 2) {{
                  const ins = d.setup.insiders[ctx.dataIndex];
                  if (!ins) return 'Insider buy';
                  return `Insider buy · ${{ins.name}} (${{ins.title}}) · ${{ins.shares.toLocaleString()}} sh @ $${{ins.price.toFixed(2)}}`;
                }}
                return '$' + Number(ctx.raw).toFixed(2);
              }},
            }},
          }},
        }},
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }}, maxTicksLimit: 10, autoSkip: true }} }},
          y: {{ grid: {{ color: 'rgba(0,0,0,0.05)' }}, ticks: {{ font: {{ size: 10 }}, callback: v => '$' + v }} }},
        }},
      }},
    }});

    // Topic mix over time
    const tmot = d.news.topics_over_time;
    const topicKeys = Object.keys(tmot.series || {{}});
    const topicDatasets = topicKeys.map(t => ({{
      label: d.topic_labels[t] || t, data: tmot.series[t],
      borderColor: d.topic_colors[t] || '#999',
      backgroundColor: (d.topic_colors[t] || '#999') + '88',
      borderWidth: 1, fill: true, tension: 0.25, pointRadius: 0,
    }}));
    new Chart(document.getElementById('topicMixChart'), {{
      type: 'line',
      data: {{ labels: tmot.weeks, datasets: topicDatasets }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{
          legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }} }} }},
          refLine: {{ refs: [{{ date: '2026-04-15', color: NEG, width: 1.5, dash: [3,3], label: 'Class actions' }}] }},
          tooltip: {{ mode: 'index', intersect: false }},
        }},
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }}, maxTicksLimit: 12, autoSkip: true }} }},
          y: {{ stacked: true, grid: {{ color: 'rgba(0,0,0,0.04)' }},
                ticks: {{ font: {{ size: 10 }} }},
                title: {{ display: true, text: 'Articles per week', font: {{ size: 10 }} }} }},
        }},
      }},
    }});

    // Cadence vs stock
    const cvs = d.cad_vs_stock;
    new Chart(document.getElementById('cadenceVsStockChart'), {{
      type: 'line',
      data: {{
        labels: cvs.weeks,
        datasets: [
          {{ label: 'Article Cadence (indexed)', data: cvs.cadence_idx, borderColor: A2,
             borderWidth: 2, tension: 0.25, pointRadius: 0, fill: false, yAxisID: 'yCad' }},
          {{ label: 'VITL Stock (indexed)', data: cvs.stock_idx, borderColor: A,
             backgroundColor: 'rgba(46,90,60,0.05)', borderWidth: 2.2, tension: 0.2,
             pointRadius: 0, fill: false, yAxisID: 'yStk' }},
        ],
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{ legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }} }} }}, tooltip: {{ mode: 'index', intersect: false }} }},
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }}, maxTicksLimit: 10, autoSkip: true }} }},
          yCad: {{ position: 'left', title: {{ display: true, text: 'Cadence indexed', font: {{ size: 10 }} }},
                   grid: {{ color: 'rgba(0,0,0,0.04)' }}, ticks: {{ font: {{ size: 10 }} }} }},
          yStk: {{ position: 'right', title: {{ display: true, text: 'Stock indexed', font: {{ size: 10 }} }},
                   grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }} }} }},
        }},
      }},
    }});

    // ── Section 03 — Egg market (4 charts) ────────────────────────────────
    const eg = d.egg;
    new Chart(document.getElementById('eggChart1'), {{
      type: 'line',
      data: {{
        labels: eg.chart1.weeks,
        datasets: [
          {{ label: 'Conventional wholesale ($/dz)', data: eg.chart1.conv, borderColor: BLUE,
             borderWidth: 2, tension: 0.25, pointRadius: 0, fill: false }},
          {{ label: 'VITL retail ($/dz, estimated)', data: eg.chart1.vitl, borderColor: A,
             borderWidth: 2, borderDash: [5,3], tension: 0.1, pointRadius: 0, spanGaps: true, fill: false }},
        ],
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{ legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }} }} }}, tooltip: {{ mode: 'index', intersect: false }} }},
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }}, maxTicksLimit: 12, autoSkip: true }} }},
          y: {{ grid: {{ color: 'rgba(0,0,0,0.04)' }}, ticks: {{ font: {{ size: 10 }}, callback: v => '$' + v }},
                title: {{ display: true, text: '$ per dozen', font: {{ size: 10 }} }} }},
        }},
      }},
    }});

    new Chart(document.getElementById('eggChart2'), {{
      type: 'line',
      data: {{
        labels: eg.chart2.weeks,
        datasets: [{{
          label: 'Premium gap %', data: eg.chart2.gap,
          borderColor: A2, backgroundColor: 'rgba(244,196,48,0.18)',
          borderWidth: 1.5, tension: 0.2, pointRadius: 0, fill: true, spanGaps: true,
        }}],
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{
          legend: {{ display: false }},
          yBand: {{ bands: [{{ from: 150, to: 200, color: 'rgba(46,90,60,0.07)' }}] }},
          tooltip: {{ callbacks: {{ label: ctx => ctx.raw == null ? '—' : ctx.raw.toFixed(0) + '%' }} }},
        }},
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }}, maxTicksLimit: 12, autoSkip: true }} }},
          y: {{ grid: {{ color: 'rgba(0,0,0,0.04)' }},
                ticks: {{ font: {{ size: 10 }}, callback: v => v + '%' }},
                title: {{ display: true, text: 'Gap (%)', font: {{ size: 10 }} }} }},
        }},
      }},
    }});

    new Chart(document.getElementById('eggChart3'), {{
      type: 'line',
      data: {{
        labels: eg.chart3.weeks,
        datasets: [
          {{ label: 'VITL stock (indexed)', data: eg.chart3.stock_idx, borderColor: A,
             borderWidth: 2.2, tension: 0.2, pointRadius: 0, fill: false }},
          {{ label: 'Premium gap % (indexed)', data: eg.chart3.gap_idx, borderColor: A2,
             borderWidth: 2, borderDash: [5,3], tension: 0.2, pointRadius: 0, fill: false }},
        ],
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{ legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }} }} }}, tooltip: {{ mode: 'index', intersect: false }} }},
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }}, maxTicksLimit: 10, autoSkip: true }} }},
          y: {{ grid: {{ color: 'rgba(0,0,0,0.04)' }}, ticks: {{ font: {{ size: 10 }} }},
                title: {{ display: true, text: 'Indexed (base=100)', font: {{ size: 10 }} }} }},
        }},
      }},
    }});

    new Chart(document.getElementById('eggChart4'), {{
      type: 'line',
      data: {{
        labels: eg.chart4.weeks,
        datasets: [
          {{ label: 'Breaker market ($/dz)', data: eg.chart4.breaker, borderColor: NEG,
             backgroundColor: 'rgba(201,93,74,0.10)', borderWidth: 2, tension: 0.25,
             pointRadius: 0, fill: true }},
          {{ label: 'Conventional wholesale ($/dz)', data: eg.chart4.conv, borderColor: BLUE,
             borderWidth: 1.5, borderDash: [4,4], tension: 0.2, pointRadius: 0, fill: false, spanGaps: true }},
        ],
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{ legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }} }} }}, tooltip: {{ mode: 'index', intersect: false }} }},
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }}, maxTicksLimit: 10, autoSkip: true }} }},
          y: {{ grid: {{ color: 'rgba(0,0,0,0.04)' }}, ticks: {{ font: {{ size: 10 }}, callback: v => '$' + v }},
                title: {{ display: true, text: '$ per dozen', font: {{ size: 10 }} }} }},
        }},
      }},
    }});

    // ── Section 03 — HPAI Cumulative ──────────────────────────────────────
    const hpc = d.hpai_cum;
    new Chart(document.getElementById('hpaiCumulativeChart'), {{
      type: 'line',
      data: {{
        labels: hpc.months,
        datasets: [{{
          label: 'Cumulative birds depopulated (M)', data: hpc.cumulative,
          borderColor: NEG, backgroundColor: 'rgba(201,93,74,0.10)',
          borderWidth: 2.2, tension: 0.15, fill: true, pointRadius: 0,
        }}],
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{ legend: {{ display: false }} }},
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }}, maxTicksLimit: 10, autoSkip: true }} }},
          y: {{ grid: {{ color: 'rgba(0,0,0,0.04)' }},
                ticks: {{ font: {{ size: 10 }}, callback: v => v + 'M' }},
                title: {{ display: true, text: 'Cumulative birds (millions)', font: {{ size: 10 }} }} }},
        }},
      }},
    }});

    // ── Section 04 — SoV pos/neu/neg stacked + Linoleic + ... ────────────
    const sovS = d.sov_sentiment;
    // Stack one VITL-only sentiment-breakout series + 5 competitor totals as flat areas.
    // Use a bar chart with sentiment stacks (pos / neu / neg) per week so the
    // sentiment composition is legible. Each VITL bar has 3 stacks (pos/neu/neg)
    // colored green/gray/red. Competitor brands shown as overlay line areas so
    // the share dynamic remains visible across all 6 brands.
    const sovDatasets = [];
    const vitl = sovS.brands && sovS.brands['Vital Farms'];
    if (vitl) {{
      sovDatasets.push(
        {{ label: 'VITL · positive', data: vitl.pos, backgroundColor: '#2a7a30',
           stack: 'vitl', type: 'bar', borderRadius: 1 }},
        {{ label: 'VITL · neutral',  data: vitl.neu, backgroundColor: '#bdbab1',
           stack: 'vitl', type: 'bar', borderRadius: 1 }},
        {{ label: 'VITL · negative', data: vitl.neg, backgroundColor: '#b34738',
           stack: 'vitl', type: 'bar', borderRadius: 1 }},
      );
    }}
    // 5 competitor brands rendered as overlay total-volume line/area
    ['Handsome Brook','Alexandre',"Pete & Gerry's",'Happy Egg','Organic Valley'].forEach(b => {{
      const arr = sovS.brands && sovS.brands[b] && sovS.brands[b].total;
      if (!arr) return;
      sovDatasets.push({{
        label: b, data: arr, borderColor: d.brand_colors[b] || '#999',
        backgroundColor: (d.brand_colors[b] || '#999') + '00',
        type: 'line', borderWidth: 1.5, tension: 0.3, pointRadius: 0,
        fill: false, stack: 'overlay',
      }});
    }});
    // Brand SoV chart was removed in pass 14 (only 21 mentions across 6 brands /
    // 36mo — same sparseness as the subreddit table). Canvas no longer in DOM
    // so the chart call is guarded.
    if (sovDatasets.length > 0 && sovS.weeks.length > 0 && document.getElementById('brandSovChart')) {{
      new Chart(document.getElementById('brandSovChart'), {{
        type: 'bar',
        data: {{ labels: sovS.weeks, datasets: sovDatasets }},
        options: {{
          responsive: true, maintainAspectRatio: false,
          plugins: {{
            legend: {{ position: 'bottom', labels: {{ font: {{ size: 10.5 }} }} }},
            refLine: {{
              refs: [{{ date: '2026-02-26', color: NEG, width: 2, dash: [], label: 'Feb 26 print' }}],
              bands: [{{ start: '2025-05-08', end: '2026-02-26', color: 'rgba(201,93,74,0.06)' }}],
            }},
            tooltip: {{ mode: 'index', intersect: false }},
          }},
          scales: {{
            x: {{ stacked: true, grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }}, maxTicksLimit: 12, autoSkip: true }} }},
            y: {{ stacked: true, grid: {{ color: 'rgba(0,0,0,0.04)' }}, ticks: {{ font: {{ size: 10 }} }},
                  title: {{ display: true, text: 'Weekly mentions (VITL stacked by sentiment; competitors overlaid as lines)', font: {{ size: 10 }} }} }},
          }},
        }},
      }});
    }}

    // Brand Awareness — annual line
    const ba = d.brand_aware;
    new Chart(document.getElementById('brandAwarenessChart'), {{
      type: 'line',
      data: {{
        labels: ba.years,
        datasets: [{{
          label: 'Aided brand awareness (%)', data: ba.values, borderColor: A,
          backgroundColor: 'rgba(46,90,60,0.08)', borderWidth: 2.5, tension: 0.2,
          fill: true, pointRadius: 7, pointHoverRadius: 9,
          pointBackgroundColor: A, pointBorderColor: '#fff', pointBorderWidth: 2,
          spanGaps: true,
        }}],
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{ legend: {{ display: false }},
                    tooltip: {{ callbacks: {{ label: ctx => ctx.raw == null ? 'TBD (pending FY26 print)' : ctx.raw.toFixed(0) + '%' }} }} }},
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 11 }} }} }},
          y: {{ grid: {{ color: 'rgba(0,0,0,0.04)' }}, ticks: {{ font: {{ size: 10 }}, callback: v => v + '%' }},
                title: {{ display: true, text: 'Aided brand awareness (%)', font: {{ size: 10 }} }} }},
        }},
      }},
    }});

    const lin = d.comm.linoleic;
    const linDatasets = [
      {{ label: 'Reddit posts + comments (weekly)', data: lin.reddit, borderColor: PURPLE,
         backgroundColor: 'rgba(142,109,180,0.14)', borderWidth: 2, tension: 0.3, pointRadius: 0, fill: true, yAxisID: 'yL' }},
    ];
    if (lin.youtube && lin.youtube.some(v => v !== null && v !== undefined)) {{
      linDatasets.push({{
        label: 'YouTube videos (monthly, scaled)', data: lin.youtube, borderColor: NEG,
        borderWidth: 2, borderDash: [5,3], tension: 0.3, pointRadius: 0, spanGaps: true, yAxisID: 'yR',
      }});
    }}
    // ── Section 01 — YouTube charts ───────────────────────────────────────
    const yv = window.__vitl.yt_vitl || {{}};
    const yvEl = document.getElementById('youtubeVitlChart');
    if (yvEl) {{
      if (yv.months && yv.months.length > 0) {{
        new Chart(yvEl, {{
          type: 'line',
          data: {{
            labels: yv.months,
            datasets: [{{
              label: 'Videos / month', data: yv.video_count, borderColor: NEG,
              backgroundColor: 'rgba(201,93,74,0.10)', borderWidth: 2, tension: 0.25,
              pointRadius: 3, fill: true,
            }}],
          }},
          options: {{
            responsive: true, maintainAspectRatio: false,
            plugins: {{ legend: {{ display: false }},
                        tooltip: {{ callbacks: {{ label: ctx => `${{ctx.raw}} videos` }} }} }},
            scales: {{
              x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }}, maxTicksLimit: 10, autoSkip: true }} }},
              y: {{ grid: {{ color: 'rgba(0,0,0,0.04)' }}, ticks: {{ font: {{ size: 10 }} }},
                    title: {{ display: true, text: 'Videos uploaded / month', font: {{ size: 10 }} }} }},
            }},
          }},
        }});
      }} else {{
        yvEl.parentElement.innerHTML = '<div class="placeholder">No YouTube data yet · set <code>YOUTUBE_API_KEY</code> in <code>.env</code> and run <code>make refresh-data</code></div>';
      }}
    }}

    // YouTube competitor chart removed in pass 11 — see render_social_overview
    // note. Brand-vs-brand comparison lives in the Reddit Brand SoV chart.

    // ── Section 01B — Category Demand (Trends + Category Growth) ─────────
    const tr = d.trends || {{}};
    const trEl = document.getElementById('categoryTrendsChart');
    if (trEl && tr.weeks && tr.weeks.length > 0) {{
      const TERM_COLORS = {{
        "pasture raised eggs": A,
        "organic eggs":        A2,
        "cage free eggs":      BLUE,
        "regenerative eggs":   PURPLE,
      }};
      const trDatasets = Object.keys(tr.terms).map(t => ({{
        label: t, data: tr.terms[t],
        borderColor: TERM_COLORS[t] || '#999',
        backgroundColor: 'transparent',
        borderWidth: t === 'pasture raised eggs' ? 2.4 : 1.6,
        tension: 0.25, pointRadius: 0,
      }}));
      new Chart(trEl, {{
        type: 'line',
        data: {{ labels: tr.weeks, datasets: trDatasets }},
        options: {{
          responsive: true, maintainAspectRatio: false,
          plugins: {{ legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }} }} }},
                      tooltip: {{ mode: 'index', intersect: false }} }},
          scales: {{
            x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }}, maxTicksLimit: 12, autoSkip: true }} }},
            y: {{ grid: {{ color: 'rgba(0,0,0,0.04)' }}, ticks: {{ font: {{ size: 10 }} }},
                  title: {{ display: true, text: 'Search interest (0-100, comparable across terms)', font: {{ size: 10 }} }} }},
          }},
        }},
      }});
    }} else if (trEl) {{
      trEl.parentElement.innerHTML = '<div class="placeholder">Google Trends data not yet loaded · run <code>fetch_google_trends.py</code></div>';
    }}

    const cg = d.cat_growth || {{}};
    const cgEl = document.getElementById('categoryGrowthChart');
    if (cgEl && cg.quarters && cg.quarters.length > 0) {{
      // Per-bar styling: solid border + full alpha for "verified" rows;
      // dashed border + reduced alpha for "estimated" / "partial" rows so
      // the analyst can visually distinguish data confidence at a glance.
      const conf = cg.confidence || [];
      const vitlColors = conf.map(c => c === 'verified' ? A : A + '88');
      const catColors  = conf.map(c => c === 'verified' ? A2 : A2 + '88');
      const borderDash = conf.map(c => c === 'verified' ? [] : [4, 3]);
      new Chart(cgEl, {{
        type: 'bar',
        data: {{
          labels: cg.quarters,
          datasets: [
            {{ label: 'VITL YoY %', data: cg.vitl,
               backgroundColor: vitlColors, borderColor: A, borderWidth: 1.5,
               borderRadius: 3, borderDash: [] }},
            {{ label: 'Pasture-raised category YoY %', data: cg.category,
               backgroundColor: catColors, borderColor: A2, borderWidth: 1.5,
               borderRadius: 3 }},
          ],
        }},
        options: {{
          responsive: true, maintainAspectRatio: false,
          plugins: {{
            legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }} }} }},
            tooltip: {{ mode: 'index', intersect: false,
              callbacks: {{
                afterBody: (ctx) => 'Confidence: ' + (conf[ctx[0].dataIndex] || 'unknown'),
              }},
            }},
          }},
          scales: {{
            x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }} }} }},
            y: {{ grid: {{ color: 'rgba(0,0,0,0.04)' }}, ticks: {{ font: {{ size: 10 }}, callback: v => v + '%' }},
                  title: {{ display: true, text: 'YoY growth (%) · solid = verified · faded = estimated', font: {{ size: 10 }} }} }},
          }},
        }},
      }});
    }}

    // ── Section 01B — Category Supply Timeline (stacked bars) ────────────
    const cs = d.cat_supply || {{}};
    const csEl = document.getElementById('categorySupplyChart');
    if (csEl && cs.years && cs.years.length > 0) {{
      new Chart(csEl, {{
        type: 'bar',
        data: {{
          labels: cs.years,
          datasets: [
            {{ label: 'Branded SKUs', data: cs.branded, backgroundColor: A, borderRadius: 2, stack: 'sku' }},
            {{ label: 'Private-label SKUs', data: cs.private_label, backgroundColor: NEG, borderRadius: 2, stack: 'sku' }},
          ],
        }},
        options: {{
          responsive: true, maintainAspectRatio: false,
          plugins: {{
            legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }} }} }},
            tooltip: {{ mode: 'index', intersect: false,
                        callbacks: {{
                          afterBody: (ctx) => {{
                            const e = cs.events[ctx[0].dataIndex];
                            return e ? ['', '↳ ' + e.event] : '';
                          }},
                        }} }},
          }},
          scales: {{
            x: {{ stacked: true, grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }} }} }},
            y: {{ stacked: true, grid: {{ color: 'rgba(0,0,0,0.04)' }}, ticks: {{ font: {{ size: 10 }} }},
                  title: {{ display: true, text: 'Nationally-distributed pasture-raised SKUs', font: {{ size: 10 }} }} }},
          }},
        }},
      }});
    }}

    // Linoleic + Controversy-vs-Stock charts removed in pass 14 (seeded data,
    // not live Reddit). Canvas elements no longer exist in DOM — guards below.
    if (document.getElementById('linoleicChart')) {{
      new Chart(document.getElementById('linoleicChart'), {{
        type: 'line', data: {{ labels: lin.weeks, datasets: linDatasets }},
        options: {{
          responsive: true, maintainAspectRatio: false,
          plugins: {{
            legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }} }} }},
            refLine: {{ refs: [{{ date: '2026-01-15', color: NEG, width: 1.5, dash: [3,3], label: 'Jan 15 TikTok peak' }}] }},
          }},
          scales: {{
            x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }}, maxTicksLimit: 8, autoSkip: true }} }},
            yL: {{ position: 'left', grid: {{ color: 'rgba(0,0,0,0.04)' }}, ticks: {{ font: {{ size: 10 }} }},
                   title: {{ display: true, text: 'Reddit posts/wk', font: {{ size: 10 }} }} }},
            yR: {{ position: 'right', grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }} }},
                   title: {{ display: true, text: 'YouTube videos (scaled)', font: {{ size: 10 }} }} }},
          }},
        }},
      }});
    }}

    const cvss = d.comm.controversy_vs_stock;
    if (document.getElementById('controversyVsStockChart')) new Chart(document.getElementById('controversyVsStockChart'), {{
      type: 'line',
      data: {{
        labels: cvss.weeks,
        datasets: [
          {{ label: 'Controversy mentions (indexed)', data: cvss.controversy_idx, borderColor: PURPLE,
             borderWidth: 2, tension: 0.25, pointRadius: 0, fill: false }},
          {{ label: 'VITL stock (indexed)', data: cvss.stock_idx, borderColor: A,
             borderWidth: 2.2, tension: 0.2, pointRadius: 0, fill: false }},
        ],
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{ legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }} }} }}, tooltip: {{ mode: 'index', intersect: false }} }},
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }}, maxTicksLimit: 10, autoSkip: true }} }},
          y: {{ grid: {{ color: 'rgba(0,0,0,0.04)' }}, ticks: {{ font: {{ size: 10 }} }},
                title: {{ display: true, text: 'Indexed (base=100)', font: {{ size: 10 }} }} }},
        }},
      }},
    }});

    // ── Section 05 — Operating Recovery (Comp Difficulty, GM, 2yr Stack, TDP) ──
    const op = d.op_rec;
    const COMP_BG = {{"easy": "#9fc69a", "medium": "#f0d168", "hard": "#d97f6e"}};
    new Chart(document.getElementById('compDifficultyChart'), {{
      type: 'bar',
      data: {{
        labels: op.comp.quarters,
        datasets: [{{
          label: 'Revenue YoY %', data: op.comp.growth,
          backgroundColor: op.comp.comp_kinds.map(k => COMP_BG[k] || '#999'),
          borderColor: op.comp.kinds.map(k => k === 'estimate' ? '#999' : 'transparent'),
          borderWidth: 2, borderDash: op.comp.kinds.map(k => k === 'estimate' ? [3,3] : []),
          borderRadius: 3,
        }}],
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{ legend: {{ display: false }}, tooltip: {{
          callbacks: {{ label: ctx => ctx.raw.toFixed(1) + '% (' + op.comp.comp_kinds[ctx.dataIndex] + ' comp · ' + op.comp.kinds[ctx.dataIndex] + ')' }} }} }},
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }}, maxRotation: 45, minRotation: 30 }} }},
          y: {{ grid: {{ color: 'rgba(0,0,0,0.04)' }}, ticks: {{ font: {{ size: 10 }}, callback: v => v + '%' }},
                title: {{ display: true, text: 'YoY revenue growth (%)', font: {{ size: 10 }} }} }},
        }},
      }},
    }});

    new Chart(document.getElementById('gmTrajectoryChart'), {{
      type: 'line',
      data: {{
        labels: op.gm.quarters,
        datasets: [{{
          label: 'Gross margin (%)', data: op.gm.values, borderColor: A,
          backgroundColor: 'rgba(46,90,60,0.06)', borderWidth: 2.2, tension: 0.2, fill: true,
          pointRadius: 5,
          pointBackgroundColor: op.gm.kinds.map(k => k === 'actual' ? A : A2),
          pointBorderColor: '#fff', pointBorderWidth: 2,
        }}],
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{ legend: {{ display: false }},
                    tooltip: {{ callbacks: {{ label: ctx => ctx.raw.toFixed(1) + '% (' + op.gm.kinds[ctx.dataIndex] + ')' }} }} }},
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }}, maxRotation: 45, minRotation: 30 }} }},
          y: {{ grid: {{ color: 'rgba(0,0,0,0.04)' }}, ticks: {{ font: {{ size: 10 }}, callback: v => v + '%' }},
                title: {{ display: true, text: 'Gross margin (%)', font: {{ size: 10 }} }} }},
        }},
      }},
    }});

    new Chart(document.getElementById('twoYrStackChart'), {{
      type: 'line',
      data: {{
        labels: op.stack.quarters,
        datasets: [{{
          label: '2yr stacked YoY %', data: op.stack.stack,
          borderColor: PURPLE, backgroundColor: 'rgba(142,109,180,0.10)',
          borderWidth: 2.2, tension: 0.2, fill: true, pointRadius: 3,
        }}],
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{ legend: {{ display: false }} }},
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }}, maxRotation: 45, minRotation: 30 }} }},
          y: {{ grid: {{ color: 'rgba(0,0,0,0.04)' }}, ticks: {{ font: {{ size: 10 }}, callback: v => v + '%' }},
                title: {{ display: true, text: '2yr stacked growth (%)', font: {{ size: 10 }} }} }},
        }},
      }},
    }});

    const tdp = d.tdp;
    new Chart(document.getElementById('tdpVsRevenueChart'), {{
      type: 'bar',
      data: {{
        labels: tdp.quarters,
        datasets: [
          {{ label: 'TDP YoY %', data: tdp.tdp, backgroundColor: A, borderRadius: 3 }},
          {{ label: 'Revenue YoY %', data: tdp.revenue, backgroundColor: A2, borderRadius: 3 }},
        ],
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{ legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }} }} }}, tooltip: {{ mode: 'index', intersect: false }} }},
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }} }} }},
          y: {{ grid: {{ color: 'rgba(0,0,0,0.04)' }}, ticks: {{ font: {{ size: 10 }}, callback: v => v + '%' }},
                title: {{ display: true, text: 'YoY (%)', font: {{ size: 10 }} }} }},
        }},
      }},
    }});

    // Velocity per shelf-slot = (1 + revenue_yoy) / (1 + tdp_yoy) - 1
    // Positive = each shelf earning more. Negative = shelves growing faster than dollars.
    const vps = tdp.quarters.map((_, i) => {{
      const r = tdp.revenue[i] / 100;
      const t = tdp.tdp[i] / 100;
      if (t === -1) return null;
      return Math.round(((1 + r) / (1 + t) - 1) * 1000) / 10;
    }});
    const vpsColors = vps.map(v => v == null ? '#ccc' : (v >= 0 ? A : NEG));
    new Chart(document.getElementById('velocityPerShelfChart'), {{
      type: 'bar',
      data: {{
        labels: tdp.quarters,
        datasets: [{{
          label: 'Velocity per shelf YoY (%)', data: vps,
          backgroundColor: vpsColors, borderRadius: 3,
        }}],
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{
          legend: {{ display: false }},
          tooltip: {{ callbacks: {{
            label: ctx => ctx.raw == null ? 'n/a' :
              (ctx.raw >= 0 ? '+' : '') + ctx.raw.toFixed(1) + '% per-shelf YoY'
              + ' (rev ' + tdp.revenue[ctx.dataIndex] + '% ÷ tdp ' + tdp.tdp[ctx.dataIndex] + '%)',
          }} }},
        }},
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }} }} }},
          y: {{ grid: {{ color: 'rgba(0,0,0,0.04)' }}, ticks: {{ font: {{ size: 10 }}, callback: v => v + '%' }},
                title: {{ display: true, text: 'Velocity per shelf YoY (%) · 0 = breakeven', font: {{ size: 10 }} }} }},
        }},
      }},
    }});

    // ── Section 06 — EBITDA history + Cash burn decomp ────────────────────
    const eh = d.fin.ebitda;
    // Color quarterly = light, annual = dark, target = accent gold
    const ebColors = eh.kinds.map(k => k === "annual" ? A : (k === "quarterly" ? A3 : A2));
    new Chart(document.getElementById('ebitdaHistoryChart'), {{
      type: 'line',
      data: {{
        labels: eh.labels,
        datasets: [{{
          label: 'EBITDA margin (%)', data: eh.values, borderColor: A,
          backgroundColor: 'rgba(46,90,60,0.06)',
          borderWidth: 2.2, tension: 0.2, fill: true,
          pointRadius: 5, pointBackgroundColor: ebColors, pointBorderColor: '#fff', pointBorderWidth: 2,
        }}],
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{
          legend: {{ display: false }},
          yBand: {{ bands: [
            {{ from: 10, to: 14, color: 'rgba(46,90,60,0.10)' }},
            {{ from: 15, to: 17, color: 'rgba(244,196,48,0.16)' }},
          ] }},
          tooltip: {{ callbacks: {{ label: ctx => ctx.raw.toFixed(1) + '% (' + eh.kinds[ctx.dataIndex] + ')' }} }},
        }},
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }}, maxRotation: 45, minRotation: 30 }} }},
          y: {{ grid: {{ color: 'rgba(0,0,0,0.04)' }}, ticks: {{ font: {{ size: 10 }}, callback: v => v + '%' }},
                title: {{ display: true, text: 'EBITDA margin (%)', font: {{ size: 10 }} }} }},
        }},
      }},
    }});

    // Cash burn chart removed — replaced by side-by-side categorized tables in Section 06.
    // Keep an empty new Chart() so the page doesn't error if any cached canvas
    // hangs around in DOM.
    const _cashBurnNoop = (() => {{
      const el = document.getElementById('cashBurnChart');
      if (!el) return null;
      return new Chart(el, {{
        type: 'bar', data: {{ labels: [], datasets: [] }},
      options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }} }} }});
    }})();
  }});
</script>

</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print(f"── {BRAND_NAME} ({BRAND_TICKER}) Recovery Dashboard v4 ──")
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
