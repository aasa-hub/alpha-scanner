from typing import Any, Dict


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_dexscreener_pair(raw_pair: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "chain": raw_pair.get("chainId", ""),
        "token_address": raw_pair.get("baseToken", {}).get("address", ""),
        "symbol": raw_pair.get("baseToken", {}).get("symbol", ""),
        "name": raw_pair.get("baseToken", {}).get("name", ""),
        "pair_address": raw_pair.get("pairAddress", ""),
        "dex": raw_pair.get("dexId", ""),
        "liquidity_usd": safe_float(raw_pair.get("liquidity", {}).get("usd")),
        "volume_1h": safe_float(raw_pair.get("volume", {}).get("h1")),
        "fdv": safe_float(raw_pair.get("fdv")),
    }
