from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.jobs.discover_pairs import run as run_discovery
from app.jobs.score_tokens import run as run_scoring
from app.services.scoring import count_scores, summarize_scores
from app.services.token_registry import count_pair_snapshots, count_tokens


if __name__ == "__main__":
    discovery_data = run_discovery()
    scoring_counts = run_scoring()
    summary = {
        chain: {
            "pairs_stored": len(pairs),
        }
        for chain, pairs in discovery_data.items()
    }
    summary["db"] = {
        "tokens": count_tokens(),
        "pair_snapshots": count_pair_snapshots(),
        "scores": count_scores(),
    }
    summary["scoring"] = scoring_counts
    summary["score_summary"] = summarize_scores()
    print(summary)
