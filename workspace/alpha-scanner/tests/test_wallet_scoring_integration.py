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
            VALUES ('solana', 'token_wallet', 'WALT', 'Wallet Token', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'https://wallet.example')
            """
        )
        conn.execute(
            """
            INSERT INTO pairs (
                chain, pair_address, token_address, quote_symbol, dex, pair_created_at,
                liquidity_usd, fdv, market_cap, price_usd, volume_5m, volume_1h, volume_4h,
                buys_1h, sells_1h, txns_1h, snapshot_at
            ) VALUES (
                'solana', 'pair_wallet', 'token_wallet', 'SOL', 'raydium', datetime('now'),
                190000, 1100000, 1100000, 0.3, 18000, 105000, 160000,
                100, 70, 170, CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            INSERT INTO wallet_signals (
                token_address, chain, tracked_wallet_buys_count, tracked_wallet_sell_count,
                tracked_wallet_netflow_usd, insider_flag, snapshot_at
            ) VALUES (
                'token_wallet', 'solana', 2, 0, 5000, 0, CURRENT_TIMESTAMP
            )
            """
        )


def test_load_latest_candidates_uses_wallet_snapshots(tmp_path, monkeypatch):
    db_path = tmp_path / 'scanner.db'
    monkeypatch.setenv('DB_PATH', str(db_path))

    from scripts.init_db import main as init_db_main

    init_db_main()
    seed_data()

    candidates = load_latest_candidates()
    target = next(candidate for candidate in candidates if candidate.token_address == 'token_wallet')

    assert target.tracked_wallet_buys_count == 2
