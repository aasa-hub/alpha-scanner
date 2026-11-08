from typing import Dict, List

from app.db import get_connection


def load_tokens_for_socials() -> List[Dict[str, object]]:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT chain, token_address, twitter_url, telegram_url, website_url, github_url
        FROM tokens
        ORDER BY last_seen_at DESC
        """
    ).fetchall()
    return [dict(row) for row in rows]


def save_social_snapshot(chain: str, token_address: str, metrics: Dict[str, object]) -> None:
    conn = get_connection()
    with conn:
        conn.execute(
            """
            INSERT INTO social_snapshots (
                token_address, chain, twitter_mentions_1h, telegram_exists, website_exists,
                domain_age_days, github_exists, github_recent_activity, farcaster_mentions_24h
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                token_address,
                chain,
                metrics["twitter_mentions_1h"],
                int(bool(metrics["telegram_exists"])),
                int(bool(metrics["website_exists"])),
                metrics["domain_age_days"],
                int(bool(metrics["github_exists"])),
                metrics["github_recent_activity"],
                metrics["farcaster_mentions_24h"],
            ),
        )


def count_social_snapshots() -> int:
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) AS count FROM social_snapshots").fetchone()
    return int(row["count"])
