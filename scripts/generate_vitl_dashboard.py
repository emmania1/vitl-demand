"""
Vital Farms Demand Intelligence Dashboard — v1 (scaffold)

Layout philosophy: most substantial → least substantial.
Outsider-friendly: clear data-source attribution on every chart; neutral
descriptive language (no investment-thesis framing in UI text).

Sections:
  1. OVERVIEW                — hero tiles + 24-month composite demand trajectory
  2. RETAIL DISTRIBUTION     — store count, % ACV, SKU breadth, OOS tracking (CPG core page)
  3. PRODUCT LINE HEAT       — eggs vs butter vs ghee vs hard-boiled per-SKU signal
  4. COMMUNITY & SOCIAL      — Reddit + YouTube + TikTok food creator signal
  5. NEWS COVERAGE           — cadence + topic mix + publisher diversity
  6. PRICING POWER           — VITL price vs conventional + premium peers
  7. SUPPLY RISK MONITOR     — H5N1 news + USDA flock data + wholesale egg prices
  8. DEMAND vs STOCK         — VITL close with event markers

Reads (all optional — missing files degrade gracefully):
  config/products.csv          REQUIRED — SKU universe
  config/retailers.csv         REQUIRED — distribution targets
  config/reddit_subreddits.csv REQUIRED — Reddit community list
  data/*.csv                   fetcher output (none wired yet — placeholders shown)
"""
import json
import webbrowser
from datetime import datetime
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

LINE_COLORS = {
    "eggs":   BRAND_ACCENT,
    "butter": BRAND_ACCENT2,
    "ghee":   "#B5651D",      # warm brown
    "new":    "#8e6db4",      # purple for newer launches
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

TOPIC_KEYWORDS = {
    "supply":    ["avian flu", "bird flu", "h5n1", "outbreak", "flock", "shortage",
                  "egg supply", "depopulate", "culled"],
    "launch":    ["launches", "debut", "new product", "expands", "rolls out",
                  "available at", "now at", "rollout", "expansion"],
    "health":    ["pasture-raised", "organic", "nutrition", "health", "ethical",
                  "animal welfare", "humane", "regenerative"],
    "financial": ["earnings", "revenue", "quarter", "guidance", "ceo", "cfo",
                  "shares", "analyst", "upgrade", "downgrade", "beats estimates",
                  "misses estimates", "stock", "ipo"],
    "culture":   ["recipe", "viral", "tiktok", "instagram", "celebrity", "chef"],
}
TOPIC_COLORS = {
    "supply":    BRAND_ACCENT4,
    "launch":    BRAND_ACCENT,
    "health":    BRAND_ACCENT3,
    "financial": "#e67e22",
    "culture":   "#e84393",
    "other":     "#8b8271",
}
TOPIC_LABELS = {
    "supply":    "Supply / Avian Flu",
    "launch":    "Launch / Distribution",
    "health":    "Health / Ethical",
    "financial": "Financial",
    "culture":   "Culture / Recipe",
    "other":     "Other",
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
        "products":  safe_read(CONFIG_DIR / "products.csv"),
        "retailers": safe_read(CONFIG_DIR / "retailers.csv"),
        "subs":      safe_read(CONFIG_DIR / "reddit_subreddits.csv"),
        # data fetchers land here when wired up:
        "reddit_monthly": safe_read(DATA_DIR / "reddit_monthly.csv"),
        "youtube":        safe_read(DATA_DIR / "youtube.csv"),
        "news":           safe_read(DATA_DIR / "google_news.csv"),
        "stock":          safe_read(DATA_DIR / "vitl_stock.csv"),
        "egg_prices":     safe_read(DATA_DIR / "egg_wholesale.csv"),
        "retail_ACV":     safe_read(DATA_DIR / "retail_acv.csv"),
        "oos":            safe_read(DATA_DIR / "retail_oos.csv"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Compute layer (placeholders — replaced as fetchers come online)
# ─────────────────────────────────────────────────────────────────────────────
def compute_trajectory(d: dict) -> dict:
    """24-month demand composite — placeholder until Reddit/YouTube/News land."""
    months = pd.date_range(end=datetime.today(), periods=24, freq="MS").strftime("%Y-%m").tolist()
    # Placeholder series — gentle upward trajectory with seasonal egg-price spike
    eggs   = [100 + i * 1.8 + (12 if i in (10, 11, 12) else 0) for i in range(24)]
    butter = [40 + i * 1.2 for i in range(24)]
    ghee   = [15 + i * 0.6 for i in range(24)]
    return {
        "months":  months,
        "eggs":    [round(x, 1) for x in eggs],
        "butter":  [round(x, 1) for x in butter],
        "ghee":    [round(x, 1) for x in ghee],
    }


def compute_hero(d: dict, traj: dict) -> dict:
    products = d["products"]
    retailers = d["retailers"]
    sku_count   = len(products) if not products.empty else 0
    retail_targets = len(retailers) if not retailers.empty else 0
    # placeholder YoY composite
    yoy_eggs = round((traj["eggs"][-1] / traj["eggs"][-13] - 1) * 100, 1) if traj["eggs"][-13] else 0
    return {
        "sku_count": sku_count,
        "retail_targets": retail_targets,
        "yoy_composite": yoy_eggs,
        "data_lag_days": 1,
    }


def compute_retail(d: dict) -> dict:
    """Retail distribution table — placeholder until ACV/store-count fetchers land."""
    retailers = d["retailers"]
    if retailers.empty:
        return {"rows": []}
    # Placeholder: assign synthetic distribution snapshots
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
        key = r["key"]
        rows.append({
            "key": key,
            "name": r["display_name"],
            "channel": r["channel"],
            "priority": r["priority"],
            "pct_acv": placeholder_acv.get(key, 0),
            "skus": placeholder_skus.get(key, 0),
            "oos_pct": 0,  # placeholder until OOS fetcher wired
            "notes": r.get("notes", "") if "notes" in r else "",
        })
    return {"rows": rows}


def compute_product_heat(d: dict) -> dict:
    """Per-SKU heat map — placeholder."""
    products = d["products"]
    if products.empty:
        return {"rows": []}
    rows = []
    for _, p in products.iterrows():
        rows.append({
            "key": p["key"],
            "name": p["display_name"],
            "line": p["line"],
            "priority": p["priority"],
            "launch_year": p["launch_year"],
            "reddit_yoy": None,    # filled when Reddit fetcher lands
            "youtube_yoy": None,
            "search_yoy": None,
            "notes": p.get("notes", "") if "notes" in p else "",
        })
    return {"rows": rows}


def compute_community(d: dict) -> dict:
    subs = d["subs"]
    if subs.empty:
        return {"sub_rows": [], "platform_summary": {}}
    rows = [{
        "subreddit": r["subreddit"],
        "topic": r["topic"],
        "priority": r["priority"],
        "mentions_90d": None,        # placeholder
        "yoy_pct": None,
    } for _, r in subs.iterrows()]
    return {
        "sub_rows": rows,
        "platform_summary": {
            "reddit_mentions_90d": None,
            "youtube_uploads_90d": None,
            "tiktok_hashtag_views": None,
        },
    }


def compute_news(d: dict) -> dict:
    """News cadence + topic mix — placeholder."""
    news = d["news"]
    if news.empty:
        return {"cadence": {"months": [], "counts": []}, "topics": {}, "publishers": []}
    # placeholder — when fetcher lands, classify by TOPIC_KEYWORDS
    return {"cadence": {"months": [], "counts": []}, "topics": {}, "publishers": []}


def compute_pricing(d: dict) -> dict:
    """Premium price spread vs conventional + peers — placeholder."""
    return {
        "vitl_price": None,
        "conventional_price": None,
        "peers": [],  # [{name, price, premium_pct}]
        "history": {"months": [], "vitl": [], "conventional": []},
    }


def compute_supply(d: dict) -> dict:
    """Avian flu + wholesale egg price + flock data — placeholder."""
    egg = d["egg_prices"]
    return {
        "wholesale_history": {"months": [], "cents_per_dozen": []},
        "flu_events": [],     # [{date, headline, severity}]
        "flock_size": None,
        "pasture_raised_premium": None,
    }


def compute_stock(d: dict) -> dict:
    """VITL stock overlay — placeholder."""
    stock = d["stock"]
    if stock.empty:
        return {"dates": [], "close": [], "events": []}
    return {"dates": [], "close": [], "events": []}


def compute_summary(d, hero, retail, heat, news, supply) -> dict:
    """Auto-narrative for the modal. Reads computed metrics; degrades when missing."""
    bullets = [
        f"SKU universe tracked: <strong>{hero['sku_count']}</strong> products across eggs / butter / ghee / adjacencies.",
        f"Retail targets monitored: <strong>{hero['retail_targets']}</strong> banners spanning natural, grocery, mass, club, and ecom.",
        ("Composite demand trajectory (placeholder): "
         f"<strong>{hero['yoy_composite']:+.1f}% YoY</strong> — replace once Reddit/YouTube/News fetchers land."),
        "Pricing power and Avian Flu / supply-risk panels are wired but awaiting fetchers (USDA wholesale + flock data).",
    ]
    return {
        "headline": f"{BRAND_NAME} ({BRAND_TICKER}) — Demand Signal Scaffold",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "bullets": bullets,
        "to_do_next": [
            "Wire <code>fetch_reddit_arctic.py</code> for r/Cooking / r/keto / r/PaleoDiet 3-yr archive.",
            "Wire <code>fetch_google_news.py</code> for whole-internet news + topic classification.",
            "Wire <code>fetch_youtube.py</code> for food / health creator coverage.",
            "Wire <code>fetch_stock_price.py</code> (yfinance VITL) and overlay events.",
            "Decide approach for Retail % ACV (NielsenIQ / Numerator licensing vs Instacart proxy).",
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Render helpers
# ─────────────────────────────────────────────────────────────────────────────
def fmt_num(v, default="—"):
    if v is None or (isinstance(v, float) and pd.isna(v)): return default
    if isinstance(v, (int, float)) and abs(v) >= 1000: return f"{int(v):,}"
    return str(v)


def source_caption(text: str) -> str:
    return f'<div class="source-caption">{text}</div>'


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
    <div class="hero-sub">products tracked across eggs, butter, ghee, adjacencies</div>
  </div>
  <div class="hero-tile">
    <div class="hero-label">Retail Banners Monitored</div>
    <div class="hero-val">{hero['retail_targets']}</div>
    <div class="hero-sub">natural / grocery / mass / club / ecom</div>
  </div>
  <div class="hero-tile">
    <div class="hero-label">Composite Demand YoY (placeholder)</div>
    <div class="hero-val">{hero['yoy_composite']:+.1f}<span class="hero-val-suffix">%</span></div>
    <div class="hero-sub">replace once Reddit/YouTube/News fetchers land</div>
  </div>
</div>

<div class="chart-card">
  <h3>24-Month Composite Demand Trajectory by Line</h3>
  <div class="chart-wrap big"><canvas id="trajChart"></canvas></div>
  {source_caption("Placeholder series. Once <code>fetch_reddit_arctic.py</code> + <code>fetch_youtube.py</code> + <code>fetch_google_news.py</code> are wired, this chart sums per-line signal from each source.")}
</div>
"""


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
  <div class="section-title">Retail Distribution &amp; Shelf</div>
  <div class="section-blurb">
    The <strong>core CPG page</strong>. For VITL specifically — does premium-egg distribution
    continue widening into mass / club, and does on-shelf availability hold during supply shocks?
    % ACV is a placeholder until a licensed scan-data feed (NielsenIQ / Numerator) or Instacart proxy
    is wired in.
  </div>
</div>
{body}
{source_caption("Placeholder distribution snapshot. Real values to come from licensed retail scan data, Instacart cross-banner proxy, or store-locator scrapes.")}
"""


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
  <div class="section-title">Product Line Heat Map</div>
  <div class="section-blurb">
    Per-SKU signal: eggs (flagship) vs butter (mid-stage extension) vs ghee (newer / paleo-keto)
    vs liquid-egg / hard-boiled (adjacencies). YoY columns light up once
    <code>fetch_reddit_arctic.py</code>, <code>fetch_youtube.py</code>, and
    <code>fetch_google_trends.py</code> are wired.
  </div>
</div>
{body}
"""


def render_community(comm: dict) -> str:
    if not comm["sub_rows"]:
        body = '<div class="placeholder">No subreddits in <code>config/reddit_subreddits.csv</code> yet.</div>'
    else:
        rows_html = ""
        for r in comm["sub_rows"]:
            rows_html += f"""
<tr>
  <td><strong>r/{r['subreddit']}</strong></td>
  <td>{r['topic']}</td>
  <td><span class="badge badge-na">{r['priority']}</span></td>
  <td class="num muted-cell">{fmt_num(r['mentions_90d'])}</td>
  <td class="num muted-cell">{fmt_num(r['yoy_pct'])}</td>
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
    return f"""
<div class="section-header" id="community">
  <div class="section-num">SECTION 04</div>
  <div class="section-title">Community &amp; Social Signal</div>
  <div class="section-blurb">
    Reddit + YouTube + TikTok food-creator volume around <em>Vital Farms</em>, pasture-raised eggs,
    and adjacent SKUs. For VITL the highest-signal subs are likely cooking + keto + paleo +
    EatCheapAndHealthy (premium-vs-value tension).
  </div>
</div>
{body}
{source_caption("To be filled by <code>fetch_reddit_arctic.py</code> (Arctic Shift public API), <code>fetch_youtube.py</code> (YouTube Data API), and a manual/scraped TikTok hashtag snapshot.")}
"""


def render_news() -> str:
    return f"""
<div class="section-header" id="news">
  <div class="section-num">SECTION 05</div>
  <div class="section-title">News Coverage</div>
  <div class="section-blurb">
    Article cadence + topic mix (<strong>supply / launch / health / financial / culture</strong>) +
    publisher diversity. Surfaces non-quarterly news flow — especially supply / avian-flu coverage
    that moves the egg category.
  </div>
</div>
<div class="dual-col">
  <div class="chart-card">
    <h3>Article Cadence (24 months)</h3>
    <div class="chart-wrap"><canvas id="newsCadenceChart"></canvas></div>
  </div>
  <div class="chart-card">
    <h3>Topic Mix</h3>
    <div class="chart-wrap"><canvas id="newsTopicChart"></canvas></div>
  </div>
</div>
{source_caption("Wired by <code>fetch_google_news.py</code> (public RSS). Topics classified via keyword dictionary in script (<code>TOPIC_KEYWORDS</code>).")}
"""


def render_pricing() -> str:
    return f"""
<div class="section-header" id="pricing">
  <div class="section-num">SECTION 06</div>
  <div class="section-title">Pricing Power Monitor</div>
  <div class="section-blurb">
    VITL retail price vs (a) conventional Grade-A eggs (USDA / BLS) and (b) premium peers
    (Pete &amp; Gerry's, Happy Egg, Handsome Brook, Organic Valley). The signal: does the
    pasture-raised premium <strong>compress</strong> when conventional egg prices spike, or
    does VITL hold absolute pricing?
  </div>
</div>
<div class="chart-card">
  <h3>VITL vs Conventional — Retail Price History (placeholder)</h3>
  <div class="chart-wrap big"><canvas id="pricingChart"></canvas></div>
  {source_caption("To be wired from store-locator scrapes (Instacart, Kroger.com), USDA wholesale, and BLS CPI eggs series.")}
</div>
"""


def render_supply() -> str:
    return f"""
<div class="section-header" id="supply">
  <div class="section-num">SECTION 07</div>
  <div class="section-title">Supply Risk Monitor — Avian Flu &amp; Egg Wholesale</div>
  <div class="section-blurb">
    H5N1 / HPAI news flow + USDA egg wholesale prices + flock data.
    Pasture-raised flocks have <strong>lower density</strong> than caged operations, so VITL is
    structurally less exposed than CALM-style conventional producers — but not immune. This panel
    isolates supply-side risk separately from demand.
  </div>
</div>
<div class="chart-card">
  <h3>Wholesale Egg Price (USDA, cents/dozen) — placeholder</h3>
  <div class="chart-wrap big"><canvas id="supplyChart"></canvas></div>
  {source_caption("To be wired from USDA AMS daily egg market reports + USDA APHIS HPAI confirmed cases.")}
</div>
"""


def render_stock() -> str:
    return f"""
<div class="section-header" id="stock">
  <div class="section-num">SECTION 08</div>
  <div class="section-title">Demand vs Stock</div>
  <div class="section-blurb">
    VITL close overlaid with composite demand and event markers (earnings, distribution wins,
    supply shocks, analyst initiations).
  </div>
</div>
<div class="chart-card">
  <h3>VITL Close + Demand + Events (placeholder)</h3>
  <div class="chart-wrap big"><canvas id="stockChart"></canvas></div>
  {source_caption("Wired by <code>fetch_stock_price.py</code> (yfinance) + event log from news classification + manual analyst log.")}
</div>
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
    traj    = compute_trajectory(d)
    hero    = compute_hero(d, traj)
    retail  = compute_retail(d)
    heat    = compute_product_heat(d)
    comm    = compute_community(d)
    news    = compute_news(d)
    supply  = compute_supply(d)
    stock   = compute_stock(d)
    summary = compute_summary(d, hero, retail, heat, news, supply)

    chart_blob = json.dumps({
        "traj": traj,
        "news_cadence": news["cadence"],
        "news_topics":  news["topics"],
        "pricing":      compute_pricing(d),
        "supply":       supply,
        "stock":        stock,
    })

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    summary_html = render_summary_modal(summary)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{BRAND_NAME} ({BRAND_TICKER}) Demand Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
<style>
  /* Vital Farms — warm cream / pasture-green palette */
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
  .section-blurb {{ font-size: 13px; color: var(--text-soft); line-height: 1.6;
                    margin-top: 12px; padding: 12px 16px; max-width: 880px;
                    background: #fef9ec; border: 1px solid #f2e4b6;
                    border-left: 4px solid var(--accent2); border-radius: 6px; }}
  .section-blurb strong {{ color: var(--text); font-weight: 700; }}

  .hero-row {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 14px; margin-bottom: 14px; }}
  .hero-tile {{ background: var(--surface); border: 1px solid var(--border);
                border-radius: 10px; padding: 20px 22px;
                box-shadow: 0 1px 3px rgba(45,47,37,0.04); }}
  .hero-label {{ font-size: 10px; color: var(--muted); text-transform: uppercase;
                 letter-spacing: 0.8px; margin-bottom: 10px; font-weight: 700; }}
  .hero-val {{ font-size: 34px; font-weight: 700; letter-spacing: -0.8px; color: var(--text); }}
  .hero-val-suffix {{ font-size: 12px; color: var(--muted); font-weight: 500; margin-left: 8px; }}
  .hero-sub {{ font-size: 11.5px; color: var(--muted); margin-top: 6px; }}

  .chart-card {{ background: var(--surface); border: 1px solid var(--border);
                 border-radius: 10px; padding: 20px 22px; margin-bottom: 14px;
                 box-shadow: 0 1px 3px rgba(45,47,37,0.04); }}
  .chart-card h3 {{ font-size: 14px; font-weight: 700; margin-bottom: 14px;
                    letter-spacing: -0.2px; color: var(--text); }}
  .chart-wrap {{ position: relative; height: 300px; }}
  .chart-wrap.big {{ height: 380px; }}

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
  <h1>{BRAND_NAME} <span style="color:var(--muted);font-weight:400">— {BRAND_TICKER} Demand Intelligence</span></h1>
  <div class="topbar-nav">
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
  {render_overview(hero, traj)}
  {render_retail(retail)}
  {render_product_heat(heat)}
  {render_community(comm)}
  {render_news()}
  {render_pricing()}
  {render_supply()}
  {render_stock()}
</div>

<footer>
  {BRAND_NAME} ({BRAND_TICKER}) Demand Dashboard · generated {generated_at}
</footer>

{summary_html}

<script>
  window.__vitl = {chart_blob};
  document.addEventListener('DOMContentLoaded', () => {{
    const d = window.__vitl;

    // ── Section 1: trajectory ────────────────────────────────────────────────
    new Chart(document.getElementById('trajChart'), {{
      type: 'line',
      data: {{
        labels: d.traj.months,
        datasets: [
          {{ label: 'Eggs',   data: d.traj.eggs,   borderColor: '{BRAND_ACCENT}',
             backgroundColor: 'rgba(46,90,60,0.08)', borderWidth: 2.2, tension: 0.3, fill: true }},
          {{ label: 'Butter', data: d.traj.butter, borderColor: '{BRAND_ACCENT2}',
             backgroundColor: 'rgba(244,196,48,0.08)', borderWidth: 2, tension: 0.3, fill: false }},
          {{ label: 'Ghee',   data: d.traj.ghee,   borderColor: '#B5651D',
             backgroundColor: 'rgba(181,101,29,0.08)', borderWidth: 2, tension: 0.3, fill: false }},
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

    // ── Section 5: news cadence (placeholder empty data — chart skips gracefully) ─
    const cadence = d.news_cadence || {{ months: [], counts: [] }};
    new Chart(document.getElementById('newsCadenceChart'), {{
      type: 'bar',
      data: {{
        labels: cadence.months,
        datasets: [{{ label: 'Articles', data: cadence.counts,
                      backgroundColor: '{BRAND_ACCENT}', borderRadius: 3 }}]
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{ legend: {{ display: false }} }},
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }} }} }},
          y: {{ grid: {{ color: 'rgba(0,0,0,0.04)' }}, ticks: {{ font: {{ size: 10 }} }} }}
        }}
      }}
    }});

    // topic mix doughnut
    const topics = d.news_topics || {{}};
    const topicKeys   = Object.keys(topics);
    const topicVals   = topicKeys.map(k => topics[k]);
    const topicColors = topicKeys.map(k => ({{
      supply: '{BRAND_ACCENT4}', launch: '{BRAND_ACCENT}', health: '{BRAND_ACCENT3}',
      financial: '#e67e22', culture: '#e84393', other: '#8b8271'
    }})[k] || '#999');
    new Chart(document.getElementById('newsTopicChart'), {{
      type: 'doughnut',
      data: {{ labels: topicKeys, datasets: [{{ data: topicVals, backgroundColor: topicColors, borderWidth: 0 }}] }},
      options: {{ responsive: true, maintainAspectRatio: false,
                  plugins: {{ legend: {{ position: 'right', labels: {{ font: {{ size: 11 }} }} }} }} }}
    }});

    // ── Section 6: pricing placeholder ────────────────────────────────────────
    new Chart(document.getElementById('pricingChart'), {{
      type: 'line',
      data: {{ labels: d.pricing.history.months || [],
               datasets: [
                 {{ label: 'VITL (premium)', data: d.pricing.history.vitl || [], borderColor: '{BRAND_ACCENT}', borderWidth: 2.2, tension: 0.3 }},
                 {{ label: 'Conventional', data: d.pricing.history.conventional || [], borderColor: '#8b8b78', borderDash: [4,4], borderWidth: 2, tension: 0.3 }},
               ] }},
      options: {{ responsive: true, maintainAspectRatio: false,
                  plugins: {{ legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }} }} }} }} }}
    }});

    // ── Section 7: supply ────────────────────────────────────────────────────
    new Chart(document.getElementById('supplyChart'), {{
      type: 'line',
      data: {{ labels: d.supply.wholesale_history.months || [],
               datasets: [{{ label: 'Wholesale (¢/dz)', data: d.supply.wholesale_history.cents_per_dozen || [],
                             borderColor: '{BRAND_ACCENT4}', backgroundColor: 'rgba(201,93,74,0.08)',
                             borderWidth: 2.2, tension: 0.3, fill: true }}] }},
      options: {{ responsive: true, maintainAspectRatio: false,
                  plugins: {{ legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }} }} }} }} }}
    }});

    // ── Section 8: stock ─────────────────────────────────────────────────────
    new Chart(document.getElementById('stockChart'), {{
      type: 'line',
      data: {{ labels: d.stock.dates || [],
               datasets: [{{ label: 'VITL Close', data: d.stock.close || [],
                             borderColor: '{BRAND_ACCENT}', backgroundColor: 'rgba(46,90,60,0.06)',
                             borderWidth: 2.2, tension: 0.2, fill: true }}] }},
      options: {{ responsive: true, maintainAspectRatio: false,
                  plugins: {{ legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }} }} }} }} }}
    }});
  }});
</script>

</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print(f"── {BRAND_NAME} ({BRAND_TICKER}) Demand Dashboard — scaffold v1 ──")
    d = load_all()
    for k, v in d.items():
        n = len(v) if hasattr(v, "__len__") else 0
        flag = "✓" if n > 0 else "·"
        print(f"  {flag} {k:20s} rows={n}")

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
