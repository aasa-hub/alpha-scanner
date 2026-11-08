from app.schemas import TokenCandidate
from app.strategies.base_meme import score_base_meme
from app.strategies.base_utility import score_base_utility
from app.strategies.sol_meme import score_sol_meme


STRATEGY_DISPATCH = {
    "sol_meme": score_sol_meme,
    "base_meme": score_base_meme,
    "base_utility": score_base_utility,
}


def run(strategy_type: str, candidate: TokenCandidate):
    scorer = STRATEGY_DISPATCH[strategy_type]
    return scorer(candidate)
