from dataclasses import dataclass
from typing import Dict


@dataclass
class ScoreResult:
    strategy_type: str
    score_total: float
    score_components: Dict[str, float]
    risk_level: str
