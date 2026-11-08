from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db import get_connection

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chain TEXT NOT NULL,
    token_address TEXT NOT NULL,
    symbol TEXT,
    name TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    first_seen_at TEXT,
    last_seen_at TEXT,
    discovery_sources TEXT,
    website_url TEXT,
    twitter_url TEXT,
    telegram_url TEXT,
    github_url TEXT,
    UNIQUE(chain, token_address)
);

CREATE TABLE IF NOT EXISTS pairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chain TEXT NOT NULL,
    pair_address TEXT NOT NULL,
    token_address TEXT NOT NULL,
    quote_symbol TEXT,
    dex TEXT,
    pair_created_at TEXT,
    liquidity_usd REAL,
    fdv REAL,
    market_cap REAL,
    price_usd REAL,
    volume_5m REAL,
    volume_1h REAL,
    volume_4h REAL,
    buys_1h INTEGER,
    sells_1h INTEGER,
    txns_1h INTEGER,
    snapshot_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(chain, pair_address, snapshot_at)
);

CREATE TABLE IF NOT EXISTS holder_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_address TEXT NOT NULL,
    chain TEXT NOT NULL,
    holder_count INTEGER,
    top_10_pct REAL,
    top_20_pct REAL,
    creator_pct REAL,
    snapshot_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS risk_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_address TEXT NOT NULL,
    chain TEXT NOT NULL,
    verified_contract INTEGER,
    mint_authority INTEGER,
    freeze_authority INTEGER,
    proxy_contract INTEGER,
    ownership_flags TEXT,
    blacklist_flags TEXT,
    risk_level TEXT,
    risk_reasons TEXT,
    snapshot_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS social_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_address TEXT NOT NULL,
    chain TEXT NOT NULL,
    twitter_mentions_1h INTEGER,
    telegram_exists INTEGER,
    website_exists INTEGER,
    domain_age_days INTEGER,
    github_exists INTEGER,
    github_recent_activity INTEGER,
    farcaster_mentions_24h INTEGER,
    snapshot_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS wallet_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_address TEXT NOT NULL,
    chain TEXT NOT NULL,
    tracked_wallet_buys_count INTEGER,
    tracked_wallet_sell_count INTEGER,
    tracked_wallet_netflow_usd REAL,
    insider_flag INTEGER,
    snapshot_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_address TEXT NOT NULL,
    chain TEXT NOT NULL,
    strategy_type TEXT NOT NULL,
    score_total REAL,
    score_components TEXT,
    risk_level TEXT,
    computed_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_address TEXT NOT NULL,
    chain TEXT NOT NULL,
    strategy_type TEXT NOT NULL,
    alert_level TEXT NOT NULL,
    score_total REAL,
    message_hash TEXT,
    sent_to TEXT,
    sent_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def main() -> None:
    conn = get_connection()
    with conn:
        conn.executescript(SCHEMA_SQL)
    print("Database initialized.")


if __name__ == "__main__":
    main()
