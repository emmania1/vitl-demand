PY := venv/bin/python

.PHONY: help refresh-data refresh-fast generate venv install clean-data

help:
	@echo "VITL Demand Dashboard"
	@echo ""
	@echo "  make venv          create local virtualenv at ./venv"
	@echo "  make install       install requirements into ./venv"
	@echo "  make refresh-data  run all fetchers in order (stock + reddit + news + competitors + youtube)"
	@echo "  make refresh-fast  skip youtube (no API key needed)"
	@echo "  make generate      regenerate index.html from existing /data CSVs"
	@echo "  make clean-data    remove all CSVs in /data (configs and fetchers untouched)"

venv:
	python3 -m venv venv

install: venv
	./venv/bin/pip install -U pip
	./venv/bin/pip install -r requirements.txt

refresh-data:
	@echo "── stock ────────────────────────────────────────────"
	$(PY) scripts/fetch_stock_price.py
	@echo "── short interest (yfinance snap + seed) ────────────"
	$(PY) scripts/fetch_short_interest.py
	@echo "── insider trades (EDGAR Form 4 + seed) ─────────────"
	$(PY) scripts/fetch_insider_trades.py
	@echo "── reddit (vital farms + linoleic pass) ─────────────"
	$(PY) scripts/fetch_reddit_arctic.py
	@echo "── competitor mentions ──────────────────────────────"
	$(PY) scripts/fetch_competitor_mentions.py
	@echo "── news (gdelt + google news rss) ───────────────────"
	$(PY) scripts/fetch_google_news.py
	@echo "── egg prices (BLS CPI + seed for USDA AMS) ─────────"
	$(PY) scripts/fetch_egg_prices.py
	@echo "── hpai / layer flock (APHIS + seed) ────────────────"
	$(PY) scripts/fetch_hpai.py
	@echo "── youtube (skipped if YOUTUBE_API_KEY missing) ─────"
	$(PY) scripts/fetch_youtube.py || echo "  [warn] youtube fetcher failed — continuing"
	@echo "── compute correlations (no external fetch) ─────────"
	$(PY) scripts/compute_correlations.py
	@echo "── regenerate dashboard ─────────────────────────────"
	$(PY) scripts/generate_vitl_dashboard.py

refresh-fast:
	@echo "── stock ────────────────────────────────────────────"
	$(PY) scripts/fetch_stock_price.py
	@echo "── short interest ───────────────────────────────────"
	$(PY) scripts/fetch_short_interest.py
	@echo "── insider trades ───────────────────────────────────"
	$(PY) scripts/fetch_insider_trades.py
	@echo "── reddit ───────────────────────────────────────────"
	$(PY) scripts/fetch_reddit_arctic.py
	@echo "── news ─────────────────────────────────────────────"
	$(PY) scripts/fetch_google_news.py
	@echo "── competitor mentions ──────────────────────────────"
	$(PY) scripts/fetch_competitor_mentions.py
	@echo "── egg prices ───────────────────────────────────────"
	$(PY) scripts/fetch_egg_prices.py
	@echo "── hpai ─────────────────────────────────────────────"
	$(PY) scripts/fetch_hpai.py
	@echo "── compute correlations ─────────────────────────────"
	$(PY) scripts/compute_correlations.py
	@echo "── regenerate dashboard ─────────────────────────────"
	$(PY) scripts/generate_vitl_dashboard.py

generate:
	$(PY) scripts/generate_vitl_dashboard.py

clean-data:
	rm -f data/*.csv data/*.json
