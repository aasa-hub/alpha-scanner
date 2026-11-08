import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.services.wallet_tracking import compute_wallet_metrics


def test_compute_wallet_metrics_counts_tracked_wallet_buys(monkeypatch):
    monkeypatch.setenv('TRACKED_WALLETS', 'wallet1,wallet2')

    trades = [
        {'owner': 'wallet1', 'side': 'buy', 'amount_usd': 100},
        {'owner': 'wallet2', 'side': 'sell', 'amount_usd': 40},
        {'owner': 'wallet3', 'side': 'buy', 'amount_usd': 80},
    ]

    metrics = compute_wallet_metrics(trades)

    assert metrics['tracked_wallet_buys_count'] == 1
    assert metrics['tracked_wallet_sell_count'] == 1
    assert metrics['tracked_wallet_netflow_usd'] == 60.0
