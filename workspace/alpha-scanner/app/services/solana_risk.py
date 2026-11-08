import json
from typing import Dict, List

from app.db import get_connection


def load_latest_solana_tokens() -> List[str]:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT DISTINCT token_address
        FROM tokens
        WHERE chain = 'solana'
        ORDER BY last_seen_at DESC
        """
    ).fetchall()
    return [row["token_address"] for row in rows]


def analyze_token_security(security_data: Dict[str, object]) -> Dict[str, object]:
    mint_authority = bool(security_data.get("mintAuthority") or security_data.get("mint_authority"))
    freeze_authority = bool(security_data.get("freezeAuthority") or security_data.get("freeze_authority"))
    creator_pct = float(security_data.get("creatorPercentage") or security_data.get("creator_percentage") or 0)

    ownership_flags = []
    risk_reasons = []
    blacklist_flags = []

    if mint_authority:
        ownership_flags.append("mint_authority")
        risk_reasons.append("mint_authority")
    if freeze_authority:
        ownership_flags.append("freeze_authority")
        risk_reasons.append("freeze_authority")
    if creator_pct > 15:
        risk_reasons.append("creator_concentration")

    risk_level = "safe-ish"
    if len(risk_reasons) >= 1:
        risk_level = "warning"
    if len(risk_reasons) >= 2 or creator_pct > 25:
        risk_level = "high_risk"

    return {
        "verified_contract": True,
        "mint_authority": mint_authority,
        "freeze_authority": freeze_authority,
        "proxy_contract": False,
        "ownership_flags": ownership_flags,
        "blacklist_flags": blacklist_flags,
        "risk_level": risk_level,
        "risk_reasons": risk_reasons,
    }


def save_risk_profile(chain: str, token_address: str, profile: Dict[str, object]) -> None:
    conn = get_connection()
    with conn:
        conn.execute(
            """
            INSERT INTO risk_profiles (
                token_address, chain, verified_contract, mint_authority, freeze_authority,
                proxy_contract, ownership_flags, blacklist_flags, risk_level, risk_reasons
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                token_address,
                chain,
                int(bool(profile.get("verified_contract"))),
                int(bool(profile.get("mint_authority"))),
                int(bool(profile.get("freeze_authority"))),
                int(bool(profile.get("proxy_contract"))),
                json.dumps(profile.get("ownership_flags", [])),
                json.dumps(profile.get("blacklist_flags", [])),
                str(profile.get("risk_level", "warning")),
                json.dumps(profile.get("risk_reasons", [])),
            ),
        )
