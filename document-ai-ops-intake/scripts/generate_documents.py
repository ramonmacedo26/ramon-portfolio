from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from document_ai_ops.generate_data import generate_all


if __name__ == "__main__":
    generate_all()
    print("Synthetic documents created.")
