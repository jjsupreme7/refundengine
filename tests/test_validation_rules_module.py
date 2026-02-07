from __future__ import annotations

from refund_engine.validation_rules import normalize_final_decision, validate_output_row


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
