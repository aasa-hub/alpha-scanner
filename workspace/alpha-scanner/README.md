# Alpha Scanner MVP

Semi-automated Solana + Base alpha scanner for early meme and utility coin discovery.

## MVP features
- Pair discovery scaffolding for Solana and Base
- SQLite database initialization
- Strategy-specific scoring functions
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
