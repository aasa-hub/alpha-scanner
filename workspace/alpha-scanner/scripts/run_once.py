from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.services.pipeline import run_pipeline


if __name__ == "__main__":
    print(run_pipeline())
