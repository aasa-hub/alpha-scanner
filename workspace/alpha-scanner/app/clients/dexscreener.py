from typing import Any, Dict

import requests

from app.config import DEXSCREENER_BASE_URL


class DexScreenerClient:
    def fetch_pairs(self, query: str) -> Dict[str, Any]:
        url = f"{DEXSCREENER_BASE_URL}/search"
        response = requests.get(url, params={"q": query}, timeout=20)
        response.raise_for_status()
        return response.json()
