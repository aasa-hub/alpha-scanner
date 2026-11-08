from typing import Dict, List

from app.schemas import TokenCandidate
from app.services.filters import (
    reject_base_meme,
    reject_base_utility,
    reject_sol_meme,
)
from app.services.scoring import load_latest_candidates, save_score
from app.strategies.base_meme import score_base_meme
from app.strategies.base_utility import score_base_utility
from app.strategies.sol_meme import score_sol_meme


STRATEGY_DISPATCH = {
    "sol_meme": score_sol_meme,
    "base_meme": score_base_meme,
    "base_utility": score_base_utility,
}

STRATEGY_FILTERS = {
    "sol_meme": reject_sol_meme,
    "base_meme": reject_base_meme,
    "base_utility": reject_base_utility,
}


def score_candidate(strategy_type: str, candidate: TokenCandidate):
    scorer = STRATEGY_DISPATCH[strategy_type]
    return scorer(candidate)


def _strategies_for_candidate(candidate: TokenCandidate) -> List[str]:
    if candidate.chain == "solana":
        return ["sol_meme"]
    if candidate.chain == "base":
        return ["base_meme", "base_utility"]
    return []


def run() -> Dict[str, int]:
    candidates = load_latest_candidates()
    saved_counts: Dict[str, int] = {key: 0 for key in STRATEGY_DISPATCH}

    for candidate in candidates:
        for strategy_type in _strategies_for_candidate(candidate):
            should_reject = STRATEGY_FILTERS[strategy_type](candidate)
            if should_reject:
                continue

            score_result = score_candidate(strategy_type, candidate)
            save_score(candidate.token_address, candidate.chain, score_result)
            saved_counts[strategy_type] += 1

    return saved_counts
