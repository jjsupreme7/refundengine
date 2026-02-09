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
    "Refund_Source",
    "Final_Decision",
    "Explanation",
    "Needs_Review",
    "Follow_Up_Questions",
    "AI_Reasoning",
    "Tax_Category",
    "Methodology",
    "Sales_Use_Tax",
)

REQUIRED_REASONING_HEADERS = (
    "INVOICE VERIFIED:",
    "SHIP-TO:",
    "MATCHED LINE ITEM:",
)

# --- Controlled vocabulary sets (from Phase 2 Master Refunds) ---

VALID_TAX_CATEGORIES = frozenset({
    "License",
    "Services",
    "Software maintenance",
    "Hardware maintenance",
    "Hardware",
    "Tangible goods",
    "Digital good",
    "DAS",
    "Maintenance",
})

VALID_PRODUCT_TYPES = frozenset({
    "License",
    "Services",
    "DAS",
    "Maintenance",
    "HW maintenance",
    "HW\\SW maintenance",
    "Hardware",
    "HW Maintenance",
    "Tangible goods",
    "Digital good",
    "Resale",
})

VALID_REFUND_BASES = frozenset({
    "MPU",
    "Non-taxable",
    "Partial OOS services",
    "Wrong rate",
    "Partial OOS shipment",
    "OOS services",
    "OOS shipment",
    "B&O tax",
    "Resale",
    "Discount",
})

VALID_METHODOLOGIES = frozenset({
    "User location",
    "Non-taxable",
    "Headcount",
    "Equipment Location",
    "Wrong rate",
    "Call center",
    "Call center Retail",
    "Retail stores",
    "Engineering",
    "Resale",
    "RF Engineering",
    "Ship-to location",
    "Delivery out-of-state",
    "Subscribers",
    # New from Phase 2 Recon Master
    "MPU",                     # 284 rows - multi-point use allocation
    "Care+Retail",             # 214 rows - care center + retail split
    "Fraud team",              # 39 rows - fraud team location allocation
    "Project location",        # 28 rows - allocation by project site
    "Call center + Marketing", # 26 rows - call center + marketing split
})

VALID_SALES_USE_TAX = frozenset({
    "Sales",
    "Use",
    "B&O",
})
