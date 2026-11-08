import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.clients.socials import SocialSignalsClient


def test_social_metrics_derive_from_links():
    client = SocialSignalsClient()
    metrics = client.derive_metrics(
        {
            'chain': 'base',
            'twitter_url': 'https://x.com/example',
            'telegram_url': 'https://t.me/example',
            'website_url': 'https://example.com',
            'github_url': 'https://github.com/example/repo',
        }
    )

    assert metrics['twitter_mentions_1h'] > 0
    assert metrics['telegram_exists'] is True
    assert metrics['website_exists'] is True
    assert metrics['github_exists'] is True
    assert metrics['farcaster_mentions_24h'] == 2
