from typing import Any, Dict, List

import requests

from app.config import BIRDEYE_API_KEY


class BirdeyeClient:
    BASE_URL = "https://public-api.birdeye.so"

    def headers(self) -> Dict[str, str]:
        return {
            "X-API-KEY": BIRDEYE_API_KEY,
            "accept": "application/json",
        }

    def is_configured(self) -> bool:
        return bool(BIRDEYE_API_KEY)

    def _get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        response = requests.get(
            f"{self.BASE_URL}{path}",
            params=params,
            headers=self.headers(),
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    def top_holders(self, token_address: str) -> List[Dict[str, Any]]:
        # TODO: wire real Solana holder enrichment when API access is available.
        return []

    def token_security(self, token_address: str) -> Dict[str, Any]:
        if not self.is_configured():
            return {}
        payload = self._get("/defi/token_security", {"address": token_address})
        data = payload.get("data") or {}
        return data if isinstance(data, dict) else {}

    def token_trades(self, token_address: str, limit: int = 50) -> List[Dict[str, Any]]:
        if not self.is_configured():
            return []
        payload = self._get("/defi/txs/token", {"address": token_address, "limit": limit})
        data = payload.get("data") or {}
        items = data.get("items") if isinstance(data, dict) else []
        return items if isinstance(items, list) else []
