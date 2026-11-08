from typing import Any, Dict, List

from app.config import BIRDEYE_API_KEY


class BirdeyeClient:
    def headers(self) -> Dict[str, str]:
        return {
            "X-API-KEY": BIRDEYE_API_KEY,
            "accept": "application/json",
        }

    def is_configured(self) -> bool:
        return bool(BIRDEYE_API_KEY)

    def top_holders(self, token_address: str) -> List[Dict[str, Any]]:
        # TODO: wire real Solana holder enrichment when API access is available.
        return []
