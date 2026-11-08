import json
import os
from typing import Dict, List, Set

from app.db import get_connection


TRACKED_WALLETS_ENV = "TRACKED_WALLETS"


def tracked_wallet_score(tracked_wallet_buys_count: int) -> float:
    if tracked_wallet_buys_count >= 3:
        return 10
    if tracked_wallet_buys_count == 2:
        return 7
    if tracked_wallet_buys_count == 1:
        return 4
    return 0


def tracked_wallets() -> Set[str]:
    raw = os.getenv(TRACKED_WALLETS_ENV, "")
    return {item.strip().lower() for item in raw.split(",") if item.strip()}


def compute_wallet_metrics(trades: List[dict]) -> Dict[str, float]:
    watched = tracked_wallets()
    buys = 0
    sells = 0
    netflow = 0.0
    insider_flag = False

    for trade in trades:
        wallet = str(trade.get("owner") or trade.get("wallet") or trade.get("trader") or "").lower()
        side = str(trade.get("side") or trade.get("type") or "").lower()
        amount_usd = float(trade.get("amount_usd") or trade.get("usd") or trade.get("value_usd") or 0)

        if wallet in watched:
            if side == "buy":
                buys += 1
                netflow += amount_usd
            elif side == "sell":
                sells += 1
                netflow -= amount_usd

        if trade.get("insider") is True:
            insider_flag = True

    return {
        "tracked_wallet_buys_count": buys,
        "tracked_wallet_sell_count": sells,
        "tracked_wallet_netflow_usd": round(netflow, 4),
        "insider_flag": int(insider_flag),
    }


def save_wallet_snapshot(chain: str, token_address: str, metrics: Dict[str, float]) -> None:
    conn = get_connection()
    with conn:
        conn.execute(
            """
            INSERT INTO wallet_signals (
                token_address, chain, tracked_wallet_buys_count, tracked_wallet_sell_count,
                tracked_wallet_netflow_usd, insider_flag
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                token_address,
                chain,
                metrics["tracked_wallet_buys_count"],
                metrics["tracked_wallet_sell_count"],
                metrics["tracked_wallet_netflow_usd"],
                metrics["insider_flag"],
            ),
        )


def count_wallet_snapshots() -> int:
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) AS count FROM wallet_signals").fetchone()
    return int(row["count"])


def load_latest_tokens(chain: str) -> List[str]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT token_address FROM tokens WHERE chain = ? ORDER BY last_seen_at DESC",
        (chain,),
    ).fetchall()
    return [row["token_address"] for row in rows]
