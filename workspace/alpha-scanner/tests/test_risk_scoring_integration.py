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
            VALUES ('base', 'token_risk', 'RISK', 'Risk Token', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'https://risk.example')
            """
        )
        conn.execute(
            """
            INSERT INTO pairs (
                chain, pair_address, token_address, quote_symbol, dex, pair_created_at,
                liquidity_usd, fdv, market_cap, price_usd, volume_5m, volume_1h, volume_4h,
                buys_1h, sells_1h, txns_1h, snapshot_at
            ) VALUES (
                'base', 'pair_risk', 'token_risk', 'WETH', 'uniswap', datetime('now'),
                210000, 12000000, 12000000, 0.6, 15000, 100000, 190000,
                90, 55, 145, CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            INSERT INTO risk_profiles (
                token_address, chain, verified_contract, mint_authority, freeze_authority,
                proxy_contract, ownership_flags, blacklist_flags, risk_level, risk_reasons, snapshot_at
            ) VALUES (
                'token_risk', 'base', 1, 1, 0, 1, '["proxy_contract"]', '[]', 'warning', '["proxy_contract"]', CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            INSERT INTO holder_snapshots (
                token_address, chain, holder_count, top_10_pct, top_20_pct, creator_pct, snapshot_at
            ) VALUES (
                'token_risk', 'base', 1300, 22.0, 33.0, 4.0, CURRENT_TIMESTAMP
            )
            """
        )


def test_load_latest_candidates_uses_risk_snapshots(tmp_path, monkeypatch):
    db_path = tmp_path / 'scanner.db'
    monkeypatch.setenv('DB_PATH', str(db_path))

    from scripts.init_db import main as init_db_main

    init_db_main()
    seed_data()

    candidates = load_latest_candidates()
    target = next(candidate for candidate in candidates if candidate.token_address == 'token_risk')

    assert target.verified_contract is True
    assert target.mint_authority is True
    assert target.proxy_contract is True
