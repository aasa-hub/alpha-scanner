import json
from typing import Dict, List

from app.db import get_connection
from app.models import ScoreResult
from app.schemas import TokenCandidate


def load_latest_candidates() -> List[TokenCandidate]:
    conn = get_connection()
    rows = conn.execute(
        """
        WITH latest_pairs AS (
            SELECT p.*
            FROM pairs p
            JOIN (
                SELECT chain, pair_address, MAX(snapshot_at) AS latest_snapshot_at
                FROM pairs
                GROUP BY chain, pair_address
            ) latest
              ON p.chain = latest.chain
             AND p.pair_address = latest.pair_address
             AND p.snapshot_at = latest.latest_snapshot_at
        )
        SELECT
            lp.chain,
            lp.token_address,
            t.symbol,
            t.name,
            lp.pair_address,
            lp.dex,
            lp.liquidity_usd,
            lp.volume_1h,
            lp.fdv,
            lp.market_cap,
            lp.price_usd,
            lp.quote_symbol,
            lp.pair_created_at,
            COALESCE(CAST((julianday('now') - julianday(lp.pair_created_at)) * 1440 AS INTEGER), 0) AS pair_age_minutes,
            COALESCE(twitter_url, '') AS twitter_url,
            COALESCE(telegram_url, '') AS telegram_url,
            COALESCE(website_url, '') AS website_url,
            COALESCE(github_url, '') AS github_url
        FROM latest_pairs lp
        JOIN tokens t
          ON t.chain = lp.chain
         AND t.token_address = lp.token_address
        """
    ).fetchall()

    candidates: List[TokenCandidate] = []
    for row in rows:
        candidates.append(
            TokenCandidate(
                chain=row["chain"],
                token_address=row["token_address"],
                symbol=row["symbol"] or "",
                name=row["name"] or "",
                pair_address=row["pair_address"] or "",
                dex=row["dex"] or "",
                liquidity_usd=row["liquidity_usd"] or 0,
                volume_1h=row["volume_1h"] or 0,
                fdv=row["fdv"] or 0,
                market_cap=row["market_cap"] or 0,
                pair_age_minutes=row["pair_age_minutes"] or 0,
                twitter_mentions_1h=0,
                telegram_exists=bool(row["telegram_url"]),
                website_exists=bool(row["website_url"]),
                github_exists=bool(row["github_url"]),
                verified_contract=(row["chain"] == "solana"),
                mint_authority=False,
                freeze_authority=False,
                proxy_contract=False,
                holder_count=0,
                top_10_pct=0,
                creator_pct=0,
                tracked_wallet_buys_count=0,
                product_activity_score=6 if row["github_url"] else 0,
                catalyst_score=4 if row["website_url"] else 0,
            )
        )
    return candidates


def save_score(token_address: str, chain: str, score_result: ScoreResult) -> None:
    conn = get_connection()
    with conn:
        conn.execute(
            """
            INSERT INTO scores (
                token_address, chain, strategy_type, score_total, score_components, risk_level
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                token_address,
                chain,
                score_result.strategy_type,
                score_result.score_total,
                json.dumps(score_result.score_components, sort_keys=True),
                score_result.risk_level,
            ),
        )


def count_scores() -> int:
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) AS count FROM scores").fetchone()
    return int(row["count"])


def summarize_scores() -> List[Dict[str, object]]:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT strategy_type, COUNT(*) AS count, ROUND(MAX(score_total), 2) AS max_score
        FROM scores
        GROUP BY strategy_type
        ORDER BY strategy_type
        """
    ).fetchall()
    return [dict(row) for row in rows]
