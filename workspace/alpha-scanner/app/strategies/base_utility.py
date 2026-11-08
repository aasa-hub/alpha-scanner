from app.models import ScoreResult
from app.schemas import TokenCandidate
from app.services.risk_analysis import classify_risk


def _liquidity_score(value: float) -> float:
    if value >= 200000:
        return 10
    if value >= 100000:
        return 7
    if value >= 50000:
        return 4
    return 1


def _market_cap_opportunity(value: float) -> float:
    if 0 < value <= 10000000:
        return 15
    if value <= 25000000:
        return 10
    if value <= 50000000:
        return 6
    return 2


def _contract_safety_score(candidate: TokenCandidate) -> float:
    score = 0
    if candidate.verified_contract:
        score += 9
    if not candidate.mint_authority:
        score += 3
    if not candidate.proxy_contract:
        score += 2
    if not candidate.freeze_authority:
        score += 1
    return min(score, 15)


def _holder_quality_score(top_10_pct: float) -> float:
    if top_10_pct <= 20:
        return 10
    if top_10_pct <= 30:
        return 8
    if top_10_pct <= 40:
        return 6
    if top_10_pct <= 50:
        return 3
    return 0


def _social_quality_score(candidate: TokenCandidate) -> float:
    score = 0
    if candidate.twitter_mentions_1h >= 25:
        score += 4
    elif candidate.twitter_mentions_1h >= 5:
        score += 2
    if candidate.telegram_exists:
        score += 2
    if candidate.website_exists:
        score += 2
    if candidate.github_exists:
        score += 2
    return min(score, 10)


def _product_activity_score(value: float) -> float:
    return max(0, min(value, 20))


def _catalyst_score(value: float) -> float:
    return max(0, min(value, 15))


def _wallet_signal_score(tracked_wallet_buys_count: int) -> float:
    if tracked_wallet_buys_count >= 3:
        return 5
    if tracked_wallet_buys_count == 2:
        return 4
    if tracked_wallet_buys_count == 1:
        return 2
    return 0


def score_base_utility(candidate: TokenCandidate) -> ScoreResult:
    risk_level = classify_risk(candidate)
    components = {
        "liquidity_quality": _liquidity_score(candidate.liquidity_usd),
        "market_cap_opportunity": _market_cap_opportunity(candidate.market_cap),
        "contract_safety": _contract_safety_score(candidate),
        "holder_quality": _holder_quality_score(candidate.top_10_pct),
        "social_community_quality": _social_quality_score(candidate),
        "product_dev_activity": _product_activity_score(candidate.product_activity_score),
        "catalyst_strength": _catalyst_score(candidate.catalyst_score),
        "wallet_signal": _wallet_signal_score(candidate.tracked_wallet_buys_count),
    }
    total = sum(components.values())
    if risk_level == "high_risk":
        total -= 5
    elif risk_level == "warning":
        total -= 2
    return ScoreResult(
        strategy_type="base_utility",
        score_total=total,
        score_components=components,
        risk_level=risk_level,
    )
