from pathlib import Path
import sys
import time

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.config import SCHEDULER_INTERVAL_SECONDS
from app.services.pipeline import run_pipeline


if __name__ == "__main__":
    print(f"Starting scheduler loop with interval={SCHEDULER_INTERVAL_SECONDS}s")
    while True:
        summary = run_pipeline()
        print(summary)
        time.sleep(SCHEDULER_INTERVAL_SECONDS)
