"""SEC EDGAR Form 4 insider transactions for VITL.

EDGAR exposes a clean JSON submissions endpoint per company:
  https://data.sec.gov/submissions/CIK<10-digit-zero-padded>.json

That endpoint lists recent filings; we filter to type='4' (Form 4 — insider
transactions). Each Form 4 has an XML payload at:
  https://www.sec.gov/Archives/edgar/data/<CIK>/<acc-no-dashes>/<primary_doc>

For this pass we attempt the real EDGAR pull but degrade gracefully to the
seeded May 13-15 cluster CSV. Even when real Form 4s come through, we union
with the seed so the cluster is always present even if EDGAR drops a row.

Output: data/insider_trades.csv
  date, name, title, kind, shares, price, total_value, source

Cluster flag: any 3+ buys within 10 days. Surfaced via stdout summary.
"""
from __future__ import annotations

import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUT_CSV = DATA_DIR / "insider_trades.csv"

VITL_CIK = "0001658566"  # Vital Farms, padded to 10 digits
# EDGAR requires a real contact User-Agent. Use the analyst's email per SEC fair-access policy.
EDGAR_UA = "Pillsbury Lake Capital research en@pillsburycap.com"

SUBMISSIONS_URL = f"https://data.sec.gov/submissions/CIK{VITL_CIK}.json"


def fetch_recent_form4s(window_days: int = 90) -> list[dict]:
    """Return Form 4 filing metadata from the last `window_days` for VITL."""
    headers = {"User-Agent": EDGAR_UA, "Accept": "application/json"}
    try:
        r = requests.get(SUBMISSIONS_URL, headers=headers, timeout=20)
        r.raise_for_status()
        data = r.json()
    except (requests.RequestException, ValueError) as exc:
        print(f"  [warn] EDGAR submissions fetch failed: {exc}", file=sys.stderr)
        return []

    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    acc_nos = recent.get("accessionNumber", [])
    primary_docs = recent.get("primaryDocument", [])
    cutoff = (datetime.today() - timedelta(days=window_days)).strftime("%Y-%m-%d")
    out = []
    for f, d, a, pd_ in zip(forms, dates, acc_nos, primary_docs):
        if f != "4": continue
        if d < cutoff: continue
        out.append({"date": d, "accession": a, "primary_doc": pd_})
    return out


def parse_form4_xml(accession: str, primary_doc: str) -> list[dict]:
    """Parse one Form 4 XML and extract non-derivative transactions.

    EDGAR Form 4 XML has <nonDerivativeTransaction> blocks with shares, price,
    transaction code (P=Purchase, S=Sale), and the reporting person info.
    """
    acc_clean = accession.replace("-", "")
    url = f"https://www.sec.gov/Archives/edgar/data/{int(VITL_CIK)}/{acc_clean}/{primary_doc}"
    headers = {"User-Agent": EDGAR_UA}
    try:
        time.sleep(0.15)  # SEC fair-use rate limit
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
    except requests.RequestException as exc:
        print(f"  [warn] Form 4 XML fetch failed for {accession}: {exc}", file=sys.stderr)
        return []

    try:
        root = ET.fromstring(r.text)
    except ET.ParseError:
        return []

    # Form 4 XML uses no namespace prefix but does declare xmlns in some
    # filings; .find/findall with element-name-only paths handle both cases.
    # Strip default namespace if present so xpath paths work consistently.
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0].strip("{")
        # Re-parse with namespace stripping
        for elem in root.iter():
            if "}" in elem.tag:
                elem.tag = elem.tag.split("}", 1)[1]

    # Reporting person
    name = "Unknown"
    rpt_name_el = root.find(".//rptOwnerName")
    if rpt_name_el is not None and rpt_name_el.text:
        name = rpt_name_el.text.strip()

    rel = root.find(".//reportingOwnerRelationship")
    title_bits = []
    if rel is not None:
        if (rel.findtext("isDirector") or "").strip() in ("1","true","True"): title_bits.append("Director")
        if (rel.findtext("isOfficer") or "").strip() in ("1","true","True"):
            ot = rel.findtext("officerTitle") or "Officer"
            title_bits.append(ot)
        if (rel.findtext("isTenPercentOwner") or "").strip() in ("1","true","True"): title_bits.append("10% Owner")
    title = " / ".join(title_bits) or "Insider"

    rows = []
    for tx in root.findall(".//nonDerivativeTransaction"):
        # Form 4 wraps each value in a <value> child element
        date_el = tx.find(".//transactionDate/value")
        code_el = tx.find(".//transactionCoding/transactionCode")
        shares_el = tx.find(".//transactionAmounts/transactionShares/value")
        price_el = tx.find(".//transactionAmounts/transactionPricePerShare/value")
        date = (date_el.text if date_el is not None else "") or ""
        code = ((code_el.text if code_el is not None else "") or "").upper()
        shares_txt = (shares_el.text if shares_el is not None else "0") or "0"
        price_txt = (price_el.text if price_el is not None else "0") or "0"
        try:
            shares = float(shares_txt); price = float(price_txt)
        except ValueError:
            continue
        if shares <= 0 or price <= 0: continue
        kind = "buy" if code == "P" else ("sell" if code == "S" else code.lower())
        rows.append({
            "date": date, "name": name, "title": title, "kind": kind,
            "shares": int(shares), "price": round(price, 2),
            "total_value": round(shares * price, 2),
            "source": f"EDGAR Form 4 ({accession})",
        })
    return rows


def detect_clusters(df: pd.DataFrame, window_days: int = 10, min_insiders: int = 3) -> list[dict]:
    if df.empty: return []
    buys = df[df["kind"] == "buy"].copy()
    if buys.empty: return []
    buys["dt"] = pd.to_datetime(buys["date"])
    buys = buys.sort_values("dt").reset_index(drop=True)
    clusters = []
    i = 0
    while i < len(buys):
        window = buys[buys["dt"] <= buys.iloc[i]["dt"] + pd.Timedelta(days=window_days)]
        window = window[window["dt"] >= buys.iloc[i]["dt"]]
        unique_insiders = window["name"].nunique()
        if unique_insiders >= min_insiders:
            clusters.append({
                "start": window["dt"].min().strftime("%Y-%m-%d"),
                "end": window["dt"].max().strftime("%Y-%m-%d"),
                "insiders": unique_insiders,
                "total_value": float(window["total_value"].sum()),
            })
            i += len(window)
        else:
            i += 1
    return clusters


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Load seed
    if OUT_CSV.exists():
        existing = pd.read_csv(OUT_CSV)
        print(f"  · loaded seed/existing  rows={len(existing)}")
    else:
        existing = pd.DataFrame(columns=["date","name","title","kind","shares","price","total_value","source"])

    print(f"  attempting EDGAR Form 4 fetch for CIK {VITL_CIK} (last 90d) ...")
    metas = fetch_recent_form4s(window_days=90)
    print(f"  · EDGAR returned {len(metas)} Form 4 filings")

    fetched_rows = []
    for m in metas[:30]:  # cap at 30 to keep request volume polite
        fetched_rows.extend(parse_form4_xml(m["accession"], m["primary_doc"]))
    if fetched_rows:
        new_df = pd.DataFrame(fetched_rows)
        print(f"  · parsed {len(new_df)} transactions")
        # Union with seed, dedupe on (date, name, shares, price)
        combined = pd.concat([existing, new_df], ignore_index=True)
        combined = combined.drop_duplicates(subset=["date","name","shares","price"])
        combined = combined.sort_values("date", ascending=False).reset_index(drop=True)
    else:
        combined = existing
        print("  · no EDGAR rows parsed — using seed only")

    combined.to_csv(OUT_CSV, index=False)
    print(f"  ✓ wrote {OUT_CSV.name}  rows={len(combined)}")

    # Cluster detection summary
    clusters = detect_clusters(combined)
    if clusters:
        for c in clusters:
            print(f"    cluster: {c['insiders']} insiders  {c['start']}..{c['end']}  ${c['total_value']:,.0f}")
    else:
        print("    no buying clusters detected in current window")

    return 0


if __name__ == "__main__":
    sys.exit(main())
