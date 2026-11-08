from typing import Dict

from app.clients.birdeye import BirdeyeClient
from app.services.wallet_tracking import (
    compute_wallet_metrics,
    load_latest_tokens,
    save_wallet_snapshot,
)


def run() -> Dict[str, int]:
    client = BirdeyeClient()
    saved = {
        "solana": 0,
        "base": 0,
    }

    if not client.is_configured():
        return saved

    for token_address in load_latest_tokens("solana"):
        trades = client.token_trades(token_address)
        if not trades:
            continue
        metrics = compute_wallet_metrics(trades)
        save_wallet_snapshot("solana", token_address, metrics)
        saved["solana"] += 1

    return saved
