from app.models import ScoreResult


def build_alert_summary(symbol: str, score_result: ScoreResult) -> str:
    return (
        f"[{score_result.strategy_type}] {symbol} scored {score_result.score_total:.1f} "
        f"with risk {score_result.risk_level}"
    )
