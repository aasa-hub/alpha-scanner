from typing import Optional

from pydantic import BaseModel


class TokenCandidate(BaseModel):
    chain: str
    token_address: str
    symbol: str
    name: Optional[str] = None
    pair_address: Optional[str] = None
    dex: Optional[str] = None
    liquidity_usd: float = 0
    volume_1h: float = 0
    fdv: float = 0
    pair_age_minutes: int = 0
    holder_count: int = 0
    top_10_pct: float = 0
    creator_pct: float = 0
    tracked_wallet_buys_count: int = 0
    twitter_mentions_1h: int = 0
    telegram_exists: bool = False
    website_exists: bool = False
    github_exists: bool = False
    verified_contract: bool = False
    mint_authority: bool = False
    freeze_authority: bool = False
    proxy_contract: bool = False
    product_activity_score: float = 0
    catalyst_score: float = 0
    market_cap: float = 0
