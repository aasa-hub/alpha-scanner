from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.jobs.discover_pairs import run as run_discovery
from app.jobs.enrich_holders import run as run_holder_enrichment
from app.jobs.score_tokens import run as run_scoring
from app.jobs.send_alerts import run as run_alerts
from app.services.alerting import count_alerts
from app.services.holders import count_holder_snapshots
from app.services.scoring import count_scores, summarize_scores
from app.services.token_registry import count_pair_snapshots, count_tokens


if __name__ == "__main__":
    discovery_data = run_discovery()
    holder_counts = run_holder_enrichment()
    scoring_counts = run_scoring()
    alerts = run_alerts()

    summary = {
        chain: {
            "pairs_stored": len(pairs),
        }
        for chain, pairs in discovery_data.items()
    }
    summary["db"] = {
        "tokens": count_tokens(),
        "pair_snapshots": count_pair_snapshots(),
        "holder_snapshots": count_holder_snapshots(),
        "scores": count_scores(),
        "alerts": count_alerts(),
    }
    summary["holder_enrichment"] = holder_counts
    summary["scoring"] = scoring_counts
    summary["alerts"] = [alert["summary"] for alert in alerts]
    summary["score_summary"] = summarize_scores()
    print(summary)
