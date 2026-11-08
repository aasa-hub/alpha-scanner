from typing import Dict

from app.clients.basescan import BasescanClient
from app.clients.birdeye import BirdeyeClient
from app.services.risk_profiles import (
    analyze_base_contract,
    load_latest_base_tokens,
    save_risk_profile,
)
from app.services.solana_risk import (
    analyze_token_security,
    load_latest_solana_tokens,
    save_risk_profile as save_solana_risk_profile,
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
            source = base_client.source_code(token_address)
            if not source:
                continue
            profile = analyze_base_contract(source)
            save_risk_profile("base", token_address, profile)
            saved["base"] += 1

    if solana_client.is_configured():
        for token_address in load_latest_solana_tokens():
            security_data = solana_client.token_security(token_address)
            if not security_data:
                continue
            profile = analyze_token_security(security_data)
            save_solana_risk_profile("solana", token_address, profile)
            saved["solana"] += 1

    return saved
