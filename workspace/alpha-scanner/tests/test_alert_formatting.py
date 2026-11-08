import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.services.alerting import build_alert_summary


def test_build_alert_summary_contains_rich_fields():
    summary = build_alert_summary(
        {
            'strategy_type': 'sol_meme',
            'symbol': 'SAM',
            'chain': 'solana',
            'score_total': 88,
            'alert_level': 'high_priority',
            'risk_level': 'warning',
            'liquidity_usd': 125000,
            'volume_1h': 260000,
            'pair_age_minutes': 42,
            'top_10_pct': 21.5,
            'tracked_wallet_buys_count': 3,
        }
    )

    assert 'SOL MEME' in summary
    assert 'Liquidity: $125,000' in summary
    assert '1h Volume: $260,000' in summary
    assert 'Tracked Wallet Buys: 3' in summary
