from app.schemas import TokenCandidate


def reject_sol_meme(candidate: TokenCandidate) -> bool:
    return (
        candidate.liquidity_usd < 25000
        or candidate.pair_age_minutes > 360
        or candidate.top_10_pct > 50
        or candidate.creator_pct > 15
    )


def reject_base_meme(candidate: TokenCandidate) -> bool:
    return (
        candidate.liquidity_usd < 35000
        or candidate.pair_age_minutes > 1440
        or candidate.top_10_pct > 50
        or not candidate.verified_contract
    )


def reject_base_utility(candidate: TokenCandidate) -> bool:
    return (
        not candidate.verified_contract
        or not candidate.website_exists
        or candidate.product_activity_score < 3
    )
