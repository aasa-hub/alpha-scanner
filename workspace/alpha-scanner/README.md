# Alpha Scanner MVP

Semi-automated Solana + Base alpha scanner for early meme and utility coin discovery.

## MVP features
- Real DexScreener pair discovery for Solana and Base
- SQLite token + pair snapshot persistence
- Base-first holder enrichment with Solana fallback scaffolding
- Social enrichment snapshots feeding scores
- Wallet tracking snapshots feeding scores
- Base contract/risk enrichment with Solana authority-risk fallback
- Strategy-specific scoring functions
- Threshold-based alert generation with alert dedupe
- Simple test coverage for scoring thresholds

## Quick start
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/init_db.py
python scripts/run_once.py
PYTHONPATH=. pytest
```

## Scheduler automation
Run the continuous loop with:
```bash
python scripts/run_scheduler.py
```

Optional interval override:
```env
SCHEDULER_INTERVAL_SECONDS=300
```

## Environment
Copy `.env.example` to `.env` and fill in keys as needed.

For Telegram delivery, set:
```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=5815439260
```

For tracked-wallet scoring, optionally set:
```env
TRACKED_WALLETS=wallet1,wallet2,wallet3
```

## Current ingestion behavior
`python scripts/run_once.py` will:
- query DexScreener for Solana and Base pairs
- normalize pair data
- upsert tokens into SQLite
- insert pair snapshots into SQLite
- enrich holder snapshots (Base first, Solana fallback)
- enrich social snapshots
- enrich tracked wallet snapshots
- enrich Base contract/risk snapshots plus Solana authority-risk snapshots
- compute and store strategy scores
- generate deduped threshold-based alerts
- send rich alerts to Telegram when configured
- print a short storage summary
