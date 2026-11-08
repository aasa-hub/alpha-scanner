from app.models import ScoreResult
from app.schemas import TokenCandidate
from app.services.risk_analysis import classify_risk
from app.services.wallet_tracking import tracked_wallet_score


def _liquidity_score(value: float) -> float:
    if value >= 100000:
        return 20
    if value >= 50000:
        return 14
    if value >= 25000:
        return 8
    return 0


def _volume_score(value: float) -> float:
    if value >= 200000:
        return 20
    if value >= 75000:
        return 14
    if value >= 25000:
        return 8
    return 0


def _freshness_score(minutes: int) -> float:
    if minutes <= 60:
        return 10
    if minutes <= 180:
        return 8
    if minutes <= 360:
        return 5
    return 0


def _holder_growth_score(holder_count: int) -> float:
    if holder_count >= 500:
        return 10
    if holder_count >= 250:
        return 7
    if holder_count >= 100:
        return 4
    return 1


def _holder_distribution_score(top_10_pct: float) -> float:
    if top_10_pct <= 20:
        return 15
    if top_10_pct <= 30:
        return 12
    if top_10_pct <= 40:
        return 8
    if top_10_pct <= 50:
        return 4
    return 0


def _social_score(candidate: TokenCandidate) -> float:
    score = 0
    if candidate.twitter_mentions_1h >= 50:
        score += 6
    elif candidate.twitter_mentions_1h >= 15:
        score += 4
    elif candidate.twitter_mentions_1h >= 5:
        score += 2

    if candidate.telegram_exists:
        score += 2
    if candidate.website_exists:
        score += 1
    if candidate.github_exists:
        score += 1
    return min(score, 10)


def _risk_adjustment(risk_level: str) -> float:
    if risk_level == "high_risk":
        return -5
    if risk_level == "warning":
        return -2
    return 2


def score_sol_meme(candidate: TokenCandidate) -> ScoreResult:
    risk_level = classify_risk(candidate)
    components = {
        "liquidity_quality": _liquidity_score(candidate.liquidity_usd),
        "volume_momentum": _volume_score(candidate.volume_1h),
        "pair_freshness": _freshness_score(candidate.pair_age_minutes),
        "holder_growth": _holder_growth_score(candidate.holder_count),
        "holder_distribution": _holder_distribution_score(candidate.top_10_pct),
        "social_velocity": _social_score(candidate),
        "wallet_signal": tracked_wallet_score(candidate.tracked_wallet_buys_count),
        "risk_adjustment": _risk_adjustment(risk_level),
    }
    total = sum(components.values())
    return ScoreResult(
        strategy_type="sol_meme",
        score_total=total,
        score_components=components,
        risk_level=risk_level,
    )
