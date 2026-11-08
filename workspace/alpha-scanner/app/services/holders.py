from typing import Dict, List, Tuple

from app.db import get_connection


def compute_holder_metrics(holders: List[dict]) -> Dict[str, float]:
    if not holders:
        return {
            "holder_count": 0,
            "top_10_pct": 0,
            "top_20_pct": 0,
            "creator_pct": 0,
        }

    percentages: List[float] = []
    creator_pct = 0.0

    for index, holder in enumerate(holders):
        raw_pct = holder.get("percentage") or holder.get("share") or holder.get("percent") or 0
        try:
            pct = float(str(raw_pct).replace('%', ''))
        except ValueError:
            pct = 0.0
        percentages.append(pct)
        if index == 0:
            creator_pct = pct

    return {
        "holder_count": len(holders),
        "top_10_pct": round(sum(percentages[:10]), 4),
        "top_20_pct": round(sum(percentages[:20]), 4),
        "creator_pct": round(creator_pct, 4),
    }


def save_holder_snapshot(chain: str, token_address: str, metrics: Dict[str, float]) -> None:
    conn = get_connection()
    with conn:
        conn.execute(
            """
            INSERT INTO holder_snapshots (
                token_address, chain, holder_count, top_10_pct, top_20_pct, creator_pct
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                token_address,
                chain,
                metrics["holder_count"],
                metrics["top_10_pct"],
                metrics["top_20_pct"],
                metrics["creator_pct"],
            ),
        )


def load_latest_base_tokens() -> List[str]:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT DISTINCT token_address
        FROM tokens
        WHERE chain = 'base'
        ORDER BY last_seen_at DESC
        """
    ).fetchall()
    return [row["token_address"] for row in rows]


def load_latest_solana_tokens() -> List[str]:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT DISTINCT token_address
        FROM tokens
        WHERE chain = 'solana'
        ORDER BY last_seen_at DESC
        """
    ).fetchall()
    return [row["token_address"] for row in rows]


def count_holder_snapshots() -> int:
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) AS count FROM holder_snapshots").fetchone()
    return int(row["count"])
