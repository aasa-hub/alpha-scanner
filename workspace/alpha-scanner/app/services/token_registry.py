import json
from typing import Any, Dict

from app.db import get_connection


def upsert_token(
    chain: str,
    token_address: str,
    symbol: str,
    name: str = "",
    discovery_source: str = "",
    links: Dict[str, Any] | None = None,
) -> None:
    links = links or {}
    conn = get_connection()
    with conn:
        conn.execute(
            """
            INSERT INTO tokens (
                chain, token_address, symbol, name, first_seen_at, last_seen_at,
                discovery_sources, website_url, twitter_url, telegram_url, github_url
            )
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?)
            ON CONFLICT(chain, token_address) DO UPDATE SET
                symbol=excluded.symbol,
                name=excluded.name,
                last_seen_at=CURRENT_TIMESTAMP,
                discovery_sources=CASE
                    WHEN tokens.discovery_sources IS NULL OR tokens.discovery_sources = '' THEN excluded.discovery_sources
                    WHEN excluded.discovery_sources = '' THEN tokens.discovery_sources
                    WHEN instr(tokens.discovery_sources, excluded.discovery_sources) > 0 THEN tokens.discovery_sources
                    ELSE tokens.discovery_sources || ',' || excluded.discovery_sources
                END,
                website_url=COALESCE(excluded.website_url, tokens.website_url),
                twitter_url=COALESCE(excluded.twitter_url, tokens.twitter_url),
                telegram_url=COALESCE(excluded.telegram_url, tokens.telegram_url),
                github_url=COALESCE(excluded.github_url, tokens.github_url)
            """,
            (
                chain,
                token_address,
                symbol,
                name,
                discovery_source,
                links.get("website"),
                links.get("twitter"),
                links.get("telegram"),
                links.get("github"),
            ),
        )


def insert_pair_snapshot(pair: Dict[str, Any]) -> None:
    conn = get_connection()
    with conn:
        conn.execute(
            """
            INSERT INTO pairs (
                chain, pair_address, token_address, quote_symbol, dex, pair_created_at,
                liquidity_usd, fdv, market_cap, price_usd, volume_5m, volume_1h, volume_4h,
                buys_1h, sells_1h, txns_1h
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pair["chain"],
                pair["pair_address"],
                pair["token_address"],
                pair.get("quote_symbol"),
                pair.get("dex"),
                pair.get("pair_created_at"),
                pair.get("liquidity_usd"),
                pair.get("fdv"),
                pair.get("market_cap"),
                pair.get("price_usd"),
                pair.get("volume_5m"),
                pair.get("volume_1h"),
                pair.get("volume_4h"),
                pair.get("buys_1h"),
                pair.get("sells_1h"),
                pair.get("txns_1h"),
            ),
        )


def count_tokens() -> int:
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) AS count FROM tokens").fetchone()
    return int(row["count"])


def count_pair_snapshots() -> int:
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) AS count FROM pairs").fetchone()
    return int(row["count"])
