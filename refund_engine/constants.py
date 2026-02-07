from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATASETS_PATH = PROJECT_ROOT / "config" / "datasets.yaml"
RUNS_DIR = PROJECT_ROOT / "runs"

AI_OUTPUT_COLUMNS = (
    "Product_Desc",
    "Product_Type",
    "Service_Classification",
    "Refund_Basis",
    "Citation",
    "Citation_Source",
    "Confidence",
    "Estimated_Refund",
    "Final_Decision",
    "Explanation",
    "Needs_Review",
    "Follow_Up_Questions",
    "AI_Reasoning",
)

REQUIRED_REASONING_HEADERS = (
    "INVOICE VERIFIED:",
    "SHIP-TO:",
    "MATCHED LINE ITEM:",
)
