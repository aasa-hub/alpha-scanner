from typing import Dict

from app.clients.socials import SocialSignalsClient
from app.services.socials import load_tokens_for_socials, save_social_snapshot


def run() -> Dict[str, int]:
    client = SocialSignalsClient()
    saved = {
        "solana": 0,
        "base": 0,
    }

    for token_record in load_tokens_for_socials():
        metrics = client.derive_metrics(token_record)
        save_social_snapshot(str(token_record["chain"]), str(token_record["token_address"]), metrics)
        saved[str(token_record["chain"])] = saved.get(str(token_record["chain"]), 0) + 1

    return saved
