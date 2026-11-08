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
            INSERT INTO tokens (
                chain, token_address, symbol, name, first_seen_at, last_seen_at,
                website_url, twitter_url, telegram_url, github_url
            ) VALUES (
                'base', 'token_social', 'SOC', 'Social Token', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
                'https://social.example', 'https://x.com/social', 'https://t.me/social', 'https://github.com/example/social'
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
                'base', 'pair_social', 'token_social', 'WETH', 'uniswap', datetime('now'),
                150000, 7000000, 7000000, 0.4, 12000, 85000, 140000,
                70, 45, 115, CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            INSERT INTO social_snapshots (
                token_address, chain, twitter_mentions_1h, telegram_exists, website_exists,
                domain_age_days, github_exists, github_recent_activity, farcaster_mentions_24h, snapshot_at
            ) VALUES (
                'token_social', 'base', 18, 1, 1, 30, 1, 1, 2, CURRENT_TIMESTAMP
            )
            """
        )


def test_load_latest_candidates_uses_social_snapshots(tmp_path, monkeypatch):
    db_path = tmp_path / 'scanner.db'
    monkeypatch.setenv('DB_PATH', str(db_path))

    from scripts.init_db import main as init_db_main

    init_db_main()
    seed_data()

    candidates = load_latest_candidates()
    target = next(candidate for candidate in candidates if candidate.token_address == 'token_social')

    assert target.twitter_mentions_1h == 18
    assert target.telegram_exists is True
    assert target.website_exists is True
    assert target.github_exists is True
