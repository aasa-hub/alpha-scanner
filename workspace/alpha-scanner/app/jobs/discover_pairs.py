from typing import Dict, List

from app.clients.dexscreener import DexScreenerClient
from app.services.normalization import normalize_dexscreener_pair
from app.services.token_registry import insert_pair_snapshot, upsert_token

QUERIES = {
    "solana": "chain:solana",
    "base": "chain:base",
}


def _valid_candidate(pair: Dict[str, object], expected_chain: str) -> bool:
    return (
        pair.get("chain") == expected_chain
        and bool(pair.get("token_address"))
        and bool(pair.get("pair_address"))
    )


def run() -> Dict[str, List[Dict[str, object]]]:
    client = DexScreenerClient()
    stored: Dict[str, List[Dict[str, object]]] = {}

    for chain, query in QUERIES.items():
        raw_pairs = client.search_pairs(query)
        normalized_pairs = [normalize_dexscreener_pair(pair) for pair in raw_pairs]
        valid_pairs = [pair for pair in normalized_pairs if _valid_candidate(pair, chain)]

        for pair in valid_pairs:
            upsert_token(
                chain=pair["chain"],
                token_address=pair["token_address"],
                symbol=pair["symbol"],
                name=pair.get("name", ""),
                discovery_source="dexscreener",
                links=pair.get("links") or {},
            )
            insert_pair_snapshot(pair)

        stored[chain] = valid_pairs

    return stored
