from pathlib import Path
import sqlite3

from app.config import DB_PATH


def get_connection() -> sqlite3.Connection:
    db_path = Path(DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
