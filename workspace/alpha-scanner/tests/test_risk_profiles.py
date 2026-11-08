import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.services.risk_profiles import analyze_base_contract


def test_analyze_base_contract_flags_proxy_and_mint():
    source = {
        'SourceCode': 'contract Token { function mint(address to,uint amount) public {} function pause() public {} }',
        'ABI': '[{"name":"mint"},{"name":"pause"}]',
        'ContractName': 'Token',
        'Proxy': '1',
    }

    profile = analyze_base_contract(source)

    assert profile['verified_contract'] is True
    assert profile['mint_authority'] is True
    assert profile['freeze_authority'] is True
    assert profile['proxy_contract'] is True
    assert profile['risk_level'] == 'high_risk'
