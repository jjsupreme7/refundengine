#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from refund_engine.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
