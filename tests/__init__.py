import sys
from pathlib import Path

# Lambda runs with src/ as its root, so the modules there import each other
# by bare name. Make the same true for the tests.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
