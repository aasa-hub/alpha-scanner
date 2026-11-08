import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db import get_connection
from app.jobs.send_alerts import run


def seed_scores() -> None:
    conn = get_connection()
    with conn:
        conn.execute(
            """
            INSERT INTO tokens (chain, token_address, symbol, name, first_seen_at, last_seen_at, website_url)
            VALUES ('solana', 'token_alert', 'ALRT', 'Alert Token', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'https://alert.example')
            """
        )
        conn.execute(
            """
            INSERT INTO scores (token_address, chain, strategy_type, score_total, score_components, risk_level, computed_at)
            VALUES ('token_alert', 'solana', 'sol_meme', 82, '{}', 'safe-ish', CURRENT_TIMESTAMP)
            """
        )


def test_send_alerts_persists_and_dedupes(tmp_path, monkeypatch):
    db_path = tmp_path / 'scanner.db'
    monkeypatch.setenv('DB_PATH', str(db_path))

    from scripts.init_db import main as init_db_main

    init_db_main()
    seed_scores()

    first_run = run()
    second_run = run()

    assert len(first_run) == 1
    assert len(second_run) == 0

    conn = get_connection()
    total_alerts = conn.execute('SELECT COUNT(*) AS count FROM alerts').fetchone()['count']
    assert total_alerts == 1
