from typing import Dict

from app.clients.basescan import BasescanClient
from app.services.risk_profiles import (
    analyze_base_contract,
    count_risk_profiles,
    load_latest_base_tokens,
    save_risk_profile,
)


def run() -> Dict[str, int]:
    client = BasescanClient()
    saved = {
        "base": 0,
        "solana": 0,
    }

    if not client.is_configured():
        return saved

    for token_address in load_latest_base_tokens():
        source = client.source_code(token_address)
        if not source:
            continue
        profile = analyze_base_contract(source)
        save_risk_profile("base", token_address, profile)
        saved["base"] += 1

    return saved
