from app.schemas import TokenCandidate


def classify_risk(candidate: TokenCandidate) -> str:
    risk_points = 0

    if candidate.mint_authority:
        risk_points += 2
    if candidate.freeze_authority:
        risk_points += 2
    if candidate.proxy_contract:
        risk_points += 1
    if candidate.creator_pct > 15:
        risk_points += 2
    if candidate.top_10_pct > 50:
        risk_points += 2

    if risk_points >= 6:
        return "high_risk"
    if risk_points >= 3:
        return "warning"
    return "safe-ish"
