import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.services.solana_risk import analyze_token_security


def test_analyze_token_security_flags_authorities():
    security = {
        'mintAuthority': 'mint_auth',
        'freezeAuthority': 'freeze_auth',
        'creatorPercentage': 12,
    }

    profile = analyze_token_security(security)

    assert profile['verified_contract'] is True
    assert profile['mint_authority'] is True
    assert profile['freeze_authority'] is True
    assert profile['risk_level'] == 'high_risk'
