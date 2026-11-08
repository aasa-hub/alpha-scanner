import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db import get_connection
from app.services.scoring import load_latest_candidates


def seed_data() -> None:
    conn = get_connection()
    with conn:
        conn.execute(
            """
            INSERT INTO tokens (chain, token_address, symbol, name, first_seen_at, last_seen_at, website_url)
            VALUES ('base', 'token_holder', 'HOLD', 'Holder Token', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'https://holder.example')
            """
        )
        conn.execute(
            """
            INSERT INTO pairs (
                chain, pair_address, token_address, quote_symbol, dex, pair_created_at,
                liquidity_usd, fdv, market_cap, price_usd, volume_5m, volume_1h, volume_4h,
                buys_1h, sells_1h, txns_1h, snapshot_at
            ) VALUES (
                'base', 'pair_holder', 'token_holder', 'WETH', 'uniswap', datetime('now'),
                180000, 9000000, 9000000, 0.5, 12000, 90000, 150000,
                80, 50, 130, CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            INSERT INTO holder_snapshots (
                token_address, chain, holder_count, top_10_pct, top_20_pct, creator_pct, snapshot_at
            ) VALUES (
                'token_holder', 'base', 2450, 28.5, 41.0, 8.1, CURRENT_TIMESTAMP
            )
            """
        )


def test_load_latest_candidates_uses_holder_snapshots(tmp_path, monkeypatch):
    db_path = tmp_path / 'scanner.db'
    monkeypatch.setenv('DB_PATH', str(db_path))

    from scripts.init_db import main as init_db_main

    init_db_main()
    seed_data()

    candidates = load_latest_candidates()
    target = next(candidate for candidate in candidates if candidate.token_address == 'token_holder')

    assert target.holder_count == 2450
    assert target.top_10_pct == 28.5
    assert target.creator_pct == 8.1
