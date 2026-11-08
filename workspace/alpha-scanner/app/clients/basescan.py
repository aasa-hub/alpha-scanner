from typing import Any, Dict, List

import requests

from app.config import BASESCAN_API_KEY


class BasescanClient:
    BASE_URL = "https://api.basescan.org/api"

    def is_configured(self) -> bool:
        return bool(BASESCAN_API_KEY)

    def _get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        response = requests.get(
            self.BASE_URL,
            params={**params, "apikey": BASESCAN_API_KEY},
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    def top_holders(self, contract_address: str, limit: int = 20) -> List[Dict[str, Any]]:
        if not self.is_configured():
            return []
        payload = self._get(
            {
                "module": "token",
                "action": "tokenholderlist",
                "contractaddress": contract_address,
                "page": 1,
                "offset": limit,
            }
        )
        if payload.get("status") != "1":
            return []
        result = payload.get("result") or []
        return result if isinstance(result, list) else []

    def source_code(self, contract_address: str) -> Dict[str, Any]:
        if not self.is_configured():
            return {}
        payload = self._get(
            {
                "module": "contract",
                "action": "getsourcecode",
                "address": contract_address,
            }
        )
        result = payload.get("result") or []
        if isinstance(result, list) and result:
            return result[0]
        return {}
