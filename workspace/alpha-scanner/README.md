# Alpha Scanner MVP

Semi-automated Solana + Base alpha scanner for early meme and utility coin discovery.

## MVP features
- Real DexScreener pair discovery for Solana and Base
- SQLite token + pair snapshot persistence
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

## Current ingestion behavior
`python scripts/run_once.py` will:
- query DexScreener for Solana and Base pairs
- normalize pair data
- upsert tokens into SQLite
- insert pair snapshots into SQLite
- compute and store strategy scores
- generate deduped threshold-based alerts
- print a short storage summary
