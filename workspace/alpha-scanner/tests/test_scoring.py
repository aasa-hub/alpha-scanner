from app.schemas import TokenCandidate
from app.strategies.base_meme import score_base_meme
from app.strategies.base_utility import score_base_utility
from app.strategies.sol_meme import score_sol_meme


def test_sol_meme_high_score_candidate():
    candidate = TokenCandidate(
        chain="solana",
        token_address="token1",
        symbol="SAM",
        liquidity_usd=120000,
        volume_1h=250000,
        pair_age_minutes=45,
        holder_count=600,
        top_10_pct=18,
        creator_pct=3,
        tracked_wallet_buys_count=3,
        twitter_mentions_1h=60,
        telegram_exists=True,
        website_exists=True,
        github_exists=False,
    )
    result = score_sol_meme(candidate)
    assert result.score_total >= 75


def test_base_meme_requires_good_contract_profile():
    candidate = TokenCandidate(
        chain="base",
        token_address="token2",
        symbol="BASEY",
        liquidity_usd=90000,
        volume_1h=120000,
        pair_age_minutes=180,
        top_10_pct=25,
        tracked_wallet_buys_count=2,
        twitter_mentions_1h=20,
        telegram_exists=True,
        website_exists=True,
        github_exists=True,
        verified_contract=True,
    )
    result = score_base_meme(candidate)
    assert result.score_total >= 70


def test_base_utility_rewards_product_and_catalyst():
    candidate = TokenCandidate(
        chain="base",
        token_address="token3",
        symbol="UTIL",
        liquidity_usd=210000,
        market_cap=8000000,
        top_10_pct=22,
        tracked_wallet_buys_count=2,
        twitter_mentions_1h=30,
        telegram_exists=True,
        website_exists=True,
        github_exists=True,
        verified_contract=True,
        product_activity_score=18,
        catalyst_score=13,
    )
    result = score_base_utility(candidate)
    assert result.score_total >= 80
