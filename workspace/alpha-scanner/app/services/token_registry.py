from app.db import get_connection


def upsert_token(chain: str, token_address: str, symbol: str, name: str = "") -> None:
    conn = get_connection()
    with conn:
        conn.execute(
            """
            INSERT INTO tokens (chain, token_address, symbol, name, first_seen_at, last_seen_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(chain, token_address) DO UPDATE SET
                symbol=excluded.symbol,
                name=excluded.name,
                last_seen_at=CURRENT_TIMESTAMP
            """,
            (chain, token_address, symbol, name),
        )
