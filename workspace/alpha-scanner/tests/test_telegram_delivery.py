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
            VALUES ('solana', 'token_tg', 'TGRAM', 'Telegram Token', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'https://tg.example')
            """
        )
        conn.execute(
            """
            INSERT INTO scores (token_address, chain, strategy_type, score_total, score_components, risk_level, computed_at)
            VALUES ('token_tg', 'solana', 'sol_meme', 85, '{}', 'safe-ish', CURRENT_TIMESTAMP)
            """
        )


def test_send_alerts_uses_telegram_target_when_configured(tmp_path, monkeypatch):
    db_path = tmp_path / 'scanner.db'
    monkeypatch.setenv('DB_PATH', str(db_path))

    from scripts.init_db import main as init_db_main

    init_db_main()
    seed_scores()

    monkeypatch.setattr('app.jobs.send_alerts.is_configured', lambda: True)
    monkeypatch.setattr('app.jobs.send_alerts.configured_target', lambda: 'telegram:5815439260')
    monkeypatch.setattr('app.jobs.send_alerts.send_message', lambda text: {'ok': True, 'result': {'text': text}})

    alerts = run()

    assert len(alerts) == 1
    conn = get_connection()
    row = conn.execute('SELECT sent_to FROM alerts LIMIT 1').fetchone()
    assert row['sent_to'] == 'telegram:5815439260'
