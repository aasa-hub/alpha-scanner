from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.jobs.discover_pairs import run
from app.services.token_registry import count_pair_snapshots, count_tokens


if __name__ == "__main__":
    data = run()
    summary = {
        chain: {
            "pairs_stored": len(pairs),
        }
        for chain, pairs in data.items()
    }
    summary["db"] = {
        "tokens": count_tokens(),
        "pair_snapshots": count_pair_snapshots(),
    }
    print(summary)
