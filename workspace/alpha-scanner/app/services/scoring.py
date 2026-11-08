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
            COALESCE(github_url, '') AS github_url,
            COALESCE(hs.holder_count, 0) AS holder_count,
            COALESCE(hs.top_10_pct, 0) AS top_10_pct,
            COALESCE(hs.creator_pct, 0) AS creator_pct,
            COALESCE(rp.verified_contract, CASE WHEN lp.chain = 'solana' THEN 1 ELSE 0 END) AS verified_contract,
            COALESCE(rp.mint_authority, 0) AS mint_authority,
            COALESCE(rp.freeze_authority, 0) AS freeze_authority,
            COALESCE(rp.proxy_contract, 0) AS proxy_contract,
            COALESCE(ws.tracked_wallet_buys_count, 0) AS tracked_wallet_buys_count
        FROM latest_pairs lp
        JOIN tokens t
          ON t.chain = lp.chain
         AND t.token_address = lp.token_address
        LEFT JOIN (
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
        ) hs
          ON hs.chain = lp.chain
         AND hs.token_address = lp.token_address
        LEFT JOIN (
            SELECT r1.*
            FROM risk_profiles r1
            JOIN (
                SELECT chain, token_address, MAX(snapshot_at) AS latest_snapshot_at
                FROM risk_profiles
                GROUP BY chain, token_address
            ) r2
              ON r1.chain = r2.chain
             AND r1.token_address = r2.token_address
             AND r1.snapshot_at = r2.latest_snapshot_at
        ) rp
          ON rp.chain = lp.chain
         AND rp.token_address = lp.token_address
        LEFT JOIN (
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
        ) ws
          ON ws.chain = lp.chain
         AND ws.token_address = lp.token_address
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
                verified_contract=bool(row["verified_contract"]),
                mint_authority=bool(row["mint_authority"]),
                freeze_authority=bool(row["freeze_authority"]),
                proxy_contract=bool(row["proxy_contract"]),
                holder_count=row["holder_count"] or 0,
                top_10_pct=row["top_10_pct"] or 0,
                creator_pct=row["creator_pct"] or 0,
                tracked_wallet_buys_count=row["tracked_wallet_buys_count"] or 0,
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
