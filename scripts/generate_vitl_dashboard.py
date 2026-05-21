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
    # Projected Q2 burn estimate — bake in the guided ~$45M from cash_burn_decomp
    projected_q2 = None
    if not d["cash_burn_decomp"].empty:
        q2 = d["cash_burn_decomp"][d["cash_burn_decomp"]["quarter"].astype(str).str.contains("Q2 2026", na=False)]
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
    cash_burn = {"quarters": [], "operations": [], "capex": [], "supply_mgmt": [],
                 "buyback": [], "other": [], "total": []}
    if not cbd.empty:
        cash_burn["quarters"]   = cbd["quarter"].astype(str).tolist()
        cash_burn["operations"] = cbd["operations_m"].astype(float).tolist()
        cash_burn["capex"]      = cbd["capex_m"].astype(float).tolist()
        cash_burn["supply_mgmt"]= cbd["supply_mgmt_m"].astype(float).tolist()
        cash_burn["buyback"]    = cbd["buyback_m"].astype(float).tolist()
        cash_burn["other"]      = cbd["other_m"].astype(float).tolist()
        cash_burn["total"]      = cbd["total_m"].astype(float).tolist()

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


def compute_summary(d, qr, setup, news, egg, fin, corr) -> dict:
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
    return {
        "headline": f"{BRAND_NAME} ({BRAND_TICKER}) — Recovery Signal Dashboard",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "bullets": bullets,
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
               height_class: str = "big") -> str:
    """Render the chrome around a chart canvas with consistent title /
    subtitle / source / y-axis caption / what-to-watch from /reads/."""
    md = load_markdown(read_md_path)
    take_html = (
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
  {take_html}
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


def render_setup(setup: dict) -> str:
    cluster = setup.get("cluster")
    cluster_kpi = (f"{cluster['insiders']} insiders · ${cluster['total_value']:,.0f} "
                   f"cluster {cluster['start']}→{cluster['end']}"
                   if cluster else "no cluster detected")
    cash_change = setup.get("cash_change")
    cash_kpi = (f"${abs(cash_change):.0f}M burned in Q1" if cash_change is not None else "—")
    runway_qs = setup.get("runway_qs"); projected_q2 = setup.get("projected_q2_burn")
    runway_block = ""
    if runway_qs is not None:
        proj_line = (f' · Q2 guided ~${projected_q2:.0f}M → projected cash ~${setup["projected_cash"]:.0f}M'
                     if projected_q2 is not None else "")
        runway_block = (
            f'<div class="runway-gauge">'
            f'<div class="runway-headline">Implied runway: <strong>{runway_qs:.1f} quarters</strong> '
            f'at Q1 burn rate</div>'
            f'<div class="runway-sub">${setup["current_cash"]:.0f}M cash ÷ ${setup["q_burn"]:.0f}M/quarter burn'
            f'{proj_line} · <em>$100M JPM revolver undrawn extends this; not modeled here</em></div>'
            f'</div>'
        )

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

    return f"""
<div class="section-header" id="setup">
  <div class="section-num">SECTION 01</div>
  <div class="section-title">The Setup — Conviction vs Cash</div>
  <div class="section-subtitle">Four panels on one frame · the single binary that breaks or makes the thesis.</div>
</div>

<div class="setup-grid">

  <div class="setup-card">
    <div class="setup-card-header">
      <div class="setup-card-title">Cash Position</div>
      <div class="setup-kpi">{cash_kpi}</div>
    </div>
    <div class="chart-wrap" style="height:200px"><canvas id="cashChart"></canvas></div>
    {runway_block}
    <div class="setup-foot"><strong>What this shows:</strong> $113M cash at Dec 28 2025 → $51M at Mar 29 2026. Projected Q2 bar is lighter (TBD per Aug print).
    <strong>What to watch:</strong> any 8-K disclosing revolver draw or covenant amendment terms.</div>
    {refresh_footer(DATA_DIR / "cash_position.csv")}
  </div>

  <div class="setup-card">
    <div class="setup-card-header">
      <div class="setup-card-title">Recent Insider Buying</div>
      <div class="setup-kpi">{cluster_kpi}</div>
    </div>
    <div class="setup-explain"><strong>Why this matters:</strong> 7 insiders putting personal money in post-print is the strongest insider signal pattern — single buys are noise, clusters are conviction.</div>
    {insider_table_html}
    {refresh_footer(DATA_DIR / "insider_trades.csv")}
  </div>

  <div class="setup-card">
    <div class="setup-card-header">
      <div class="setup-card-title">Short Interest Trend</div>
      <div class="setup-kpi">{short_kpi}</div>
    </div>
    <div class="chart-wrap" style="height:200px"><canvas id="shortChart"></canvas></div>
    <div class="setup-foot"><strong>What to watch:</strong> sustained cover (declining %) confirms recovery; holding at 40%+ says bears are still confident.</div>
    {refresh_footer(DATA_DIR / "short_interest.csv")}
  </div>

  <div class="setup-card setup-buyback">
    <div class="setup-card-header">
      <div class="setup-card-title">Buyback Authorization {datestamp_chip(buyback_md['datestamp'])}</div>
    </div>
    <div class="buyback-body">{buyback_md['html']}</div>
    <div class="setup-foot"><strong>What to watch:</strong> resumption flips short-squeeze risk hard — management wouldn't burn cash on share repurchases mid-covenant-negotiation unless conviction is high.</div>
    {refresh_footer(READS_DIR / "buyback_status.md")}
  </div>
</div>

<div class="setup-synthesis">
  <div class="setup-synth-eyebrow">SYNTHESIS {datestamp_chip(setup_synth_md['datestamp'])}</div>
  {setup_synth_md['html']}
</div>

{chart_card("setupOverTimeChart",
            "Insider Buys · Short Interest · Stock Price · 24 months",
            "All three normalized to 100 at start. Tests whether the May 13-15 cluster is the first divergence in a regime change.",
            "Stock = yfinance · short interest = FINRA semi-monthly (seeded historical + yfinance current) · insider buys = SEC Form 4 (seeded May 13-15 cluster, EDGAR parser pending).",
            READS_DIR / "setup_over_time_take.md",
            y_axis_label="Stock = index (left, base=100). Short % and Insider cumulative $K = right axis.",
            height_class="big")}
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
  <div class="section-num">SECTION 02</div>
  <div class="section-title">Stock &amp; News <span class="muted-cell" style="font-size:11.5px;font-weight:500">· {news.get('total', 0)} articles tracked</span></div>
  <div class="section-subtitle">The hero overlays meaningful news events on the stock line. Below: topic mix over time, news-cadence vs price, and expandable article log.</div>
</div>

<div class="chart-card">
  <div class="chart-title-row">
    <h3>VITL Daily Close · 18 months · News Events Overlaid</h3>
    <div class="chart-subtitle">7 negative-event reactions tracked. The +3.6% April 2 dot is the only positive reaction to bad news in the cycle.</div>
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
  <div class="section-num">SECTION 03</div>
  <div class="section-title">The Egg Market — Price Gap Tracker</div>
  <div class="section-subtitle">The single most analytically unique panel on the dashboard. Four sub-charts split out so each tells one story.</div>
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
            "Conventional Wholesale vs VITL Retail · 5 years weekly",
            "Two lines, both in $/dozen, single y-axis. Shows the absolute spread that drives the gap chart below.",
            "Conventional shell egg = USDA AMS midwest large white (seeded; MARS API fetcher TBD). VITL retail = manual snapshots from in-store checks + earnings-call commentary, monthly forward-filled.",
            READS_DIR / "conv_vs_vitl_take.md",
            y_axis_label="Price ($/dozen)",
            height_class="big")}

{chart_card("eggChart2",
            "Premium Gap % · 5 years weekly",
            "(VITL retail / Conventional wholesale − 1) × 100. The single most important variable in the thesis.",
            "Derived from the two series above. Shaded band = 150-200% historical norm.",
            READS_DIR / "premium_gap_take.md",
            y_axis_label="Gap (%)",
            height_class="big")}

{chart_card("eggChart3",
            "VITL Stock vs Premium Gap % · 18 months",
            "Two lines, both normalized to 100 at start. Tests whether the stock is fundamentally a macro trade on the gap.",
            "Stock = yfinance. Gap = derived from USDA AMS + VITL retail series.",
            READS_DIR / "stock_vs_gap_take.md",
            y_axis_label="Indexed to 100 at start of window",
            height_class="big")}

{chart_card("eggChart4",
            "Breaker Market vs Conventional Wholesale · 2 years weekly",
            "Both in $/dozen. The breaker market is where unsold branded eggs end up — every dime higher is direct margin tailwind for VITL.",
            "USDA AMS breaker egg market (seeded; same MARS API). Conventional from chart 1.",
            READS_DIR / "breaker_take.md",
            y_axis_label="Price ($/dozen)",
            height_class="big")}
"""


def render_community(comm: dict) -> str:
    md = load_markdown(READS_DIR / "brand_health_take.md")
    # Subreddit table
    if not comm["sub_rows"]:
        body = '<div class="placeholder">No subreddits in <code>config/reddit_subreddits.csv</code>.</div>'
    else:
        rows_html = ""
        for r in comm["sub_rows"]:
            yoy = r["yoy_pct"]
            yoy_cls = "badge-pos" if (yoy is not None and yoy >= 0) else ("badge-neg" if yoy is not None else "")
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
        body = f"""<div class="table-card"><table><thead><tr>
<th>Subreddit</th><th>Topic</th><th>Priority</th>
<th class="num">Mentions (90d)</th><th class="num">YoY %</th>
</tr></thead><tbody>{rows_html}</tbody></table></div>"""

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
  <div class="section-title">Brand Health &amp; Distribution</div>
  <div class="section-subtitle">Reddit volume across food/health/value subs · 6-brand share of voice · controversy decay · TDPs vs revenue.</div>
</div>

<div class="chart-card">
  <div class="chart-title-row">
    <h3>Subreddit Mention Activity · Past 90 Days &amp; YoY</h3>
    <div class="chart-subtitle">Title + post body + comments via Arctic Shift. Sparse on most subs — premium-egg brand names are not commonly written by users.</div>
  </div>
  <div class="axis-label">Mentions (90d) = absolute count · YoY = vs same 90d window 12 months ago</div>
  {body}
  <div class="source-caption"><strong>Source:</strong> Arctic Shift public archive via <code>fetch_reddit_arctic.py</code> (3-stage sweep: title → selftext → comments).</div>
  {refresh_footer(DATA_DIR / "reddit_mentions_weekly.csv")}
</div>

{chart_card("brandSovChart",
            "Brand Share of Voice — Pasture-Raised Egg Set · 36 months weekly",
            "All 6 brands (Vital Farms, Handsome Brook, Alexandre, Pete & Gerry's, Happy Egg, Organic Valley) stacked. Tests whether competitors gained mindshare during the ERP gap.",
            "Arctic Shift title + body sweep per brand. Brands with 0 hits shown as flat zero-lines so the universe is always visible.",
            READS_DIR / "brand_sov_take.md",
            y_axis_label="Weekly mention count across 15 subreddits (stacked)",
            height_class="big")}
{brand_totals_html}

{chart_card("linoleicChart",
            "Linoleic-Acid Controversy Decay · 12 months weekly",
            "Reddit posts + comments mentioning \"vital farms\" AND (\"linoleic\" OR \"PUFA\" OR \"seed oil\"). YouTube monthly video count overlaid where available.",
            "Reddit from r/seedoilfree + r/Carnivore + r/nutrition (Arctic Shift). YouTube from queries \"vital farms linoleic/PUFA/seed oil\" (data/youtube_linoleic_monthly.csv).",
            READS_DIR / "linoleic_take.md",
            y_axis_label="Reddit = weekly posts (left), YouTube = monthly videos (right, normalized)",
            height_class="big")}

{chart_card("controversyVsStockChart",
            "Controversy Mentions vs VITL Stock · 12 months",
            "Two lines normalized to 100 at start. Tests whether the linoleic chatter actually moved the stock.",
            "Reddit mentions from linoleic_decay_weekly.csv. Stock from yfinance.",
            READS_DIR / "controversy_vs_stock_take.md",
            y_axis_label="Both series indexed to 100 at start",
            height_class="big")}

{chart_card("tdpVsRevenueChart",
            "TDP Growth YoY vs Revenue Growth YoY · 8 quarters",
            "Side-by-side bars per quarter. Tests whether distribution gains are translating into revenue.",
            "TDP (Total Distribution Points — shelf SKU placements) from management commentary + sell-side. Revenue YoY from quarterly prints.",
            READS_DIR / "tdp_vs_revenue_take.md",
            y_axis_label="YoY growth (%)",
            height_class="big")}
"""


def render_financial(fin: dict) -> str:
    # Credibility table
    rows_html = ""
    for r in fin["credibility"]:
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
    cred_table = (f'<div class="table-card"><table>'
        f'<thead><tr><th>Period</th><th>Metric</th><th>Management Said</th><th>Actual</th><th>Delta</th></tr></thead>'
        f'<tbody>{rows_html}</tbody></table></div>'
        if rows_html else '<div class="placeholder">No rows in <code>data/guidance_vs_actual.csv</code>.</div>')

    md = load_markdown(READS_DIR / "credibility_take.md")

    return f"""
<div class="section-header" id="financial">
  <div class="section-num">SECTION 05</div>
  <div class="section-title">Financial History</div>
  <div class="section-subtitle">Is the financial trajectory recovering or declining? EBITDA margin arc · cash-burn composition · guidance scorecard.</div>
</div>

{chart_card("ebitdaHistoryChart",
            "EBITDA Margin History · 2020 → 2030 Target",
            "Peak Q1 25 at 16.9%. 10-14% historical norm band shaded. 2030 target 15-17% (aspirational — only hit it once).",
            "Annual data 2020-2024 from 10-K filings. Quarterly 2025-2026 from prints. 2026E and beyond from management guide ranges. 2030T from corporate strategy day.",
            READS_DIR / "ebitda_history_take.md",
            y_axis_label="EBITDA margin (% of revenue)",
            height_class="big")}

{chart_card("cashBurnChart",
            "Cash Burn Decomposition · Last 4 Quarters",
            "Stacked bars showing where each quarter's burn went: Operations · CapEx · Supply Management · Buyback · Other.",
            "Operations + CapEx from cash flow statements. Supply mgmt from management commentary. Buyback from share repurchase disclosures. Q2/H2 2026 from guidance midpoints.",
            READS_DIR / "cash_burn_take.md",
            y_axis_label="Cash burn ($M, stacked)",
            height_class="big")}

<div class="chart-card">
  <div class="chart-title-row">
    <h3>Management Credibility Scorecard {datestamp_chip(md['datestamp'])}</h3>
    <div class="chart-subtitle">Two cuts in 4 months. The trajectory matters more than any single line — watch for any forward number that holds within the new guide range as the recovery signal.</div>
  </div>
  {cred_table}
  <div class="source-caption"><strong>Source:</strong> Quarterly earnings releases and call transcripts. Hand-curated in <code>guidance_vs_actual.csv</code>; appended on each print.</div>
  {refresh_footer(DATA_DIR / "guidance_vs_actual.csv")}
  <div class="chart-take">
    <div class="take-eyebrow">WHAT TO WATCH {datestamp_chip(md['datestamp'])}</div>
    {md['html']}
  </div>
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

    return f"""
<div class="section-header" id="correlation">
  <div class="section-num">SECTION 06</div>
  <div class="section-title">Correlation Snapshot</div>
  <div class="section-subtitle">Pairwise Pearson correlations across the 5 most important signals. Numbers are over the maximum overlapping window per pair.</div>
</div>

{body}
<div class="source-caption"><strong>Source:</strong> Computed by <code>scripts/compute_correlations.py</code> from existing CSVs. All series resampled to week-ending Sunday. n = number of overlapping weekly observations per pair.</div>
{refresh_footer(DATA_DIR / "correlations.csv")}

<div class="chart-take">
  <div class="take-eyebrow">WHAT TO WATCH {datestamp_chip(md['datestamp'])}</div>
  {md['html']}
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
    qr      = compute_quick_read(d)
    setup   = compute_setup(d)
    events  = compute_events_chart(d)
    news    = compute_news(d)
    cad_vs_stock = compute_cadence_vs_stock(d, news)
    egg     = compute_egg_market(d)
    comm    = compute_community(d)
    tdp     = compute_tdp_vs_revenue(d)
    fin     = compute_financial_history(d)
    corr    = compute_correlation_matrix(d)
    summary = compute_summary(d, qr, setup, news, egg, fin, corr)

    chart_blob = json.dumps({
        "setup":          setup,
        "events":         events,
        "news":           news,
        "cad_vs_stock":   cad_vs_stock,
        "egg":            egg,
        "comm":           comm,
        "tdp":            tdp,
        "fin":            fin,
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
    <a class="nav-btn" href="#setup">Setup</a>
    <a class="nav-btn" href="#news">Stock &amp; News</a>
    <a class="nav-btn" href="#egg-market">Egg Market</a>
    <a class="nav-btn" href="#community">Brand Health</a>
    <a class="nav-btn" href="#financial">Financials</a>
    <a class="nav-btn" href="#correlation">Correlations</a>
  </div>
  <button class="summary-btn" onclick="document.getElementById('summaryModal').style.display='flex'">
    Generate Summary
  </button>
</div>

{render_top_callout()}
{render_three_damages()}

<div class="container">
  {render_quick_read(qr)}
  {render_setup(setup)}
  {render_stock_news(events, news, cad_vs_stock)}
  {render_egg_market(egg)}
  {render_community(comm)}
  {render_financial(fin)}
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

    // ── Section 01 — Cash + Short + Setup-Over-Time ───────────────────────
    const setup = d.setup;
    new Chart(document.getElementById('cashChart'), {{
      type: 'bar',
      data: {{
        labels: setup.cash_rows.map(r => r.label),
        datasets: [{{
          label: 'Cash ($M)',
          data: setup.cash_rows.map(r => r.tbd ? null : r.value),
          backgroundColor: setup.cash_rows.map(r => r.tbd ? 'rgba(46,90,60,0.18)' : (r.value < 80 ? NEG : A)),
          borderColor: setup.cash_rows.map(r => r.tbd ? A : 'transparent'),
          borderWidth: 2, borderRadius: 4,
          borderDash: setup.cash_rows.map(r => r.tbd ? [5,3] : []),
        }}],
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{
          legend: {{ display: false }},
          tooltip: {{ callbacks: {{
            label: ctx => ctx.raw == null ? 'TBD (Q2 print pending)' : '$' + ctx.raw.toFixed(1) + 'M',
            afterBody: ctx => {{ const r = setup.cash_rows[ctx[0].dataIndex]; return r && r.note ? r.note : ''; }},
          }} }},
        }},
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }} }} }},
          y: {{ grid: {{ color: 'rgba(0,0,0,0.05)' }},
                ticks: {{ font: {{ size: 10 }}, callback: v => '$' + v + 'M' }},
                title: {{ display: true, text: 'Cash & equivalents ($M)', font: {{ size: 10 }} }} }},
        }},
      }},
    }});

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

    // ── Section 02 — Events chart, Topic Mix Over Time, Cadence vs Stock ─
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
             pointRadius: 11, pointHoverRadius: 14,
             pointBackgroundColor: ev.events.map(e => d.reaction_colors[e.reaction_kind] || '#999'),
             pointBorderColor: '#fff', pointBorderWidth: 3,
             order: 1, parsing: false }},
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

    // ── Section 04 — SoV + Linoleic + Controversy vs Stock + TDP vs Rev ──
    const sov = d.comm.brand_sov;
    const sovDatasets = d.brand_order.filter(b => sov.brands && sov.brands[b]).map(b => ({{
      label: b, data: sov.brands[b], borderColor: d.brand_colors[b] || '#999',
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
            y: {{ stacked: true, grid: {{ color: 'rgba(0,0,0,0.04)' }}, ticks: {{ font: {{ size: 10 }} }},
                  title: {{ display: true, text: 'Weekly mentions across 15 subs', font: {{ size: 10 }} }} }},
          }},
        }},
      }});
    }}

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

    const cvss = d.comm.controversy_vs_stock;
    new Chart(document.getElementById('controversyVsStockChart'), {{
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

    // ── Section 05 — EBITDA history + Cash burn decomp ────────────────────
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

    const cb = d.fin.cash_burn;
    new Chart(document.getElementById('cashBurnChart'), {{
      type: 'bar',
      data: {{
        labels: cb.quarters,
        datasets: [
          {{ label: 'Operations',    data: cb.operations,  backgroundColor: A,      borderRadius: 2 }},
          {{ label: 'CapEx',         data: cb.capex,       backgroundColor: A2,     borderRadius: 2 }},
          {{ label: 'Supply mgmt',   data: cb.supply_mgmt, backgroundColor: NEG,    borderRadius: 2 }},
          {{ label: 'Buyback',       data: cb.buyback,     backgroundColor: PURPLE, borderRadius: 2 }},
          {{ label: 'Other',         data: cb.other,       backgroundColor: BROWN,  borderRadius: 2 }},
        ],
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{ legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }} }} }}, tooltip: {{ mode: 'index', intersect: false }} }},
        scales: {{
          x: {{ stacked: true, grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }} }} }},
          y: {{ stacked: true, grid: {{ color: 'rgba(0,0,0,0.04)' }},
                ticks: {{ font: {{ size: 10 }}, callback: v => '$' + v + 'M' }},
                title: {{ display: true, text: 'Cash burn ($M)', font: {{ size: 10 }} }} }},
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
