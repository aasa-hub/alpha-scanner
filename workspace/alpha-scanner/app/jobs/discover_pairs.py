from app.clients.dexscreener import DexScreenerClient


QUERIES = ["solana", "base"]


def run() -> dict:
    client = DexScreenerClient()
    return {query: client.fetch_pairs(query) for query in QUERIES}
