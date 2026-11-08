from typing import Any, Dict

import requests

from app.config import GECKOTERMINAL_BASE_URL


class GeckoTerminalClient:
    def ping(self) -> Dict[str, Any]:
        response = requests.get(f"{GECKOTERMINAL_BASE_URL}/networks", timeout=20)
        response.raise_for_status()
        return response.json()
