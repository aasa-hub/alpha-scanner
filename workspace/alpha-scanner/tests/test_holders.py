import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.services.holders import compute_holder_metrics


def test_compute_holder_metrics_sums_percentages():
    holders = [
        {"percentage": "12.5"},
        {"percentage": "10"},
        {"percentage": "7.5"},
    ]

    metrics = compute_holder_metrics(holders)

    assert metrics["holder_count"] == 3
    assert metrics["top_10_pct"] == 30.0
    assert metrics["top_20_pct"] == 30.0
    assert metrics["creator_pct"] == 12.5
