from __future__ import annotations

from refund_engine.validation_rules import (
    normalize_final_decision,
    normalize_methodology,
    validate_output_row,
)


def test_normalize_final_decision_handles_underscores():
    assert normalize_final_decision("no_refund") == "NO REFUND"
    assert normalize_final_decision("review") == "REVIEW"


def test_validate_output_row_flags_missing_headers():
    row = {
        "Final_Decision": "REVIEW",
        "Citation": "",
        "Confidence": 0.4,
        "AI_Reasoning": "missing expected headers",
        "Product_Desc": "something",
    }
    errors = validate_output_row(row)
    assert any("INVOICE VERIFIED:" in err for err in errors)
    assert any("SHIP-TO:" in err for err in errors)
    assert any("MATCHED LINE ITEM:" in err for err in errors)


def test_validate_output_row_requires_refund_citation():
    row = {
        "Final_Decision": "REFUND",
        "Citation": "",
        "Confidence": 0.8,
        "Product_Desc": "Cloud software",
        "AI_Reasoning": (
            "INVOICE VERIFIED: x\n"
            "SHIP-TO: y\n"
            "MATCHED LINE ITEM: z"
        ),
    }
    errors = validate_output_row(row)
    assert any("Citation is required for REFUND" in err for err in errors)


def test_validate_output_row_flags_invalid_product_type():
    row = {
        "Final_Decision": "REFUND",
        "Citation": "RCW 82.08.02565",
        "Confidence": 0.8,
        "Product_Desc": "Network switches",
        "Product_Type": "INVALID_TYPE",
        "AI_Reasoning": (
            "INVOICE VERIFIED: x\n"
            "SHIP-TO: y\n"
            "MATCHED LINE ITEM: z"
        ),
    }
    errors = validate_output_row(row)
    assert any("Product_Type" in err and "controlled vocabulary" in err for err in errors)


def test_validate_output_row_flags_invalid_sales_use_tax():
    row = {
        "Final_Decision": "REVIEW",
        "Product_Desc": "Cloud service",
        "Sales_Use_Tax": "Income",
        "AI_Reasoning": (
            "INVOICE VERIFIED: x\n"
            "SHIP-TO: y\n"
            "MATCHED LINE ITEM: z"
        ),
    }
    errors = validate_output_row(row)
    assert any("Sales_Use_Tax" in err for err in errors)


_VALID_REASONING = (
    "INVOICE VERIFIED: Invoice #12345 dated 2024-03-15\n"
    "SHIP-TO: 15015 NE 90th St, Redmond, WA 98052\n"
    "MATCHED LINE ITEM: Cloud hosting service @ $10,000.00"
)


def test_validate_output_row_accepts_valid_row():
    row = {
        "Final_Decision": "REFUND",
        "Citation": "RCW 82.08.02565",
        "Confidence": 0.8,
        "Product_Desc": "Network switches",
        "Product_Type": "Hardware",
        "Refund_Basis": "MPU",
        "Methodology": "User location",
        "Tax_Category": "Hardware",
        "Sales_Use_Tax": "Sales",
        "Explanation": "Multi-point use allocation for nationwide deployment.",
        "AI_Reasoning": _VALID_REASONING,
    }
    errors = validate_output_row(row)
    assert errors == []


def test_validate_refund_requires_methodology():
    row = {
        "Final_Decision": "REFUND",
        "Citation": "RCW 82.08.02565",
        "Confidence": 0.8,
        "Product_Desc": "Cloud service",
        "Refund_Basis": "MPU",
        "Explanation": "MPU allocation.",
        "AI_Reasoning": _VALID_REASONING,
    }
    errors = validate_output_row(row)
    assert any("Methodology is required" in err for err in errors)


def test_validate_refund_requires_refund_basis():
    row = {
        "Final_Decision": "REFUND",
        "Citation": "RCW 82.08.02565",
        "Confidence": 0.8,
        "Product_Desc": "Cloud service",
        "Methodology": "User location",
        "Explanation": "MPU allocation.",
        "AI_Reasoning": _VALID_REASONING,
    }
    errors = validate_output_row(row)
    assert any("Refund_Basis is required" in err for err in errors)


def test_validate_matched_line_item_needs_amount():
    row = {
        "Final_Decision": "REFUND",
        "Citation": "RCW 82.08.02565",
        "Confidence": 0.8,
        "Product_Desc": "Cloud service",
        "Refund_Basis": "MPU",
        "Methodology": "User location",
        "Explanation": "MPU allocation.",
        "AI_Reasoning": (
            "INVOICE VERIFIED: Invoice #12345 dated 2024-03-15\n"
            "SHIP-TO: 15015 NE 90th St, Redmond, WA 98052\n"
            "MATCHED LINE ITEM: UNKNOWN"
        ),
    }
    errors = validate_output_row(row)
    assert any("MATCHED LINE ITEM must identify" in err for err in errors)


def test_validate_ship_to_needs_detail():
    row = {
        "Final_Decision": "NO REFUND",
        "Confidence": 0.8,
        "Product_Desc": "Cloud service",
        "Explanation": "Taxable service.",
        "AI_Reasoning": (
            "INVOICE VERIFIED: Invoice #12345 dated 2024-03-15\n"
            "SHIP-TO: WA\n"
            "MATCHED LINE ITEM: Cloud hosting @ $5,000.00"
        ),
    }
    errors = validate_output_row(row)
    assert any("SHIP-TO must be a full address" in err for err in errors)


def test_validate_review_needs_follow_up():
    row = {
        "Final_Decision": "REVIEW",
        "Confidence": 0.4,
        "Product_Desc": "Cloud service",
        "Follow_Up_Questions": "",
        "AI_Reasoning": _VALID_REASONING,
    }
    errors = validate_output_row(row)
    assert any("follow-up questions" in err for err in errors)


def test_validate_high_confidence_review_flagged():
    row = {
        "Final_Decision": "REVIEW",
        "Confidence": 0.9,
        "Product_Desc": "Cloud service",
        "Follow_Up_Questions": "Need to verify the invoice line item details with vendor.",
        "AI_Reasoning": _VALID_REASONING,
    }
    errors = validate_output_row(row)
    assert any("too high for REVIEW" in err for err in errors)


def test_validate_methodology_vocabulary():
    row = {
        "Final_Decision": "REFUND",
        "Citation": "RCW 82.08.02565",
        "Confidence": 0.8,
        "Product_Desc": "Cloud service",
        "Refund_Basis": "MPU",
        "Methodology": "INVALID_METHOD",
        "Explanation": "MPU allocation.",
        "AI_Reasoning": _VALID_REASONING,
    }
    errors = validate_output_row(row)
    assert any("Methodology" in err and "controlled vocabulary" in err for err in errors)


def test_validate_explanation_required():
    row = {
        "Final_Decision": "REFUND",
        "Citation": "RCW 82.08.02565",
        "Confidence": 0.8,
        "Product_Desc": "Cloud service",
        "Refund_Basis": "MPU",
        "Methodology": "User location",
        "Explanation": "",
        "AI_Reasoning": _VALID_REASONING,
    }
    errors = validate_output_row(row)
    assert any("Explanation is required" in err for err in errors)


def test_normalize_methodology_case_insensitive():
    assert normalize_methodology("equipment location") == "Equipment Location"
    assert normalize_methodology("Equipment Location") == "Equipment Location"


def test_normalize_methodology_punctuation_variants():
    assert normalize_methodology("Call center, Retail") == "Call center Retail"
    assert normalize_methodology("call center,retail") == "Call center Retail"


def test_normalize_methodology_new_entries():
    assert normalize_methodology("care+retail") == "Care+Retail"
    assert normalize_methodology("Care + Retail") == "Care+Retail"


def test_normalize_methodology_passthrough():
    assert normalize_methodology("MPU") == "MPU"
    assert normalize_methodology("Fraud team") == "Fraud team"
    assert normalize_methodology("") == ""
    assert normalize_methodology(None) == ""


def test_validate_accepts_mpu_methodology():
    row = {
        "Final_Decision": "REFUND",
        "Citation": "RCW 82.08.0208(4)",
        "Confidence": 0.8,
        "Product_Desc": "Cloud SaaS platform",
        "Refund_Basis": "MPU",
        "Methodology": "MPU",
        "Tax_Category": "License",
        "Sales_Use_Tax": "Sales",
        "Explanation": "Multi-point use allocation for nationwide deployment.",
        "AI_Reasoning": _VALID_REASONING,
    }
    errors = validate_output_row(row)
    assert errors == []


def test_validate_normalizes_before_vocabulary_check():
    """Ensure 'equipment location' (lowercase) passes validation after normalization."""
    row = {
        "Final_Decision": "REFUND",
        "Citation": "RCW 82.08.02565",
        "Confidence": 0.8,
        "Product_Desc": "Network switches",
        "Refund_Basis": "MPU",
        "Methodology": "equipment location",
        "Explanation": "Equipment deployed outside WA.",
        "AI_Reasoning": _VALID_REASONING,
    }
    errors = validate_output_row(row)
    assert not any("controlled vocabulary" in err for err in errors)
