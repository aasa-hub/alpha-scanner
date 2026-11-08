from typing import Optional

import requests

from app.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


class TelegramConfigError(RuntimeError):
    pass


class TelegramSendError(RuntimeError):
    pass


def is_configured() -> bool:
    return bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)


def send_message(text: str) -> dict:
    if not is_configured():
        raise TelegramConfigError("Telegram bot token or chat id is not configured")

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    response = requests.post(
        url,
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "disable_web_page_preview": True,
        },
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    if not payload.get("ok"):
        raise TelegramSendError(f"Telegram API error: {payload}")
    return payload


def configured_target() -> Optional[str]:
    if not is_configured():
        return None
    return f"telegram:{TELEGRAM_CHAT_ID}"
