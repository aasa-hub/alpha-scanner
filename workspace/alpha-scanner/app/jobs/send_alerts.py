import hashlib
from typing import Dict, List

from app.services.alerting import (
    alert_level,
    build_alert_summary,
    load_alert_candidates,
    save_alert,
    should_alert,
)


def run() -> List[Dict[str, object]]:
    emitted_alerts: List[Dict[str, object]] = []

    for candidate in load_alert_candidates():
        if not should_alert(candidate):
            continue

        enriched = dict(candidate)
        enriched["alert_level"] = alert_level(
            float(candidate["score_total"]), str(candidate["strategy_type"])
        )
        enriched["summary"] = build_alert_summary(enriched)
        enriched["message_hash"] = hashlib.sha256(
            enriched["summary"].encode("utf-8")
        ).hexdigest()
        save_alert(enriched)
        emitted_alerts.append(enriched)

    return emitted_alerts
