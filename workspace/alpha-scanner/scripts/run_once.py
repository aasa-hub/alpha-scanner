from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.jobs.discover_pairs import run


if __name__ == "__main__":
    data = run()
    print({key: list(value.keys()) if isinstance(value, dict) else type(value).__name__ for key, value in data.items()})
