import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db import get_connection
from app.jobs.score_tokens import run


def seed_minimal_data() -> None:
    conn = get_connection()
    with conn:
        conn.execute(
            """
            INSERT INTO tokens (chain, token_address, symbol, name, first_seen_at, last_seen_at, website_url)
            VALUES ('solana', 'token_sol', 'SOLX', 'Sol X', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'https://solx.example')
            """
        )
        conn.execute(
            """
            INSERT INTO pairs (
                chain, pair_address, token_address, quote_symbol, dex, pair_created_at,
                liquidity_usd, fdv, market_cap, price_usd, volume_5m, volume_1h, volume_4h,
                buys_1h, sells_1h, txns_1h, snapshot_at
            ) VALUES (
                'solana', 'pair_sol', 'token_sol', 'SOL', 'raydium', datetime('now'),
                150000, 900000, 900000, 0.01, 10000, 250000, 400000,
                120, 80, 200, CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            INSERT INTO tokens (
                chain, token_address, symbol, name, first_seen_at, last_seen_at,
                website_url, github_url, twitter_url, telegram_url
            ) VALUES (
                'base', 'token_base', 'BASX', 'Base X', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
                'https://basex.example', 'https://github.com/example/basex', 'https://x.com/basex', 'https://t.me/basex'
            )
            """
        )
        conn.execute(
            """
            INSERT INTO pairs (
                chain, pair_address, token_address, quote_symbol, dex, pair_created_at,
                liquidity_usd, fdv, market_cap, price_usd, volume_5m, volume_1h, volume_4h,
                buys_1h, sells_1h, txns_1h, snapshot_at
            ) VALUES (
                'base', 'pair_base', 'token_base', 'WETH', 'uniswap', datetime('now'),
                180000, 8000000, 8000000, 0.2, 15000, 140000, 300000,
                150, 90, 240, CURRENT_TIMESTAMP
            )
            """
        )


def test_scoring_job_persists_scores(tmp_path, monkeypatch):
    db_path = tmp_path / 'scanner.db'
    monkeypatch.setenv('DB_PATH', str(db_path))

    from scripts.init_db import main as init_db_main

    init_db_main()
    seed_minimal_data()

    counts = run()

    assert counts['sol_meme'] == 1
    assert counts['base_meme'] == 1
    assert counts['base_utility'] == 1

    conn = get_connection()
    total_scores = conn.execute('SELECT COUNT(*) AS count FROM scores').fetchone()['count']
    assert total_scores == 3
