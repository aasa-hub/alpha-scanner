from typing import Dict

from app.clients.basescan import BasescanClient
from app.clients.birdeye import BirdeyeClient
from app.services.holders import (
    compute_holder_metrics,
    load_latest_base_tokens,
    load_latest_solana_tokens,
    save_holder_snapshot,
)


def run() -> Dict[str, int]:
    base_client = BasescanClient()
    solana_client = BirdeyeClient()
    saved = {
        "base": 0,
        "solana": 0,
    }

    if base_client.is_configured():
        for token_address in load_latest_base_tokens():
            holders = base_client.top_holders(token_address)
            if not holders:
                continue
            metrics = compute_holder_metrics(holders)
            save_holder_snapshot("base", token_address, metrics)
            saved["base"] += 1

    if solana_client.is_configured():
        for token_address in load_latest_solana_tokens():
            holders = solana_client.top_holders(token_address)
            if not holders:
                continue
            metrics = compute_holder_metrics(holders)
            save_holder_snapshot("solana", token_address, metrics)
            saved["solana"] += 1

    return saved
