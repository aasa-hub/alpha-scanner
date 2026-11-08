from typing import Any, Dict, List

import requests

from app.config import DEXSCREENER_BASE_URL


class DexScreenerClient:
    def search_pairs(self, query: str) -> List[Dict[str, Any]]:
        url = f"{DEXSCREENER_BASE_URL}/search"
        response = requests.get(url, params={"q": query}, timeout=20)
        response.raise_for_status()
        payload = response.json()
        return payload.get("pairs", [])
