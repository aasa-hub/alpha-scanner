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


def build_alert_summary(alert_row: Dict[str, object]) -> str:
    return (
        f"[{alert_row['strategy_type']}] {alert_row['symbol']} on {alert_row['chain']} scored "
        f"{float(alert_row['score_total']):.1f} ({alert_row['alert_level']}, risk={alert_row['risk_level']})"
    )


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
        )
        SELECT
            ls.token_address,
            ls.chain,
            ls.strategy_type,
            ls.score_total,
            ls.risk_level,
            t.symbol,
            t.name
        FROM latest_scores ls
        JOIN tokens t
          ON t.chain = ls.chain
         AND t.token_address = ls.token_address
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
