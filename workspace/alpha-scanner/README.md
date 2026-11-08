# Alpha Scanner MVP

Semi-automated **Solana + Base** alpha scanner for early meme coin and utility token discovery.

This project is designed as a practical MVP for:
- discovering new token pairs
- enriching them with onchain and heuristic signals
- scoring candidates by strategy
- generating deduped alerts
- sending alerts to Telegram
- running continuously on a scheduler loop

---

## What it does

The current pipeline runs in this order:

1. **Pair discovery**
   - pulls Solana and Base pairs from DexScreener
2. **Holder enrichment**
   - Base-first holder concentration snapshots
   - Solana fallback scaffold
3. **Social enrichment**
   - lightweight social presence snapshots from known links
4. **Wallet tracking**
   - tracked-wallet participation snapshots
5. **Risk enrichment**
   - Base contract/source heuristics
   - Solana authority-risk checks
6. **Scoring**
   - Solana meme scoring
   - Base meme scoring
   - Base utility scoring
7. **Alerts**
   - threshold filtering
   - dedupe against prior alerts
   - Telegram delivery when configured

---

## Current MVP features

- Real DexScreener pair discovery for **Solana** and **Base**
- SQLite storage for tokens, pairs, scores, alerts, and enrichment snapshots
- Base-first holder enrichment
- Social enrichment snapshots feeding scores
- Wallet tracking snapshots feeding scores
- Base contract/risk enrichment
- Solana authority-risk enrichment
- Strategy-specific scoring functions
- Threshold-based alert generation with alert dedupe
- Telegram alert delivery
- Continuous scheduler loop

---

## Project structure

```text
alpha-scanner/
├── app/
│   ├── clients/        # external API wrappers
│   ├── jobs/           # scheduled pipeline tasks
│   ├── services/       # DB, enrichment, alerting, pipeline logic
│   ├── strategies/     # scoring rules per strategy
│   ├── utils/          # shared helpers
│   ├── config.py
│   ├── db.py
│   ├── models.py
│   └── schemas.py
├── data/               # local SQLite DB (ignored by git)
├── scripts/            # runnable entrypoints
├── tests/              # focused tests for scoring/enrichment logic
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/init_db.py
python scripts/run_once.py
PYTHONPATH=. pytest
```

---

## Running the scanner

### One-shot run
Use this for a single pipeline pass:

```bash
python scripts/run_once.py
```

### Continuous scheduler loop
Use this to keep the scanner running:

```bash
python scripts/run_scheduler.py
```

Optional interval override:

```env
SCHEDULER_INTERVAL_SECONDS=300
```

Default interval is **300 seconds** (5 minutes).

---

## Environment setup

Copy `.env.example` to `.env` and fill in only the values you need.

### Core optional keys

```env
DB_PATH=data/scanner.db
DEXSCREENER_BASE_URL=https://api.dexscreener.com/latest/dex
GECKOTERMINAL_BASE_URL=https://api.geckoterminal.com/api/v2
BIRDEYE_API_KEY=
BASESCAN_API_KEY=
```

### Telegram alerts

```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=5815439260
```

### Tracked wallet scoring

```env
TRACKED_WALLETS=wallet1,wallet2,wallet3
```

### Scheduler interval

```env
SCHEDULER_INTERVAL_SECONDS=300
```

---

## Contributor-safe setup notes

### Never commit these
- `.env`
- `.venv/`
- `data/scanner.db`
- any API tokens or wallet credentials

These are already covered in `.gitignore`, but contributors should still double-check before pushing.

### Recommended local workflow

```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/init_db.py
python scripts/run_once.py
```

### Before opening a PR
- run `PYTHONPATH=. pytest`
- verify no secrets are staged
- verify no local DB file is staged
- keep commits focused by feature

---

## Alert behavior

Alerts are only generated when:
- the score exceeds the strategy threshold
- and either no prior alert exists
- or the score improves by a meaningful delta

Telegram messages currently include:
- strategy label
- token and chain
- score
- alert level
- risk level
- liquidity
- 1h volume
- pair age
- top 10 holder concentration
- tracked wallet buy count

---

## Important limitations

This is an MVP and some parts are still heuristic.

### Social enrichment
Current social signals are derived from stored links and lightweight heuristics, not full live social scraping.

### Base risk enrichment
Current Base contract analysis is heuristic and based on source verification, proxy flags, and suspicious term matching.

### Solana risk enrichment
Current Solana risk checks are a first-pass authority/security layer, not full token forensics.

### Wallet tracking
Wallet tracking only becomes useful when `TRACKED_WALLETS` is configured with meaningful wallets.

---

## Suggested next upgrades

- Real X/Twitter/Farcaster/Telegram social ingestion
- Better smart-wallet tagging and wallet-performance tracking
- Background process supervision / deployment hardening
- Richer Telegram alert score breakdowns
- Historical analytics and backtesting

---

## Safety note

This tool helps surface candidates. It does **not** guarantee profitable trades.
Early token trading carries high risk, including scams, rugs, low liquidity, and manipulated volume.
Use small sizing and verify signals manually before acting.
