class SocialSignalsClient:
    def get_placeholder_metrics(self) -> dict:
        return {
            "twitter_mentions_1h": 0,
            "telegram_exists": False,
            "website_exists": False,
            "github_exists": False,
        }
