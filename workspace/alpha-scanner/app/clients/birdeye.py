from typing import Any, Dict

from app.config import BIRDEYE_API_KEY


class BirdeyeClient:
    def headers(self) -> Dict[str, str]:
        return {
            "X-API-KEY": BIRDEYE_API_KEY,
            "accept": "application/json",
        }

    def is_configured(self) -> bool:
        return bool(BIRDEYE_API_KEY)
