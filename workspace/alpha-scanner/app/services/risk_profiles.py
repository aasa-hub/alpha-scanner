import json
from typing import Dict, List

from app.db import get_connection


SUSPICIOUS_TERMS = [
    "blacklist",
    "setblacklist",
    "pause",
    "unpause",
    "mint",
    "settax",
    "setfee",
    "excludeFromFee",
]


def load_latest_base_tokens() -> List[str]:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT DISTINCT token_address
        FROM tokens
        WHERE chain = 'base'
        ORDER BY last_seen_at DESC
        """
    ).fetchall()
    return [row["token_address"] for row in rows]


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


def count_risk_profiles() -> int:
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) AS count FROM risk_profiles").fetchone()
    return int(row["count"])


def analyze_base_contract(source: Dict[str, object]) -> Dict[str, object]:
    source_code = str(source.get("SourceCode") or "")
    abi = str(source.get("ABI") or "")
    contract_name = str(source.get("ContractName") or "")
    proxy_flag = str(source.get("Proxy") or "0")

    verified_contract = bool(source_code.strip()) and source_code != "Contract source code not verified"
    proxy_contract = proxy_flag == "1"

    combined_text = f"{source_code}\n{abi}\n{contract_name}".lower()
    matched_terms = [term for term in SUSPICIOUS_TERMS if term.lower() in combined_text]

    mint_authority = "mint" in combined_text
    freeze_authority = "pause" in combined_text or "blacklist" in combined_text

    ownership_flags: List[str] = []
    blacklist_flags: List[str] = []
    risk_reasons: List[str] = []

    if not verified_contract:
        risk_reasons.append("unverified_contract")
    if proxy_contract:
        ownership_flags.append("proxy_contract")
        risk_reasons.append("proxy_contract")
    if mint_authority:
        ownership_flags.append("mint_capability")
        risk_reasons.append("mint_capability")
    if freeze_authority:
        ownership_flags.append("trading_controls")
        risk_reasons.append("trading_controls")

    for term in matched_terms:
        if "blacklist" in term:
            blacklist_flags.append(term)
        elif term not in ownership_flags:
            ownership_flags.append(term)

    risk_level = "safe-ish"
    if not verified_contract or proxy_contract or len(risk_reasons) >= 2:
        risk_level = "warning"
    if (not verified_contract and proxy_contract) or len(risk_reasons) >= 3:
        risk_level = "high_risk"

    return {
        "verified_contract": verified_contract,
        "mint_authority": mint_authority,
        "freeze_authority": freeze_authority,
        "proxy_contract": proxy_contract,
        "ownership_flags": ownership_flags,
        "blacklist_flags": blacklist_flags,
        "risk_level": risk_level,
        "risk_reasons": risk_reasons,
    }
