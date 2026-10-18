import sys
from pathlib import Path

# Ensure root workspace directory and engine/ are in sys.path for test execution
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(ROOT_DIR / "engine") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "engine"))
