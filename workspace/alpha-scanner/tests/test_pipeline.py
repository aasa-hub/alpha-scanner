import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.services.pipeline import run_pipeline


def test_run_pipeline_callable(monkeypatch):
    monkeypatch.setattr('app.services.pipeline.run_discovery', lambda: {'solana': [], 'base': []})
    monkeypatch.setattr('app.services.pipeline.run_holder_enrichment', lambda: {'solana': 0, 'base': 0})
    monkeypatch.setattr('app.services.pipeline.run_social_enrichment', lambda: {'solana': 0, 'base': 0})
    monkeypatch.setattr('app.services.pipeline.run_wallet_enrichment', lambda: {'solana': 0, 'base': 0})
    monkeypatch.setattr('app.services.pipeline.run_risk_enrichment', lambda: {'solana': 0, 'base': 0})
    monkeypatch.setattr('app.services.pipeline.run_scoring', lambda: {'sol_meme': 0, 'base_meme': 0, 'base_utility': 0})
    monkeypatch.setattr('app.services.pipeline.run_alerts', lambda: [])
    monkeypatch.setattr('app.services.pipeline.count_tokens', lambda: 0)
    monkeypatch.setattr('app.services.pipeline.count_pair_snapshots', lambda: 0)
    monkeypatch.setattr('app.services.pipeline.count_holder_snapshots', lambda: 0)
    monkeypatch.setattr('app.services.pipeline.count_social_snapshots', lambda: 0)
    monkeypatch.setattr('app.services.pipeline.count_wallet_snapshots', lambda: 0)
    monkeypatch.setattr('app.services.pipeline.count_risk_profiles', lambda: 0)
    monkeypatch.setattr('app.services.pipeline.count_scores', lambda: 0)
    monkeypatch.setattr('app.services.pipeline.count_alerts', lambda: 0)
    monkeypatch.setattr('app.services.pipeline.summarize_scores', lambda: [])

    summary = run_pipeline()

    assert summary['db']['tokens'] == 0
    assert summary['social_enrichment']['base'] == 0
