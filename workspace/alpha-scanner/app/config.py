import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "data/scanner.db")

DEXSCREENER_BASE_URL = os.getenv(
    "DEXSCREENER_BASE_URL", "https://api.dexscreener.com/latest/dex"
)
GECKOTERMINAL_BASE_URL = os.getenv(
    "GECKOTERMINAL_BASE_URL", "https://api.geckoterminal.com/api/v2"
)

BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY", "")
BASESCAN_API_KEY = os.getenv("BASESCAN_API_KEY", "")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

SOLANA_MIN_LIQUIDITY = int(os.getenv("SOLANA_MIN_LIQUIDITY", "25000"))
BASE_MIN_LIQUIDITY = int(os.getenv("BASE_MIN_LIQUIDITY", "35000"))
SOLANA_ALERT_THRESHOLD = int(os.getenv("SOLANA_ALERT_THRESHOLD", "75"))
BASE_MEME_ALERT_THRESHOLD = int(os.getenv("BASE_MEME_ALERT_THRESHOLD", "75"))
BASE_UTILITY_ALERT_THRESHOLD = int(os.getenv("BASE_UTILITY_ALERT_THRESHOLD", "80"))
