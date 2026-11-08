def tracked_wallet_score(tracked_wallet_buys_count: int) -> float:
    if tracked_wallet_buys_count >= 3:
        return 10
    if tracked_wallet_buys_count == 2:
        return 7
    if tracked_wallet_buys_count == 1:
        return 4
    return 0
