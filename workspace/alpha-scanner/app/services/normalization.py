from datetime import datetime, timezone
from typing import Any, Dict, Optional


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def epoch_ms_to_iso(value: Any) -> Optional[str]:
    if value in (None, ""):
        return None
    try:
        timestamp = float(value) / 1000
        return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return None


def pair_age_minutes(pair_created_at_ms: Any) -> int:
    if pair_created_at_ms in (None, ""):
        return 0
    try:
        created_at = float(pair_created_at_ms) / 1000
        now = datetime.now(tz=timezone.utc).timestamp()
        return max(0, int((now - created_at) / 60))
    except (TypeError, ValueError, OSError):
        return 0


def extract_links(info: Dict[str, Any]) -> Dict[str, Optional[str]]:
    websites = info.get("websites") or []
    socials = info.get("socials") or []

    website = websites[0].get("url") if websites else None
    twitter = None
    telegram = None
    github = None

    for social in socials:
        social_type = (social.get("type") or "").lower()
        url = social.get("url")
        if social_type == "twitter" and not twitter:
            twitter = url
        elif social_type == "telegram" and not telegram:
            telegram = url
        elif social_type == "github" and not github:
            github = url

    return {
        "website": website,
        "twitter": twitter,
        "telegram": telegram,
        "github": github,
    }


def normalize_dexscreener_pair(raw_pair: Dict[str, Any]) -> Dict[str, Any]:
    pair_created_at_ms = raw_pair.get("pairCreatedAt")
    txns_h1 = raw_pair.get("txns", {}).get("h1", {})

    return {
        "chain": raw_pair.get("chainId", ""),
        "token_address": raw_pair.get("baseToken", {}).get("address", ""),
        "symbol": raw_pair.get("baseToken", {}).get("symbol", ""),
        "name": raw_pair.get("baseToken", {}).get("name", ""),
        "pair_address": raw_pair.get("pairAddress", ""),
        "quote_symbol": raw_pair.get("quoteToken", {}).get("symbol", ""),
        "dex": raw_pair.get("dexId", ""),
        "price_usd": safe_float(raw_pair.get("priceUsd")),
        "liquidity_usd": safe_float(raw_pair.get("liquidity", {}).get("usd")),
        "volume_5m": safe_float(raw_pair.get("volume", {}).get("m5")),
        "volume_1h": safe_float(raw_pair.get("volume", {}).get("h1")),
        "volume_4h": safe_float(raw_pair.get("volume", {}).get("h4")),
        "fdv": safe_float(raw_pair.get("fdv")),
        "market_cap": safe_float(raw_pair.get("marketCap")),
        "pair_created_at": epoch_ms_to_iso(pair_created_at_ms),
        "pair_age_minutes": pair_age_minutes(pair_created_at_ms),
        "buys_1h": safe_int(txns_h1.get("buys")),
        "sells_1h": safe_int(txns_h1.get("sells")),
        "txns_1h": safe_int(txns_h1.get("buys")) + safe_int(txns_h1.get("sells")),
        "links": extract_links(raw_pair.get("info", {})),
        "url": raw_pair.get("url"),
    }
