from app.models import ScoreResult
from app.schemas import TokenCandidate
from app.services.risk_analysis import classify_risk
from app.services.wallet_tracking import tracked_wallet_score


def _liquidity_score(value: float) -> float:
    if value >= 150000:
        return 20
    if value >= 75000:
        return 14
    if value >= 35000:
        return 8
    return 0


def _volume_score(value: float) -> float:
    if value >= 200000:
        return 15
    if value >= 80000:
        return 11
    if value >= 30000:
        return 6
    return 0


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


def _contract_safety_score(candidate: TokenCandidate) -> float:
    score = 0
    if candidate.verified_contract:
        score += 10
    if not candidate.mint_authority:
        score += 2
    if not candidate.proxy_contract:
        score += 2
    if not candidate.freeze_authority:
        score += 1
    return min(score, 15)


def _social_score(candidate: TokenCandidate) -> float:
    score = 0
    if candidate.twitter_mentions_1h >= 50:
        score += 8
    elif candidate.twitter_mentions_1h >= 15:
        score += 5
    elif candidate.twitter_mentions_1h >= 5:
        score += 2

    if candidate.telegram_exists:
        score += 3
    if candidate.website_exists:
        score += 2
    if candidate.github_exists:
        score += 2
    return min(score, 15)


def _freshness_score(minutes: int) -> float:
    if minutes <= 120:
        return 10
    if minutes <= 480:
        return 7
    if minutes <= 1440:
        return 4
    return 0


def score_base_meme(candidate: TokenCandidate) -> ScoreResult:
    risk_level = classify_risk(candidate)
    components = {
        "liquidity_quality": _liquidity_score(candidate.liquidity_usd),
        "volume_momentum": _volume_score(candidate.volume_1h),
        "holder_distribution": _holder_distribution_score(candidate.top_10_pct),
        "contract_safety": _contract_safety_score(candidate),
        "social_velocity": _social_score(candidate),
        "wallet_signal": tracked_wallet_score(candidate.tracked_wallet_buys_count),
        "pair_freshness": _freshness_score(candidate.pair_age_minutes),
    }
    total = sum(components.values())
    if risk_level == "high_risk":
        total -= 5
    elif risk_level == "warning":
        total -= 2
    return ScoreResult(
        strategy_type="base_meme",
        score_total=total,
        score_components=components,
        risk_level=risk_level,
    )
