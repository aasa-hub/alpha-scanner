from app.config import BASESCAN_API_KEY


class BasescanClient:
    def is_configured(self) -> bool:
        return bool(BASESCAN_API_KEY)
