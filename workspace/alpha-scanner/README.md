# Alpha Scanner MVP

Semi-automated Solana + Base alpha scanner for early meme and utility coin discovery.

## MVP features
- Real DexScreener pair discovery for Solana and Base
- SQLite token + pair snapshot persistence
- Base-first holder enrichment with Solana fallback scaffolding
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

## Environment
Copy `.env.example` to `.env` and fill in keys as needed.

For Telegram delivery, set:
```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=5815439260
```

## Current ingestion behavior
`python scripts/run_once.py` will:
- query DexScreener for Solana and Base pairs
- normalize pair data
- upsert tokens into SQLite
- insert pair snapshots into SQLite
- enrich holder snapshots (Base first, Solana fallback)
- compute and store strategy scores
- generate deduped threshold-based alerts
- send alerts to Telegram when configured
- print a short storage summary
