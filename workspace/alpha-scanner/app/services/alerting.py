from typing import Dict, List, Optional

from app.config import (
    BASE_MEME_ALERT_THRESHOLD,
    BASE_UTILITY_ALERT_THRESHOLD,
    SOLANA_ALERT_THRESHOLD,
)
from app.db import get_connection

THRESHOLDS = {
    "sol_meme": SOLANA_ALERT_THRESHOLD,
    "base_meme": BASE_MEME_ALERT_THRESHOLD,
    "base_utility": BASE_UTILITY_ALERT_THRESHOLD,
}


def threshold_for(strategy_type: str) -> int:
    return THRESHOLDS[strategy_type]


def alert_level(score_total: float, strategy_type: str) -> str:
    threshold = threshold_for(strategy_type)
    if score_total >= threshold + 15:
        return "urgent_review"
    if score_total >= threshold + 5:
        return "high_priority"
    return "watch"


def format_strategy_label(strategy_type: str) -> str:
    return strategy_type.replace("_", " ").upper()


def build_alert_summary(alert_row: Dict[str, object]) -> str:
    parts = [
        f"⚡ {format_strategy_label(str(alert_row['strategy_type']))}",
        f"Token: {alert_row['symbol']} ({alert_row['chain']})",
        f"Score: {float(alert_row['score_total']):.1f}",
        f"Level: {alert_row['alert_level']}",
        f"Risk: {alert_row['risk_level']}",
    ]

    if alert_row.get("liquidity_usd") is not None:
        parts.append(f"Liquidity: ${float(alert_row['liquidity_usd']):,.0f}")
    if alert_row.get("volume_1h") is not None:
        parts.append(f"1h Volume: ${float(alert_row['volume_1h']):,.0f}")
    if alert_row.get("pair_age_minutes") is not None:
        parts.append(f"Pair Age: {int(alert_row['pair_age_minutes'])}m")
    if alert_row.get("top_10_pct") is not None:
        parts.append(f"Top10: {float(alert_row['top_10_pct']):.1f}%")
    if alert_row.get("tracked_wallet_buys_count") is not None:
        parts.append(f"Tracked Wallet Buys: {int(alert_row['tracked_wallet_buys_count'])}")

    return "\n".join(parts)


def latest_alert_score(token_address: str, chain: str, strategy_type: str) -> Optional[float]:
    conn = get_connection()
    row = conn.execute(
        """
        SELECT score_total
        FROM alerts
        WHERE token_address = ? AND chain = ? AND strategy_type = ?
        ORDER BY sent_at DESC, id DESC
        LIMIT 1
        """,
        (token_address, chain, strategy_type),
    ).fetchone()
    return None if row is None else float(row["score_total"])


def load_alert_candidates() -> List[Dict[str, object]]:
    conn = get_connection()
    rows = conn.execute(
        """
        WITH latest_scores AS (
            SELECT s.*
            FROM scores s
            JOIN (
                SELECT token_address, chain, strategy_type, MAX(computed_at) AS latest_computed_at
                FROM scores
                GROUP BY token_address, chain, strategy_type
            ) latest
              ON s.token_address = latest.token_address
             AND s.chain = latest.chain
             AND s.strategy_type = latest.strategy_type
             AND s.computed_at = latest.latest_computed_at
        ), latest_pairs AS (
            SELECT p.*
            FROM pairs p
            JOIN (
                SELECT chain, token_address, MAX(snapshot_at) AS latest_snapshot_at
                FROM pairs
                GROUP BY chain, token_address
            ) latest_pair
              ON p.chain = latest_pair.chain
             AND p.token_address = latest_pair.token_address
             AND p.snapshot_at = latest_pair.latest_snapshot_at
        ), latest_holders AS (
            SELECT h1.*
            FROM holder_snapshots h1
            JOIN (
                SELECT chain, token_address, MAX(snapshot_at) AS latest_snapshot_at
                FROM holder_snapshots
                GROUP BY chain, token_address
            ) h2
              ON h1.chain = h2.chain
             AND h1.token_address = h2.token_address
             AND h1.snapshot_at = h2.latest_snapshot_at
        ), latest_wallets AS (
            SELECT w1.*
            FROM wallet_signals w1
            JOIN (
                SELECT chain, token_address, MAX(snapshot_at) AS latest_snapshot_at
                FROM wallet_signals
                GROUP BY chain, token_address
            ) w2
              ON w1.chain = w2.chain
             AND w1.token_address = w2.token_address
             AND w1.snapshot_at = w2.latest_snapshot_at
        )
        SELECT
            ls.token_address,
            ls.chain,
            ls.strategy_type,
            ls.score_total,
            ls.risk_level,
            t.symbol,
            t.name,
            lp.liquidity_usd,
            lp.volume_1h,
            COALESCE(CAST((julianday('now') - julianday(lp.pair_created_at)) * 1440 AS INTEGER), 0) AS pair_age_minutes,
            COALESCE(lh.top_10_pct, 0) AS top_10_pct,
            COALESCE(lw.tracked_wallet_buys_count, 0) AS tracked_wallet_buys_count
        FROM latest_scores ls
        JOIN tokens t
          ON t.chain = ls.chain
         AND t.token_address = ls.token_address
        LEFT JOIN latest_pairs lp
          ON lp.chain = ls.chain
         AND lp.token_address = ls.token_address
        LEFT JOIN latest_holders lh
          ON lh.chain = ls.chain
         AND lh.token_address = ls.token_address
        LEFT JOIN latest_wallets lw
          ON lw.chain = ls.chain
         AND lw.token_address = ls.token_address
        ORDER BY ls.score_total DESC
        """
    ).fetchall()
    return [dict(row) for row in rows]


def should_alert(candidate: Dict[str, object], min_score_delta: float = 3.0) -> bool:
    strategy_type = str(candidate["strategy_type"])
    score_total = float(candidate["score_total"])
    if score_total < threshold_for(strategy_type):
        return False

    previous_score = latest_alert_score(
        str(candidate["token_address"]),
        str(candidate["chain"]),
        strategy_type,
    )
    if previous_score is None:
        return True
    return score_total >= previous_score + min_score_delta


def save_alert(alert_row: Dict[str, object], sent_to: str = "local") -> None:
    conn = get_connection()
    with conn:
        conn.execute(
            """
            INSERT INTO alerts (
                token_address, chain, strategy_type, alert_level, score_total, message_hash, sent_to
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                alert_row["token_address"],
                alert_row["chain"],
                alert_row["strategy_type"],
                alert_row["alert_level"],
                alert_row["score_total"],
                alert_row["message_hash"],
                sent_to,
            ),
        )


def count_alerts() -> int:
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) AS count FROM alerts").fetchone()
    return int(row["count"])
