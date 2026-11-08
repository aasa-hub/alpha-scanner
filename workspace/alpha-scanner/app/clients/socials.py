from typing import Dict
from urllib.parse import urlparse


class SocialSignalsClient:
    def derive_metrics(self, token_record: Dict[str, object]) -> dict:
        twitter_url = str(token_record.get("twitter_url") or "")
        telegram_url = str(token_record.get("telegram_url") or "")
        website_url = str(token_record.get("website_url") or "")
        github_url = str(token_record.get("github_url") or "")

        twitter_mentions_1h = 0
        if twitter_url:
            twitter_mentions_1h += 8
        if telegram_url:
            twitter_mentions_1h += 4
        if github_url:
            twitter_mentions_1h += 3
        if website_url:
            twitter_mentions_1h += 2

        domain_age_days = 0
        if website_url:
            parsed = urlparse(website_url)
            if parsed.netloc:
                domain_age_days = 30

        return {
            "twitter_mentions_1h": twitter_mentions_1h,
            "telegram_exists": bool(telegram_url),
            "website_exists": bool(website_url),
            "domain_age_days": domain_age_days,
            "github_exists": bool(github_url),
            "github_recent_activity": 1 if github_url else 0,
            "farcaster_mentions_24h": 2 if token_record.get("chain") == "base" and twitter_url else 0,
        }
